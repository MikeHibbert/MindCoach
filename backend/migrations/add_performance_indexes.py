"""
Add database indexes for performance optimization
"""
from app import db

def upgrade():
    """Add performance indexes"""
    
    # Add indexes for users table
    db.engine.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
    """)
    
    # Add indexes for subscriptions table
    db.engine.execute("""
        CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
        CREATE INDEX IF NOT EXISTS idx_subscriptions_subject ON subscriptions(subject);
        CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
        CREATE INDEX IF NOT EXISTS idx_subscriptions_user_subject ON subscriptions(user_id, subject);
        CREATE INDEX IF NOT EXISTS idx_subscriptions_expires_at ON subscriptions(expires_at);
    """)
    
    # Add indexes for survey_results table
    db.engine.execute("""
        CREATE INDEX IF NOT EXISTS idx_survey_results_user_id ON survey_results(user_id);
        CREATE INDEX IF NOT EXISTS idx_survey_results_subject ON survey_results(subject);
        CREATE INDEX IF NOT EXISTS idx_survey_results_user_subject ON survey_results(user_id, subject);
        CREATE INDEX IF NOT EXISTS idx_survey_results_completed_at ON survey_results(completed_at);
    """)

def downgrade():
    """Remove performance indexes"""
    
    # Remove indexes for users table
    db.engine.execute("""
        DROP INDEX IF EXISTS idx_users_user_id;
        DROP INDEX IF EXISTS idx_users_email;
        DROP INDEX IF EXISTS idx_users_created_at;
    """)
    
    # Remove indexes for subscriptions table
    db.engine.execute("""
        DROP INDEX IF EXISTS idx_subscriptions_user_id;
        DROP INDEX IF EXISTS idx_subscriptions_subject;
        DROP INDEX IF EXISTS idx_subscriptions_status;
        DROP INDEX IF EXISTS idx_subscriptions_user_subject;
        DROP INDEX IF EXISTS idx_subscriptions_expires_at;
    """)
    
    # Remove indexes for survey_results table
    db.engine.execute("""
        DROP INDEX IF EXISTS idx_survey_results_user_id;
        DROP INDEX IF EXISTS idx_survey_results_subject;
        DROP INDEX IF EXISTS idx_survey_results_user_subject;
        DROP INDEX IF EXISTS idx_survey_results_completed_at;
    """)

if __name__ == '__main__':
    from app import create_app
    
    app = create_app()
    with app.app_context():
        upgrade()
        print("Performance indexes added successfully")