from app import db
from datetime import datetime

class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('users.user_id'), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='active')
    purchased_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'subject'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'subject': self.subject,
            'status': self.status,
            'purchased_at': self.purchased_at.isoformat() if self.purchased_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }