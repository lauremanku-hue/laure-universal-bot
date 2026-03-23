from .extensions import db
from datetime import datetime, timedelta

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(50))
    platform_id = db.Column(db.String(100), unique=True)
    name = db.Column(db.String(100))
    bonus_given = db.Column(db.Boolean, default=False)
    balance = db.Column(db.Float, default=0.0)
    is_premium = db.Column(db.Boolean, default=False)
    premium_ends_at = db.Column(db.DateTime, nullable=True)
    trial_ends_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(days=3))
    mode = db.Column(db.String(20), default='normal') # 'normal', 'professeur'
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def has_access(self):
        """Check if the user still has access (trial or premium)."""
        now = datetime.utcnow()
        if self.is_premium:
            if self.premium_ends_at and self.premium_ends_at > now:
                return True
            else:
                # Premium expired
                self.is_premium = False
                db.session.commit()
        
        if self.trial_ends_at and self.trial_ends_at > now:
            return True
        
        return False

class MessageLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(50))
    platform_id = db.Column(db.String(100))
    message_id = db.Column(db.String(100))
    content = db.Column(db.Text)
    sender_name = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class QuizSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.String(100))
    status = db.Column(db.String(50)) # 'active', 'completed'
    responses = db.Column(db.Text) # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
