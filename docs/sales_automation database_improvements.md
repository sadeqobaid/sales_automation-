# Database Script Improvements for Sales Automation System

## 1. Introduction

After reviewing the database script (`init.sql`) for the Sales Automation System, I've identified several areas for improvement based on database security auditing best practices, backup procedures, and maintenance operations. This document outlines recommended enhancements to strengthen security, ensure data integrity, and optimize database operations.

## 2. Security Enhancements

### 2.1 Data Encryption for Sensitive Information

The current script uses password hashing but lacks encryption for other sensitive data. Implementing column-level encryption for sensitive information will enhance security.

```sql
-- Add pgcrypto extension if not already added
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create encryption functions
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

-- Modify tables to use encrypted columns for sensitive data
ALTER TABLE sales_automation.crm_integrations 
    ADD COLUMN encrypted_api_key TEXT,
    ADD COLUMN encryption_key_id INT;

ALTER TABLE sales_automation.erp_integrations 
    ADD COLUMN encrypted_api_key TEXT,
    ADD COLUMN encryption_key_id INT;

ALTER TABLE sales_automation.email_messaging_integrations 
    ADD COLUMN encrypted_api_key TEXT,
    ADD COLUMN encryption_key_id INT;

ALTER TABLE sales_automation.social_media_integrations 
    ADD COLUMN encrypted_api_key TEXT,
    ADD COLUMN encryption_key_id INT;

-- Create encryption key management table
CREATE TABLE IF NOT EXISTS sales_automation.encryption_keys (
    key_id SERIAL PRIMARY KEY,
    key_name VARCHAR(100) NOT NULL,
    key_version INT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    rotation_date TIMESTAMP,
    active BOOLEAN DEFAULT TRUE
);

-- Grant limited access to encryption functions
REVOKE ALL ON FUNCTION sales_automation.encrypt_data(TEXT, TEXT) FROM PUBLIC;
REVOKE ALL ON FUNCTION sales_automation.decrypt_data(TEXT, TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION sales_automation.encrypt_data(TEXT, TEXT) TO admin;
GRANT EXECUTE ON FUNCTION sales_automation.decrypt_data(TEXT, TEXT) TO admin;
```

### 2.2 Enhanced Audit Logging

The current audit logging captures basic information but can be enhanced to provide more comprehensive security auditing.

```sql
-- Enhance audit_logs table
ALTER TABLE sales_automation.audit_logs
    ADD COLUMN ip_address VARCHAR(45),
    ADD COLUMN user_agent TEXT,
    ADD COLUMN previous_data JSONB;

-- Improve audit logging function
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

-- Create function to set client context
CREATE OR REPLACE FUNCTION sales_automation.set_client_info(
    p_client_ip VARCHAR(45),
    p_user_agent TEXT
) RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.client_ip', p_client_ip, FALSE);
    PERFORM set_config('app.user_agent', p_user_agent, FALSE);
END;
$$ LANGUAGE plpgsql;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION sales_automation.set_client_info(VARCHAR(45), TEXT) TO sales_manager, marketing_manager, analyst;
```

### 2.3 Improved Role-Based Access Control

The current script has basic role-based access control but can be enhanced with more granular permissions.

```sql
-- Create additional roles for more granular access control
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

-- Grant appropriate permissions to roles
GRANT CONNECT ON DATABASE sales_automation TO sales_rep, marketing_specialist, customer_success;
GRANT USAGE ON SCHEMA sales_automation TO sales_rep, marketing_specialist, customer_success;

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

-- Row-level security policies
CREATE OR REPLACE FUNCTION sales_automation.get_user_id() RETURNS INTEGER AS $$
BEGIN
    RETURN current_setting('app.user_id', TRUE)::INTEGER;
END;
$$ LANGUAGE plpgsql;

-- Enable row-level security
ALTER TABLE sales_automation.contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE sales_automation.leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE sales_automation.sales_pipeline ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY contacts_user_policy ON sales_automation.contacts
    USING (created_by = sales_automation.get_user_id() OR 
           EXISTS (SELECT 1 FROM sales_automation.users WHERE user_id = sales_automation.get_user_id() AND role = 'admin'));

CREATE POLICY leads_user_policy ON sales_automation.leads
    USING (created_by = sales_automation.get_user_id() OR 
           EXISTS (SELECT 1 FROM sales_automation.users WHERE user_id = sales_automation.get_user_id() AND role = 'admin'));

CREATE POLICY sales_pipeline_user_policy ON sales_automation.sales_pipeline
    USING (created_by = sales_automation.get_user_id() OR 
           EXISTS (SELECT 1 FROM sales_automation.users WHERE user_id = sales_automation.get_user_id() AND role = 'admin'));
```

## 3. Backup and Recovery Procedures

The current script lacks database backup and recovery procedures. Adding these will ensure data durability and business continuity.

```sql
-- Create backup schema
CREATE SCHEMA IF NOT EXISTS sales_automation_backup;

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

-- Create backup history table
CREATE TABLE IF NOT EXISTS sales_automation.backup_history (
    backup_id SERIAL PRIMARY KEY,
    backup_type VARCHAR(20) CHECK (backup_type IN ('full', 'incremental', 'point_in_time')),
    backup_timestamp TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) CHECK (status IN ('in_progress', 'completed', 'failed')),
    notes TEXT
);

-- Create backup verification function
CREATE OR REPLACE FUNCTION sales_automation.verify_backup(p_backup_id INTEGER) RETURNS BOOLEAN AS $$
DECLARE
    backup_record RECORD;
    table_count INTEGER := 0;
    expected_count INTEGER := 0;
BEGIN
    SELECT * INTO backup_record FROM sales_automation.backup_history WHERE backup_id = p_backup_id;
    
    IF backup_record IS NULL THEN
        RETURN FALSE;
    END IF;
    
    IF backup_record.backup_type = 'full' THEN
        -- Count tables in backup schema that match the timestamp
        SELECT COUNT(*) INTO table_count 
        FROM pg_tables 
        WHERE schemaname = 'sales_automation_backup' 
        AND tablename LIKE '%\_' || to_char(backup_record.backup_timestamp, 'YYYY_MM_DD_HH24_MI_SS');
        
        -- Count tables in main schema
        SELECT COUNT(*) INTO expected_count FROM pg_tables WHERE schemaname = 'sales_automation';
        
        RETURN table_count = expected_count;
    ELSE
        -- For incremental backups, just check if the audit log backup exists
        RETURN EXISTS (
            SELECT 1 FROM pg_tables 
            WHERE schemaname = 'sales_automation_backup' 
            AND tablename = 'audit_logs_' || to_char(backup_record.backup_timestamp, 'YYYY_MM_DD_HH24_MI_SS')
        );
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Create scheduled backup jobs (to be executed by external scheduler)
COMMENT ON FUNCTION sales_automation.create_full_backup() IS 'Run daily at 1:00 AM';
COMMENT ON FUNCTION sales_automation.create_incremental_backup() IS 'Run hourly';
```

## 4. Database Maintenance Procedures

The current script lacks database maintenance procedures. Adding these will ensure optimal performance and data integrity.

```sql
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

-- Create maintenance history table
CREATE TABLE IF NOT EXISTS sales_automation.maintenance_history (
    operation_id SERIAL PRIMARY KEY,
    operation_type VARCHAR(50) NOT NULL,
    operation_timestamp TIMESTAMP DEFAULT NOW(),
    details TEXT,
    status VARCHAR(20) DEFAULT 'completed'
);

-- Create database health check function
CREATE OR REPLACE FUNCTION sales_automation.check_database_health() RETURNS TABLE (
    check_name TEXT,
    status TEXT,
    details TEXT
) AS $$
BEGIN
    -- Check for bloated tables
    RETURN QUERY
    SELECT 
        'table_bloat' AS check_name,
        CASE WHEN n_dead_tup > n_live_tup * 0.2 THEN 'warning' ELSE 'ok' END AS status,
        relname || ' has ' || n_dead_tup || ' dead tuples out of ' || n_live_tup || ' total' AS details
    FROM pg_stat_user_tables
    WHERE schemaname = 'sales_automation' AND n_live_tup > 0 AND n_dead_tup > n_live_tup * 0.2;
    
    -- Check for unused indexes
    RETURN QUERY
    SELECT 
        'unused_indexes' AS check_name,
        'warning' AS status,
        indexrelname || ' on ' || relname || ' has not been used' AS details
    FROM pg_stat_user_indexes
    WHERE schemaname = 'sales_automation' AND idx_scan = 0 AND indexrelname NOT LIKE '%_pkey';
    
    -- Check for missing indexes (high seq scans)
    RETURN QUERY
    SELECT 
        'missing_indexes' AS check_name,
        'warning' AS status,
        relname || ' has high sequential scan count (' || seq_scan || ')' AS details
    FROM pg_stat_user_tables
    WHERE schemaname = 'sales_automation' AND seq_scan > 1000 AND seq_scan > idx_scan * 10;
    
    -- Check for long-running queries
    RETURN QUERY
    SELECT 
        'long_running_queries' AS check_name,
        'warning' AS status,
        'Query running for ' || extract(epoch FROM now() - query_start)::TEXT || ' seconds: ' || query AS details
    FROM pg_stat_activity
    WHERE state = 'active' AND query_start < now() - interval '5 minutes' AND query NOT ILIKE '%pg_stat_activity%';
END;
$$ LANGUAGE plpgsql;

-- Create scheduled maintenance jobs (to be executed by external scheduler)
COMMENT ON FUNCTION sales_automation.perform_vacuum() IS 'Run weekly on Sunday at 2:00 AM';
COMMENT ON FUNCTION sales_automation.maintain_indexes() IS 'Run monthly on the 1st at 3:00 AM';
COMMENT ON FUNCTION sales_automation.update_statistics() IS 'Run daily at 4:00 AM';
COMMENT ON FUNCTION sales_automation.check_database_health() IS 'Run daily at 6:00 AM';
```

## 5. Data Migration and Validation

Adding data migration and validation procedures will ensure data integrity during updates and migrations.

```sql
-- Create data validation functions
CREATE OR REPLACE FUNCTION sales_automation.validate_email_addresses() RETURNS TABLE (
    table_name TEXT,
    column_name TEXT,
    record_id INTEGER,
    invalid_email TEXT
) AS $$
BEGIN
    -- Check contacts table
    RETURN QUERY
    SELECT 
        'contacts'::TEXT AS table_name,
        'email'::TEXT AS column_name,
        contact_id AS record_id,
        email AS invalid_email
    FROM sales_automation.contacts
    WHERE email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z]{2,4}$';
    
    -- Check users table
    RETURN QUERY
    SELECT 
        'users'::TEXT AS table_name,
        'email'::TEXT AS column_name,
        user_id AS record_id,
        email AS invalid_email
    FROM sales_automation.users
    WHERE email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z]{2,4}$';
END;
$$ LANGUAGE plpgsql;

-- Create data migration function with transaction support
CREATE OR REPLACE FUNCTION sales_automation.migrate_data(
    p_source_table TEXT,
    p_target_table TEXT,
    p_column_mapping JSONB,
    p_where_clause TEXT DEFAULT NULL
) RETURNS INTEGER AS $$
DECLARE
    v_columns_source TEXT := '';
    v_columns_target TEXT := '';
    v_column_pair RECORD;
    v_sql TEXT;
    v_count INTEGER;
BEGIN
    -- Build column lists
    FOR v_column_pair IN SELECT * FROM jsonb_each(p_column_mapping)
    LOOP
        IF v_columns_source <> '' THEN
            v_columns_source := v_columns_source || ', ';
            v_columns_target := v_columns_target || ', ';
        END IF;
        v_columns_source := v_columns_source || v_column_pair.key;
        v_columns_target := v_columns_target || v_column_pair.value;
    END LOOP;
    
    -- Build SQL
    v_sql := 'INSERT INTO ' || p_target_table || ' (' || v_columns_target || ') ' ||
             'SELECT ' || v_columns_source || ' FROM ' || p_source_table;
    
    -- Add WHERE clause if provided
    IF p_where_clause IS NOT NULL THEN
        v_sql := v_sql || ' WHERE ' || p_where_clause;
    END IF;
    
    -- Execute within transaction
    BEGIN
        EXECUTE v_sql;
        GET DIAGNOSTICS v_count = ROW_COUNT;
        
        -- Log migration
        INSERT INTO sales_automation.migration_history (
            source_table, target_table, records_migrated, sql_executed
        ) VALUES (
            p_source_table, p_target_table, v_count, v_sql
        );
        
        RETURN v_count;
    EXCEPTION WHEN OTHERS THEN
        -- Log error
        INSERT INTO sales_automation.migration_history (
            source_table, target_table, records_migrated, sql_executed, status, error_message
        ) VALUES (
            p_source_table, p_target_table, 0, v_sql, 'failed', SQLERRM
        );
        
        RAISE;
    END;
END;
$$ LANGUAGE plpgsql;

-- Create migration history table
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
```

## 6. Performance Optimization

Adding performance optimization features will ensure the database operates efficiently as it scales.

```sql
-- Create partitioning for large tables
-- Example for audit_logs table
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

-- Create partitions
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
    u.role IN ('sales_manager', 'admin')
GROUP BY 
    u.user_id, u.username;

-- Create refresh function for materialized views
CREATE OR REPLACE FUNCTION sales_automation.refresh_materialized_views() RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY sales_automation.mv_sales_performance;
    
    INSERT INTO sales_automation.maintenance_history (operation_type, details)
    VALUES ('refresh_mv', 'Refreshed materialized views');
END;
$$ LANGUAGE plpgsql;

-- Create index for materialized view
CREATE INDEX idx_mv_sales_performance_user_id ON sales_automation.mv_sales_performance(user_id);

-- Comment for scheduling
COMMENT ON FUNCTION sales_automation.refresh_materialized_views() IS 'Run daily at 5:00 AM';
COMMENT ON FUNCTION sales_automation.create_audit_log_partition() IS 'Run monthly on the 15th at 1:00 AM';
```

## 7. Conclusion and Implementation Recommendations

The proposed improvements enhance the Sales Automation System database in several key areas:

1. **Security Enhancements**:
   - Data encryption for sensitive information
   - Enhanced audit logging with more context
   - Improved role-based access control with row-level security

2. **Backup and Recovery**:
   - Automated backup procedures
   - Backup verification
   - Incremental and full backup options

3. **Maintenance Procedures**:
   - Regular VACUUM and ANALYZE operations
   - Index maintenance
   - Database health checks

4. **Data Migration and Validation**:
   - Transaction-supported migration functions
   - Data validation procedures
   - Migration history tracking

5. **Performance Optimization**:
   - Table partitioning for large tables
   - Materialized views for reporting
   - Automated partition management

### Implementation Approach

To implement these improvements safely:

1. **Testing**: Test all changes in a development environment first
2. **Phased Implementation**: Implement changes in phases, starting with non-disruptive enhancements
3. **Backup**: Create a full backup before implementing any changes
4. **Documentation**: Update system documentation to reflect the changes
5. **Monitoring**: Monitor system performance after implementing changes

These improvements will significantly enhance the security, reliability, and performance of the Sales Automation System database while maintaining compatibility with the existing application.
