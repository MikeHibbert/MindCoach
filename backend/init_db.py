#!/usr/bin/env python3
"""
Database initialization script for the Personalized Learning Path Generator
"""

from app import create_app, db
from app.models.user import User
from app.models.subscription import Subscription
from app.models.survey_result import SurveyResult

def init_database():
    """Initialize the database with tables"""
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")
        
        # Print table information
        print("\nCreated tables:")
        print("- users")
        print("- subscriptions") 
        print("- survey_results")
        
        print("\nDatabase initialization complete!")

if __name__ == '__main__':
    init_database()