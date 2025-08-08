#!/usr/bin/env python3
"""
Initial database schema migration
Creates users, subscriptions, and survey_results tables
"""

from app import create_app, db
from app.models.user import User
from app.models.subscription import Subscription
from app.models.survey_result import SurveyResult

def upgrade():
    """Apply the migration"""
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✓ Created users table")
        print("✓ Created subscriptions table") 
        print("✓ Created survey_results table")
        print("Migration 001_initial_schema applied successfully!")

def downgrade():
    """Rollback the migration"""
    app = create_app()
    
    with app.app_context():
        # Drop all tables
        db.drop_all()
        print("✓ Dropped all tables")
        print("Migration 001_initial_schema rolled back successfully!")

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'downgrade':
        downgrade()
    else:
        upgrade()