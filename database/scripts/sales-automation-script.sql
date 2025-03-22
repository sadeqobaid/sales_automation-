-- 1️⃣ SCHEMA CREATION
CREATE SCHEMA IF NOT EXISTS sales_automation;

-- Enable pgcrypto for secure password hashing and encryption
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 2️⃣ USERS & ROLES
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'admin') THEN
        CREATE ROLE admin WITH LOGIN PASSWORD 'securepassword';
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sales_manager') THEN
        CREATE ROLE sales_manager;
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'marketing_manager') THEN
        CREATE ROLE marketing_manager;
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'analyst') THEN
        CREATE ROLE analyst;
    END IF;
END $$;

-- Additional roles for more granular access control
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sales_rep') THEN
        CREATE ROLE sales_rep;
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'marketing_specialist') THEN
        CREATE ROLE marketing_specialist;
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'customer_success') THEN
        CREATE ROLE customer_success;
    END IF;
END $$;

GRANT CONNECT ON DATABASE sales_automation TO sales_manager, marketing_manager, analyst, sales_rep, marketing_specialist, customer_success;
GRANT USAGE ON SCHEMA sales_automation TO sales_manager, marketing_manager, analyst, sales_rep, marketing_specialist, customer_success;

-- 3️⃣ ENCRYPTION FUNCTIONS

-- Create encryption functions for sensitive data
CREATE OR REPLACE FUNCTION sales_automation.encrypt_data(data TEXT, key TEXT) RETURNS TEXT AS $$
BEGIN
    RETURN encode(pgp_sym_encrypt(data, key), 'base64');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION sales_automation.decrypt_data(encrypted_data TEXT, key TEXT) RETURNS TEXT AS $$
BEGIN
    RETURN pgp_sym_decrypt(decode(encrypted_data, 'base64'), key);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 4️⃣ FUNCTIONS

-- Function for enhanced audit logging
CREATE OR REPLACE FUNCTION sales_automation.enhanced_log_changes() RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO sales_automation.audit_logs (
        table_name, 
        operation, 
        changed_data, 
        previous_data,
        performed_by, 
        performed_at,
        ip_address,
        user_agent
    )
    VALUES (
        TG_TABLE_NAME, 
        TG_OP, 
        CASE WHEN TG_OP = 'DELETE' THEN row_to_json(OLD) ELSE row_to_json(NEW) END,
        CASE WHEN TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN row_to_json(OLD) ELSE NULL END,
        CASE 
            WHEN TG_OP = 'DELETE' THEN OLD.created_by 
            ELSE NEW.created_by 
        END,
        NOW(),
        current_setting('app.client_ip', TRUE),
        current_setting('app.user_agent', TRUE)
    );
    
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to set client context for audit logging
CREATE OR REPLACE FUNCTION sales_automation.set_client_info(
    p_client_ip VARCHAR(45),
    p_user_agent TEXT
) RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.client_ip', p_client_ip, FALSE);
    PERFORM set_config('app.user_agent', p_user_agent, FALSE);
END;
$$ LANGUAGE plpgsql;

-- Function to auto-update updated_at
CREATE OR REPLACE FUNCTION sales_automation.update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function for user ID retrieval (for row-level security)
CREATE OR REPLACE FUNCTION sales_automation.get_user_id() RETURNS INTEGER AS $$
BEGIN
    RETURN current_setting('app.user_id', TRUE)::INTEGER;
END;
$$ LANGUAGE plpgsql;

-- Function for password hashing
CREATE OR REPLACE FUNCTION sales_automation.hash_password() RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' OR NEW.password_hash <> OLD.password_hash THEN
        NEW.password_hash = crypt(NEW.password_hash, gen_salt('bf'));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 5️⃣ BACKUP AND MAINTENANCE FUNCTIONS

-- Create backup functions
CREATE OR REPLACE FUNCTION sales_automation.create_full_backup() RETURNS VOID AS $$
DECLARE
    backup_timestamp TEXT := to_char(now(), 'YYYY_MM_DD_HH24_MI_SS');
    table_name TEXT;
    backup_table_name TEXT;
    query TEXT;
BEGIN
    FOR table_name IN 
        SELECT tablename FROM pg_tables WHERE schemaname = 'sales_automation'
    LOOP
        backup_table_name := 'sales_automation_backup.' || table_name || '_' || backup_timestamp;
        query := 'CREATE TABLE ' || backup_table_name || ' AS SELECT * FROM sales_automation.' || table_name;
        EXECUTE query;
    END LOOP;
    
    INSERT INTO sales_automation.backup_history (backup_type, backup_timestamp, status)
    VALUES ('full', now(), 'completed');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create incremental backup function
CREATE OR REPLACE FUNCTION sales_automation.create_incremental_backup() RETURNS VOID AS $$
DECLARE
    backup_timestamp TEXT := to_char(now(), 'YYYY_MM_DD_HH24_MI_SS');
    last_backup_time TIMESTAMP;
BEGIN
    -- Get last backup time
    SELECT MAX(backup_timestamp) INTO last_backup_time FROM sales_automation.backup_history
    WHERE status = 'completed';
    
    IF last_backup_time IS NULL THEN
        PERFORM sales_automation.create_full_backup();
        RETURN;
    END IF;
    
    -- Create incremental backup tables for changed data
    EXECUTE 'CREATE TABLE sales_automation_backup.audit_logs_' || backup_timestamp || 
            ' AS SELECT * FROM sales_automation.audit_logs WHERE performed_at > ''' || last_backup_time || '''';
    
    INSERT INTO sales_automation.backup_history (backup_type, backup_timestamp, status)
    VALUES ('incremental', now(), 'completed');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create maintenance functions
CREATE OR REPLACE FUNCTION sales_automation.perform_vacuum() RETURNS VOID AS $$
DECLARE
    table_name TEXT;
BEGIN
    FOR table_name IN 
        SELECT tablename FROM pg_tables WHERE schemaname = 'sales_automation'
    LOOP
        EXECUTE 'VACUUM ANALYZE sales_automation.' || table_name;
    END LOOP;
    
    INSERT INTO sales_automation.maintenance_history (operation_type, details)
    VALUES ('vacuum', 'Performed VACUUM ANALYZE on all tables');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create index maintenance function
CREATE OR REPLACE FUNCTION sales_automation.maintain_indexes() RETURNS VOID AS $$
DECLARE
    index_record RECORD;
BEGIN
    FOR index_record IN 
        SELECT indexname, tablename FROM pg_indexes WHERE schemaname = 'sales_automation'
    LOOP
        EXECUTE 'REINDEX INDEX sales_automation.' || index_record.indexname;
    END LOOP;
    
    INSERT INTO sales_automation.maintenance_history (operation_type, details)
    VALUES ('reindex', 'Reindexed all indexes');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create statistics update function
CREATE OR REPLACE FUNCTION sales_automation.update_statistics() RETURNS VOID AS $$
DECLARE
    table_name TEXT;
BEGIN
    FOR table_name IN 
        SELECT tablename FROM pg_tables WHERE schemaname = 'sales_automation'
    LOOP
        EXECUTE 'ANALYZE sales_automation.' || table_name;
    END LOOP;
    
    INSERT INTO sales_automation.maintenance_history (operation_type, details)
    VALUES ('analyze', 'Updated statistics for all tables');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 6️⃣ TABLES

-- Create backup schema
CREATE SCHEMA IF NOT EXISTS sales_automation_backup;

-- Encryption key management table
CREATE TABLE IF NOT EXISTS sales_automation.encryption_keys (
    key_id SERIAL PRIMARY KEY,
    key_name VARCHAR(100) NOT NULL,
    key_version INT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    rotation_date TIMESTAMP,
    active BOOLEAN DEFAULT TRUE
);

-- Backup history table
CREATE TABLE IF NOT EXISTS sales_automation.backup_history (
    backup_id SERIAL PRIMARY KEY,
    backup_type VARCHAR(20) CHECK (backup_type IN ('full', 'incremental', 'point_in_time')),
    backup_timestamp TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) CHECK (status IN ('in_progress', 'completed', 'failed')),
    notes TEXT
);

-- Maintenance history table
CREATE TABLE IF NOT EXISTS sales_automation.maintenance_history (
    operation_id SERIAL PRIMARY KEY,
    operation_type VARCHAR(50) NOT NULL,
    operation_timestamp TIMESTAMP DEFAULT NOW(),
    details TEXT,
    status VARCHAR(20) DEFAULT 'completed'
);

-- Migration history table
CREATE TABLE IF NOT EXISTS sales_automation.migration_history (
    migration_id SERIAL PRIMARY KEY,
    migration_timestamp TIMESTAMP DEFAULT NOW(),
    source_table TEXT NOT NULL,
    target_table TEXT NOT NULL,
    records_migrated INTEGER DEFAULT 0,
    sql_executed TEXT,
    status VARCHAR(20) DEFAULT 'completed',
    error_message TEXT
);

-- Enhanced audit_logs table
CREATE TABLE IF NOT EXISTS sales_automation.audit_logs (
    log_id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    operation VARCHAR(10) NOT NULL,
    changed_data JSONB NOT NULL,
    previous_data JSONB,
    performed_by INT,
    performed_at TIMESTAMP DEFAULT NOW(),
    ip_address VARCHAR(45),
    user_agent TEXT
);

-- Users Table
CREATE TABLE IF NOT EXISTS sales_automation.users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z]{2,4}$') NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(50) CHECK (role IN ('admin', 'sales_manager', 'marketing_manager', 'analyst', 'sales_rep', 'marketing_specialist', 'customer_success')) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Add index for email in users table
CREATE INDEX IF NOT EXISTS idx_users_email ON sales_automation.users(email);

-- Login Attempts Table (Security Enhancement)
CREATE TABLE IF NOT EXISTS sales_automation.login_attempts (
    attempt_id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    attempt_time TIMESTAMP DEFAULT NOW(),
    ip_address VARCHAR(45),
    user_agent TEXT,
    success BOOLEAN NOT NULL
);

-- Add index for username and attempt_time
CREATE INDEX IF NOT EXISTS idx_login_attempts_username ON sales_automation.login_attempts(username);
CREATE INDEX IF NOT EXISTS idx_login_attempts_time ON sales_automation.login_attempts(attempt_time);

-- CRM Enhancements: Contact Management
CREATE TABLE IF NOT EXISTS sales_automation.contacts (
    contact_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z]{2,4}$') NOT NULL,
    phone VARCHAR(50),
    company VARCHAR(255),
    created_by INT REFERENCES sales_automation.users(user_id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Add index for email in contacts table
CREATE INDEX IF NOT EXISTS idx_contacts_email ON sales_automation.contacts(email);
CREATE INDEX IF NOT EXISTS idx_contacts_company ON sales_automation.contacts(company);

-- CRM Enhancements: Interaction Tracking
CREATE TABLE IF NOT EXISTS sales_automation.interactions (
    interaction_id SERIAL PRIMARY KEY,
    contact_id INT REFERENCES sales_automation.contacts(contact_id) ON DELETE CASCADE,
    interaction_type VARCHAR(50) CHECK (interaction_type IN ('email', 'call', 'meeting')) NOT NULL,
    interaction_details TEXT,
    interaction_date TIMESTAMP DEFAULT NOW(),
    created_by INT REFERENCES sales_automation.users(user_id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Add index for contact_id in interactions table
CREATE INDEX IF NOT EXISTS idx_interactions_contact_id ON sales_automation.interactions(contact_id);
CREATE INDEX IF NOT EXISTS idx_interactions_date ON sales_automation.interactions(interaction_date);

-- CRM Enhancements: Notes & Attachments
CREATE TABLE IF NOT EXISTS sales_automation.notes (
    note_id SERIAL PRIMARY KEY,
    contact_id INT REFERENCES sales_automation.contacts(contact_id) ON DELETE CASCADE,
    note_text TEXT NOT NULL,
    created_by INT REFERENCES sales_automation.users(user_id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notes_contact_id ON sales_automation.notes(contact_id);

CREATE TABLE IF NOT EXISTS sales_automation.attachments (
    attachment_id SERIAL PRIMARY KEY,
    contact_id INT REFERENCES sales_automation.contacts(contact_id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    created_by INT REFERENCES sales_automation.users(user_id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_attachments_contact_id ON sales_automation.attachments(contact_id);

-- Advanced AI/ML Features: Sentiment Analysis
CREATE TABLE IF NOT EXISTS sales_automation.sentiment_analysis (
    sentiment_id SERIAL PRIMARY KEY,
    interaction_id INT REFERENCES sales_automation.interactions(interaction_id) ON DELETE CASCADE,
    sentiment_score DECIMAL(5,2) CHECK (sentiment_score BETWEEN -1 AND 1), -- Range: -1 (negative) to 1 (positive)
    sentiment_label VARCHAR(50) CHECK (sentiment_label IN ('positive', 'neutral', 'negative')),
    analyzed_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sentiment_interaction_id ON sales_automation.sentiment_analysis(interaction_id);

-- Advanced AI/ML Features: Next Best Action (NBA)
CREATE TABLE IF NOT EXISTS sales_automation.next_best_actions (
    action_id SERIAL PRIMARY KEY,
    contact_id INT REFERENCES sales_automation.contacts(contact_id) ON DELETE CASCADE,
    recommended_action VARCHAR(255) NOT NULL,
    confidence_score DECIMAL(5,2) CHECK (confidence_score BETWEEN 0 AND 1), -- Range: 0 (low) to 1 (high)
    recommended_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_nba_contact_id ON sales_automation.next_best_actions(contact_id);
CREATE INDEX IF NOT EXISTS idx_nba_score ON sales_automation.next_best_actions(confidence_score);

-- Advanced AI/ML Features: Dynamic Lead Scoring
CREATE TABLE IF NOT EXISTS sales_automation.lead_scores (
    lead_score_id SERIAL PRIMARY KEY,
    contact_id INT REFERENCES sales_automation.contacts(contact_id) ON DELETE CASCADE,
    lead_score INT CHECK (lead_score BETWEEN 0 AND 100),
    score_updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_lead_scores_contact_id ON sales_automation.lead_scores(contact_id);
CREATE INDEX IF NOT EXISTS idx_lead_scores_score ON sales_automation.lead_scores(lead_score);

-- AI-Based Chatbot: Chatbot Interactions
CREATE TABLE IF NOT EXISTS sales_automation.chatbot_interactions (
    interaction_id SERIAL PRIMARY KEY,
    contact_id INT REFERENCES sales_automation.contacts(contact_id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    response TEXT NOT NULL,
    interaction_time TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chatbot_contact_id ON sales_automation.chatbot_interactions(contact_id);
CREATE INDEX IF NOT EXISTS idx_chatbot_time ON sales_automation.chatbot_interactions(interaction_time);

-- Voice AI: Call Transcription & Analysis
CREATE TABLE IF NOT EXISTS sales_automation.call_transcriptions (
    call_id SERIAL PRIMARY KEY,
    contact_id INT REFERENCES sales_automation.contacts(contact_id) ON DELETE CASCADE,
    call_recording_path TEXT NOT NULL,
    transcription TEXT,
    sentiment_score DECIMAL(5,2) CHECK (sentiment_score BETWEEN -1 AND 1),
    analyzed_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_call_contact_id ON sales_automation.call_transcriptions(contact_id);

-- Blockchain for Contract & Payment Automation: Smart Contracts
CREATE TABLE IF NOT EXISTS sales_automation.smart_contracts (
    contract_id SERIAL PRIMARY KEY,
    contact_id INT REFERENCES sales_automation.contacts(contact_id) ON DELETE CASCADE,
    contract_hash TEXT NOT NULL, -- Blockchain hash for the contract
    contract_details JSONB NOT NULL,
    status VARCHAR(50) CHECK (status IN ('pending', 'active', 'completed')) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_contracts_contact_id ON sales_automation.smart_contracts(contact_id);
CREATE INDEX IF NOT EXISTS idx_contracts_status ON sales_automation.smart_contracts(status);

-- Sales Gamification: Leaderboard & Rewards
CREATE TABLE IF NOT EXISTS sales_automation.leaderboard (
    leaderboard_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES sales_automation.users(user_id) ON DELETE CASCADE,
    points INT DEFAULT 0,
    rank INT,
    last_updated TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_leaderboard_user_id ON sales_automation.leaderboard(user_id);
CREATE INDEX IF NOT EXISTS idx_leaderboard_points ON sales_automation.leaderboard(points);

CREATE TABLE IF NOT EXISTS sales_automation.rewards (
    reward_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES sales_automation.users(user_id) ON DELETE CASCADE,
    reward_name VARCHAR(255) NOT NULL,
    reward_points INT CHECK (reward_points > 0),
    redeemed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rewards_user_id ON sales_automation.rewards(user_id);

-- Marketing Automation: Communication Templates
CREATE TABLE IF NOT EXISTS sales_automation.communication_templates (
    template_id SERIAL PRIMARY KEY,
    template_name VARCHAR(255) NOT NULL,
    template_type VARCHAR(50) CHECK (template_type IN ('email', 'sms', 'whatsapp')) NOT NULL,
    template_content TEXT NOT NULL,
    created_by INT REFERENCES sales_automation.users(user_id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_templates_type ON sales_automation.communication_templates(template_type);

-- Marketing Automation: Campaigns
CREATE TABLE IF NOT EXISTS sales_automation.marketing_campaigns (
    campaign_id SERIAL PRIMARY KEY,
    campaign_name VARCHAR(255) NOT NULL,
    channel VARCHAR(50) CHECK (channel IN ('email', 'social_media', 'ads', 'events')) NOT NULL,
    budget DECIMAL(12,2) CHECK (budget > 0),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(50) CHECK (status IN ('planned', 'active', 'completed')) DEFAULT 'planned',
    created_by INT REFERENCES sales_automation.users(user_id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_campaigns_status ON sales_automation.marketing_campaigns(status);
CREATE INDEX IF NOT EXISTS idx_campaigns_dates ON sales_automation.marketing_campaigns(start_date, end_date);

-- Task and Reminder Management: Tasks
CREATE TABLE IF NOT EXISTS sales_automation.tasks (
    task_id SERIAL PRIMARY KEY,
    task_name VARCHAR(255) NOT NULL,
    task_description TEXT,
    assigned_to INT REFERENCES sales_automation.users(user_id) ON DELETE SET NULL,
    due_date TIMESTAMP,
    status VARCHAR(50) CHECK (status IN ('pending', 'in_progress', 'completed')) DEFAULT 'pending',
    created_by INT REFERENCES sales_automation.users(user_id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to ON sales_automation.tasks(assigned_to);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON sales_automation.tasks(due_date);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON sales_automation.tasks(status);

-- Task and Reminder Management: Reminders
CREATE TABLE IF NOT EXISTS sales_automation.reminders (
    reminder_id SERIAL PRIMARY KEY,
    task_id INT REFERENCES sales_automation.tasks(task_id) ON DELETE CASCADE,
    reminder_time TIMESTAMP NOT NULL,
    status VARCHAR(50) CHECK (status IN ('pending', 'sent')) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reminders_task_id ON sales_automation.reminders(task_id);
CREATE INDEX IF NOT EXISTS idx_reminders_time ON sales_automation.reminders(reminder_time);
CREATE INDEX IF NOT EXISTS idx_reminders_status ON sales_automation.reminders(status);

-- Integration Configuration: CRM Integrations
CREATE TABLE IF NOT EXISTS sales_automation.crm_integrations (
    integration_id SERIAL PRIMARY KEY,
    crm_name VARCHAR(50) CHECK (crm_name IN ('HubSpot', 'Salesforce', 'Pipedrive', 'Zoho')) NOT NULL,
    api_key TEXT NOT NULL,
    encrypted_api_key TEXT,
    encryption_key_id INT,
    created_by INT REFERENCES sales_automation.users(user_id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Integration Configuration: ERP & Accounting Integrations
CREATE TABLE IF NOT EXISTS sales_automation.erp_integrations (
    integration_id SERIAL PRIMARY KEY,
    erp_name VARCHAR(50) CHECK (erp_name IN ('QuickBooks', 'Xero', 'SAP', 'Oracle')) NOT NULL,
    api_key TEXT NOT NULL,
    encrypted_api_key TEXT,
    encryption_key_id INT,
    created_by INT REFERENCES sales_automation.users(user_id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Integration Configuration: Email & Messaging Integrations
CREATE TABLE IF NOT EXISTS sales_automation.email_messaging_integrations (
    integration_id SERIAL PRIMARY KEY,
    service_name VARCHAR(50) CHECK (service_name IN ('Gmail', 'Outlook', 'Twilio', 'WhatsApp')) NOT NULL,
    api_key TEXT NOT NULL,
    encrypted_api_key TEXT,
    encryption_key_id INT,
    created_by INT REFERENCES sales_automation.users(user_id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Integration Configuration: Social Media & Ads Integrations
CREATE TABLE IF NOT EXISTS sales_automation.social_media_integrations (
    integration_id SERIAL PRIMARY KEY,
    platform_name VARCHAR(50) CHECK (platform_name IN ('Facebook', 'LinkedIn', 'Twitter', 'Google Ads')) NOT NULL,
    api_key TEXT NOT NULL,
    encrypted_api_key TEXT,
    encryption_key_id INT,
    created_by INT REFERENCES sales_automation.users(user_id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Lead Management
CREATE TABLE IF NOT EXISTS sales_automation.leads (
    lead_id SERIAL PRIMARY KEY,
    contact_id INT REFERENCES sales_automation.contacts(contact_id) ON DELETE CASCADE,
    lead_score INT,
    created_by INT REFERENCES sales_automation.users(user_id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_leads_contact_id ON sales_automation.leads(contact_id);

-- Sales Pipeline
CREATE TABLE IF NOT EXISTS sales_automation.sales_pipeline (
    deal_id SERIAL PRIMARY KEY,
    lead_id INT REFERENCES sales_automation.leads(lead_id) ON DELETE CASCADE,
    expected_revenue DECIMAL(12,2),
    close_date DATE,
    status VARCHAR(50) CHECK (status IN ('qualification', 'proposal', 'negotiation', 'won', 'lost')) NOT NULL,
    created_by INT REFERENCES sales_automation.users(user_id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sales_pipeline_lead_id ON sales_automation.sales_pipeline(lead_id);
CREATE INDEX IF NOT EXISTS idx_sales_pipeline_status ON sales_automation.sales_pipeline(status);
CREATE INDEX IF NOT EXISTS idx_sales_pipeline_close_date ON sales_automation.sales_pipeline(close_date);

-- Sales Forecast (Added missing table)
CREATE TABLE IF NOT EXISTS sales_automation.sales_forecast (
    forecast_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES sales_automation.users(user_id) ON DELETE CASCADE,
    forecast_period VARCHAR(20) CHECK (forecast_period IN ('monthly', 'quarterly', 'yearly')),
    period_start DATE,
    period_end DATE,
    target_amount DECIMAL(12,2) CHECK (target_amount > 0),
    actual_amount DECIMAL(12,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sales_forecast_user_id ON sales_automation.sales_forecast(user_id);
CREATE INDEX IF NOT EXISTS idx_sales_forecast_period ON sales_automation.sales_forecast(forecast_period, period_start, period_end);

-- 7️⃣ TRIGGERS

-- Triggers for audit logging
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'audit_contacts_changes') THEN
        CREATE TRIGGER audit_contacts_changes
        AFTER INSERT OR UPDATE OR DELETE ON sales_automation.contacts
        FOR EACH ROW EXECUTE FUNCTION sales_automation.enhanced_log_changes();
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'audit_interactions_changes') THEN
        CREATE TRIGGER audit_interactions_changes
        AFTER INSERT OR UPDATE OR DELETE ON sales_automation.interactions
        FOR EACH ROW EXECUTE FUNCTION sales_automation.enhanced_log_changes();
    END IF;
END $$;

-- Add triggers for other important tables
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'audit_leads_changes') THEN
        CREATE TRIGGER audit_leads_changes
        AFTER INSERT OR UPDATE OR DELETE ON sales_automation.leads
        FOR EACH ROW EXECUTE FUNCTION sales_automation.enhanced_log_changes();
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'audit_sales_pipeline_changes') THEN
        CREATE TRIGGER audit_sales_pipeline_changes
        AFTER INSERT OR UPDATE OR DELETE ON sales_automation.sales_pipeline
        FOR EACH ROW EXECUTE FUNCTION sales_automation.enhanced_log_changes();
    END IF;
END $$;

-- Password hashing trigger
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trigger_hash_password') THEN
        CREATE TRIGGER trigger_hash_password
        BEFORE INSERT OR UPDATE ON sales_automation.users
        FOR EACH ROW EXECUTE FUNCTION sales_automation.hash_password();
    END IF;
END $$;

-- Updated timestamp triggers
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trigger_update_timestamp_users') THEN
        CREATE TRIGGER trigger_update_timestamp_users
        BEFORE UPDATE ON sales_automation.users
        FOR EACH ROW EXECUTE FUNCTION sales_automation.update_timestamp();
    END IF;
END $$;

-- Add update timestamp triggers for all tables with updated_at column - FIXED VERSION
DO $$ 
DECLARE
    tbl_name TEXT;  -- Renamed variable to avoid ambiguity
    trigger_name TEXT;
BEGIN
    FOR tbl_name IN 
        SELECT t.tablename 
        FROM pg_tables t  -- Aliased as 't'
        WHERE t.schemaname = 'sales_automation' 
        AND EXISTS (
            SELECT 1 
            FROM information_schema.columns c  -- Aliased as 'c'
            WHERE c.table_schema = 'sales_automation' 
            AND c.table_name = t.tablename  -- Use the alias 't' to refer to the outer query
            AND c.column_name = 'updated_at'
        )
    LOOP
        trigger_name := 'trigger_update_timestamp_' || tbl_name;
        
        -- Check if trigger already exists
        IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = trigger_name) THEN
            EXECUTE 'CREATE TRIGGER ' || trigger_name || 
                    ' BEFORE UPDATE ON sales_automation.' || tbl_name || 
                    ' FOR EACH ROW EXECUTE FUNCTION sales_automation.update_timestamp()';
        END IF;
    END LOOP;
END $$;

CREATE TABLE IF NOT EXISTS sales_automation.sales_forecast (
    forecast_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES sales_automation.users(user_id) ON DELETE CASCADE,
    forecast_period VARCHAR(20) CHECK (forecast_period IN ('monthly', 'quarterly', 'yearly')),
    period_start DATE,
    period_end DATE,
    target_amount DECIMAL(12,2) CHECK (target_amount > 0),
    actual_amount DECIMAL(12,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for the new sales_forecast table
CREATE INDEX IF NOT EXISTS idx_sales_forecast_user_id ON sales_automation.sales_forecast(user_id);
CREATE INDEX IF NOT EXISTS idx_sales_forecast_period ON sales_automation.sales_forecast(forecast_period, period_start, period_end);

-- The grants should now work properly
GRANT SELECT ON sales_automation.sales_forecast TO analyst;


-- 8️⃣ PERMISSIONS

-- Revoke sensitive permissions
REVOKE UPDATE, DELETE ON sales_automation.users FROM sales_manager;

-- Grant appropriate permissions to roles
GRANT SELECT, INSERT, UPDATE ON sales_automation.contacts TO sales_manager;
GRANT SELECT ON sales_automation.sales_forecast TO analyst;

-- Sales rep permissions
GRANT SELECT, INSERT, UPDATE ON sales_automation.contacts TO sales_rep;
GRANT SELECT, INSERT, UPDATE ON sales_automation.interactions TO sales_rep;
GRANT SELECT, INSERT, UPDATE ON sales_automation.notes TO sales_rep;
GRANT SELECT, INSERT, UPDATE ON sales_automation.attachments TO sales_rep;
GRANT SELECT, INSERT, UPDATE ON sales_automation.leads TO sales_rep;
GRANT SELECT, INSERT, UPDATE ON sales_automation.sales_pipeline TO sales_rep;
GRANT SELECT, INSERT, UPDATE ON sales_automation.tasks TO sales_rep;
GRANT SELECT ON sales_automation.lead_scores TO sales_rep;
GRANT SELECT ON sales_automation.next_best_actions TO sales_rep;
-- Marketing specialist permissions
GRANT SELECT, INSERT, UPDATE ON sales_automation.marketing_campaigns TO marketing_specialist;
GRANT SELECT, INSERT, UPDATE ON sales_automation.communication_templates TO marketing_specialist;
GRANT SELECT ON sales_automation.contacts TO marketing_specialist;
GRANT SELECT ON sales_automation.lead_scores TO marketing_specialist;

-- Customer success permissions
GRANT SELECT, INSERT, UPDATE ON sales_automation.contacts TO customer_success;
GRANT SELECT, INSERT, UPDATE ON sales_automation.interactions TO customer_success;
GRANT SELECT, INSERT, UPDATE ON sales_automation.notes TO customer_success;
GRANT SELECT, INSERT, UPDATE ON sales_automation.tasks TO customer_success;
GRANT SELECT ON sales_automation.smart_contracts TO customer_success;

-- Grant limited access to encryption functions
REVOKE ALL ON FUNCTION sales_automation.encrypt_data(TEXT, TEXT) FROM PUBLIC;
REVOKE ALL ON FUNCTION sales_automation.decrypt_data(TEXT, TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION sales_automation.encrypt_data(TEXT, TEXT) TO admin;
GRANT EXECUTE ON FUNCTION sales_automation.decrypt_data(TEXT, TEXT) TO admin;

-- Grant execute permission for client info setting
GRANT EXECUTE ON FUNCTION sales_automation.set_client_info(VARCHAR(45), TEXT) TO sales_manager, marketing_manager, analyst, sales_rep, marketing_specialist, customer_success;

-- 9️⃣ ROW-LEVEL SECURITY

-- Enable row-level security
ALTER TABLE sales_automation.contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE sales_automation.leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE sales_automation.sales_pipeline ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY contacts_user_policy ON sales_automation.contacts
    USING (created_by = sales_automation.get_user_id() OR 
           EXISTS (SELECT 1 FROM sales_automation.users WHERE user_id = sales_automation.get_user_id() AND role IN ('admin', 'sales_manager')));

CREATE POLICY leads_user_policy ON sales_automation.leads
    USING (created_by = sales_automation.get_user_id() OR 
           EXISTS (SELECT 1 FROM sales_automation.users WHERE user_id = sales_automation.get_user_id() AND role IN ('admin', 'sales_manager')));

CREATE POLICY sales_pipeline_user_policy ON sales_automation.sales_pipeline
    USING (created_by = sales_automation.get_user_id() OR 
           EXISTS (SELECT 1 FROM sales_automation.users WHERE user_id = sales_automation.get_user_id() AND role IN ('admin', 'sales_manager')));

-- 🔟 PERFORMANCE OPTIMIZATION

-- Create materialized views for common reports
CREATE MATERIALIZED VIEW sales_automation.mv_sales_performance AS
SELECT 
    u.user_id,
    u.username,
    COUNT(sp.deal_id) AS total_deals,
    COUNT(CASE WHEN sp.status = 'won' THEN 1 END) AS won_deals,
    COUNT(CASE WHEN sp.status = 'lost' THEN 1 END) AS lost_deals,
    SUM(CASE WHEN sp.status = 'won' THEN sp.expected_revenue ELSE 0 END) AS total_revenue,
    AVG(CASE WHEN sp.status = 'won' THEN sp.expected_revenue ELSE NULL END) AS avg_deal_size
FROM 
    sales_automation.users u
LEFT JOIN 
    sales_automation.sales_pipeline sp ON u.user_id = sp.created_by
WHERE 
    u.role IN ('sales_manager', 'admin', 'sales_rep')
GROUP BY 
    u.user_id, u.username;

-- Create index for materialized view
CREATE INDEX idx_mv_sales_performance_user_id ON sales_automation.mv_sales_performance(user_id);

-- Create refresh function for materialized views
CREATE OR REPLACE FUNCTION sales_automation.refresh_materialized_views() RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY sales_automation.mv_sales_performance;
    
    INSERT INTO sales_automation.maintenance_history (operation_type, details)
    VALUES ('refresh_mv', 'Refreshed materialized views');
END;
$$ LANGUAGE plpgsql;

-- Create partitioning for audit_logs table
CREATE TABLE IF NOT EXISTS sales_automation.audit_logs_partitioned (
    log_id BIGSERIAL,
    table_name VARCHAR(100) NOT NULL,
    operation VARCHAR(10) NOT NULL,
    changed_data JSONB NOT NULL,
    previous_data JSONB,
    performed_by INT,
    performed_at TIMESTAMP NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT
) PARTITION BY RANGE (performed_at);

-- Create initial partitions
CREATE TABLE sales_automation.audit_logs_y2025m01 PARTITION OF sales_automation.audit_logs_partitioned
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
    
CREATE TABLE sales_automation.audit_logs_y2025m02 PARTITION OF sales_automation.audit_logs_partitioned
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
    
CREATE TABLE sales_automation.audit_logs_y2025m03 PARTITION OF sales_automation.audit_logs_partitioned
    FOR VALUES FROM ('2025-03-01') TO ('2025-04-01');

-- Create function to automatically create new partitions
CREATE OR REPLACE FUNCTION sales_automation.create_audit_log_partition() RETURNS VOID AS $$
DECLARE
    next_month DATE;
    partition_name TEXT;
    start_date TEXT;
    end_date TEXT;
BEGIN
    -- Calculate next month
    SELECT 
        date_trunc('month', now()) + interval '2 month' INTO next_month;
    
    -- Create partition name
    partition_name := 'audit_logs_y' || 
                     to_char(next_month, 'YYYY') || 
                     'm' || 
                     to_char(next_month, 'MM');
    
    -- Check if partition already exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_tables 
        WHERE schemaname = 'sales_automation' AND tablename = partition_name
    ) THEN
        -- Create new partition
        EXECUTE 'CREATE TABLE sales_automation.' || partition_name || 
                ' PARTITION OF sales_automation.audit_logs_partitioned' ||
                ' FOR VALUES FROM (''' || 
                date_trunc('month', next_month)::TEXT || ''') TO (''' || 
                (date_trunc('month', next_month) + interval '1 month')::TEXT || ''')';
                
        -- Log partition creation
        INSERT INTO sales_automation.maintenance_history (operation_type, details)
        VALUES ('create_partition', 'Created new partition: ' || partition_name);
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Add comments for scheduling
COMMENT ON FUNCTION sales_automation.create_full_backup() IS 'Run daily at 1:00 AM';
COMMENT ON FUNCTION sales_automation.create_incremental_backup() IS 'Run hourly';
COMMENT ON FUNCTION sales_automation.perform_vacuum() IS 'Run weekly on Sunday at 2:00 AM';
COMMENT ON FUNCTION sales_automation.maintain_indexes() IS 'Run monthly on the 1st at 3:00 AM';
COMMENT ON FUNCTION sales_automation.update_statistics() IS 'Run daily at 4:00 AM';
COMMENT ON FUNCTION sales_automation.refresh_materialized_views() IS 'Run daily at 5:00 AM';
COMMENT ON FUNCTION sales_automation.create_audit_log_partition() IS 'Run monthly on the 15th at 1:00 AM';
