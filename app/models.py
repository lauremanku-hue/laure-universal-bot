from .extensions import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'laure_user'
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(20), default='whatsapp') # 'whatsapp', 'telegram', 'instagram'
    platform_id = db.Column(db.String(100), nullable=False) # ID spécifique au réseau
    name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    is_premium = db.Column(db.Boolean, default=False)
    quota_mb = db.Column(db.Float, default=100.0)
    bonus_given = db.Column(db.Boolean, default=False)
    
    __table_args__ = (db.UniqueConstraint('platform', 'platform_id', name='_user_platform_uc'),)

    def add_premium_bonus(self):
        if self.is_premium and not self.bonus_given:
            self.quota_mb += 300.0
            self.bonus_given = True
            return True
        return False

class Interaction(db.Model):
    __tablename__ = 'laure_interaction'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('laure_user.id'))
    last_message = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Course(db.Model):
    __tablename__ = 'laure_course'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('laure_user.id'))
    content = db.Column(db.Text, nullable=False)
    target_group = db.Column(db.String(100), nullable=False) # ID du groupe ou de la page
    scheduled_time = db.Column(db.DateTime, nullable=False)
    platform = db.Column(db.String(20), nullable=False) # 'whatsapp', 'telegram', etc.
    is_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
