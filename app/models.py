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
    current_question_index = db.Column(db.Integer, default=0)
    total_questions = db.Column(db.Integer, default=20)
    correct_answers_count = db.Column(db.Integer, default=0)
    questions_data = db.Column(db.Text) # JSON string of questions and correct answers
    responses = db.Column(db.Text) # JSON string of user answers
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ScheduledCourse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(200))
    target_jid = db.Column(db.String(100)) # Group or User JID
    day_of_week = db.Column(db.Integer) # 0-6 (Mon-Sun)
    scheduled_time = db.Column(db.String(10)) # "HH:MM"
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
