from app import db
from datetime import datetime

class SurveyResult(db.Model):
    __tablename__ = 'survey_results'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('users.user_id'), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    skill_level = db.Column(db.String(20))
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'subject': self.subject,
            'skill_level': self.skill_level,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }