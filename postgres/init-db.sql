-- Database initialization script for horizontal scaling

-- Create connection pooling user
CREATE USER pool_user WITH PASSWORD 'pool_password';
GRANT CONNECT ON DATABASE mindcoach TO pool_user;

-- Create read-only user for reporting
CREATE USER readonly_user WITH PASSWORD 'readonly_password';
GRANT CONNECT ON DATABASE mindcoach TO readonly_user;
GRANT USAGE ON SCHEMA public TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO readonly_user;

-- Create indexes for better performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_user_id ON users(user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_created_at ON users(created_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subscriptions_subject ON subscriptions(subject);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_survey_results_user_id ON survey_results(user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_survey_results_subject ON survey_results(subject);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_survey_results_completed_at ON survey_results(completed_at);

-- Create composite indexes for common queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subscriptions_user_subject ON subscriptions(user_id, subject);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_survey_results_user_subject ON survey_results(user_id, subject);

-- Create partial indexes for active subscriptions
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subscriptions_active ON subscriptions(user_id, subject) WHERE status = 'active';

-- Enable pg_stat_statements for query monitoring
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Create monitoring views
CREATE OR REPLACE VIEW connection_stats AS
SELECT 
    datname,
    usename,
    application_name,
    client_addr,
    state,
    query_start,
    state_change,
    query
FROM pg_stat_activity 
WHERE state != 'idle';

CREATE OR REPLACE VIEW table_stats AS
SELECT 
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    n_live_tup as live_tuples,
    n_dead_tup as dead_tuples,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables;

CREATE OR REPLACE VIEW slow_queries AS
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows,
    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 20;

-- Create function to get database size
CREATE OR REPLACE FUNCTION get_db_size() 
RETURNS TABLE(
    database_name text,
    size_mb numeric
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        datname::text,
        round(pg_database_size(datname) / 1024.0 / 1024.0, 2)
    FROM pg_database 
    WHERE datname = current_database();
END;
$$ LANGUAGE plpgsql;

-- Create function to get connection count
CREATE OR REPLACE FUNCTION get_connection_count()
RETURNS TABLE(
    total_connections integer,
    active_connections integer,
    idle_connections integer
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        count(*)::integer as total,
        count(*) FILTER (WHERE state = 'active')::integer as active,
        count(*) FILTER (WHERE state = 'idle')::integer as idle
    FROM pg_stat_activity 
    WHERE datname = current_database();
END;
$$ LANGUAGE plpgsql;

-- Create health check function
CREATE OR REPLACE FUNCTION health_check()
RETURNS json AS $$
DECLARE
    result json;
BEGIN
    SELECT json_build_object(
        'status', 'healthy',
        'timestamp', now(),
        'database', current_database(),
        'version', version(),
        'connections', (SELECT row_to_json(get_connection_count())),
        'size', (SELECT row_to_json(get_db_size()))
    ) INTO result;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT EXECUTE ON FUNCTION health_check() TO pool_user;
GRANT EXECUTE ON FUNCTION get_connection_count() TO pool_user;
GRANT EXECUTE ON FUNCTION get_db_size() TO pool_user;

-- Create session management table for horizontal scaling
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);

-- Create trigger to update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_sessions_updated_at 
    BEFORE UPDATE ON user_sessions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create cleanup function for expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM user_sessions WHERE expires_at < CURRENT_TIMESTAMP;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create performance monitoring table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC NOT NULL,
    tags JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_performance_metrics_name_timestamp ON performance_metrics(metric_name, timestamp);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp ON performance_metrics(timestamp);

-- Insert initial performance baseline
INSERT INTO performance_metrics (metric_name, metric_value, tags) VALUES
('database_connections_max', 200, '{"type": "config"}'),
('shared_buffers_mb', 256, '{"type": "config"}'),
('effective_cache_size_mb', 1024, '{"type": "config"}');

COMMIT;