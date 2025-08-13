#!/usr/bin/env python3
"""
Simple migration runner for authentication fields
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from migrations.add_auth_fields_to_users import upgrade

def run_migration():
    """Run the authentication migration"""
    app = create_app('development')
    
    with app.app_context():
        try:
            print("Running authentication migration...")
            upgrade()
            print("Migration completed successfully!")
            
        except Exception as e:
            print(f"Migration failed: {str(e)}")
            sys.exit(1)

if __name__ == '__main__':
    run_migration()