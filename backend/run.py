import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app import create_app, db
from app.models.user import User
from app.models.survey_result import SurveyResult

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # Create database tables
        db.create_all()
        app.logger.info('Database tables created successfully')
    
    app.run(debug=True, port=5000, host='0.0.0.0')