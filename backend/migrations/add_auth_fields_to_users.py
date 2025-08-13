"""
Database migration to add authentication fields to users table
"""
from app import db
from app.models.user import User
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

def upgrade():
    """Add authentication fields to users table"""
    try:
        # Check if we're using SQLite
        if 'sqlite' in str(db.engine.url):
            # SQLite doesn't support ALTER TABLE for adding NOT NULL columns
            # We need to recreate the table
            
            # First, backup existing data
            existing_users = db.session.execute(
                text("SELECT id, user_id, email, created_at, updated_at FROM users")
            ).fetchall()
            
            # Drop the existing table
            db.session.execute(text("DROP TABLE IF EXISTS users_backup"))
            db.session.execute(text("""
                CREATE TABLE users_backup AS 
                SELECT id, user_id, email, created_at, updated_at FROM users
            """))
            
            # Drop the original table
            db.session.execute(text("DROP TABLE users"))
            
            # Create new table with authentication fields
            db.session.execute(text("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(128) NOT NULL DEFAULT '',
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    last_login DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Migrate existing data with default password hash
            for user in existing_users:
                db.session.execute(text("""
                    INSERT INTO users (id, user_id, email, password_hash, is_active, created_at, updated_at)
                    VALUES (:id, :user_id, :email, :password_hash, :is_active, :created_at, :updated_at)
                """), {
                    'id': user.id,
                    'user_id': user.user_id,
                    'email': user.email or f"{user.user_id}@example.com",  # Ensure email is not null
                    'password_hash': 'temp_hash_needs_reset',  # Temporary hash - users will need to reset
                    'is_active': True,
                    'created_at': user.created_at,
                    'updated_at': user.updated_at
                })
            
            # Clean up backup table
            db.session.execute(text("DROP TABLE users_backup"))
            
        else:
            # For other databases, use ALTER TABLE
            db.session.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(128) NOT NULL DEFAULT 'temp_hash_needs_reset'"))
            db.session.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE"))
            db.session.execute(text("ALTER TABLE users ADD COLUMN last_login DATETIME"))
            db.session.execute(text("ALTER TABLE users ALTER COLUMN email SET NOT NULL"))
            db.session.execute(text("ALTER TABLE users ADD CONSTRAINT users_email_unique UNIQUE (email)"))
        
        db.session.commit()
        logger.info("Successfully added authentication fields to users table")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to add authentication fields: {str(e)}")
        raise

def downgrade():
    """Remove authentication fields from users table"""
    try:
        if 'sqlite' in str(db.engine.url):
            # For SQLite, recreate table without auth fields
            db.session.execute(text("DROP TABLE IF EXISTS users_backup"))
            db.session.execute(text("""
                CREATE TABLE users_backup AS 
                SELECT id, user_id, email, created_at, updated_at FROM users
            """))
            
            db.session.execute(text("DROP TABLE users"))
            
            db.session.execute(text("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Restore data
            db.session.execute(text("""
                INSERT INTO users (id, user_id, email, created_at, updated_at)
                SELECT id, user_id, email, created_at, updated_at FROM users_backup
            """))
            
            db.session.execute(text("DROP TABLE users_backup"))
            
        else:
            # For other databases
            db.session.execute(text("ALTER TABLE users DROP COLUMN password_hash"))
            db.session.execute(text("ALTER TABLE users DROP COLUMN is_active"))
            db.session.execute(text("ALTER TABLE users DROP COLUMN last_login"))
            db.session.execute(text("ALTER TABLE users DROP CONSTRAINT users_email_unique"))
            db.session.execute(text("ALTER TABLE users ALTER COLUMN email DROP NOT NULL"))
        
        db.session.commit()
        logger.info("Successfully removed authentication fields from users table")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to remove authentication fields: {str(e)}")
        raise

if __name__ == '__main__':
    # Run migration
    upgrade()