import os
from .extensions import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'laure_user'
    
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(20), default='whatsapp')
    platform_id = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Paramètres de quota et bonus
    is_premium_member = db.Column(db.Boolean, default=False)
    bonus_given = db.Column(db.Boolean, default=False) # Bonus 100 FCFA
    data_bonus_given = db.Column(db.Boolean, default=False) # Bonus 500 Mo
    
    # Relations
    subscriptions = db.relationship('Subscription', backref='owner', lazy=True, cascade="all, delete-orphan")
    interactions = db.relationship('Interaction', backref='user', lazy=True, cascade="all, delete-orphan")

    __table_args__ = (db.UniqueConstraint('platform', 'platform_id', name='_user_platform_uc'),)

    @property
    def is_premium(self):
        # Vérifier si le numéro est dans la liste des admins (via variable d'env)
        admin_numbers = os.getenv("ADMIN_NUMBERS", "").split(",")
        if self.platform_id in admin_numbers:
            return True
            
        now = datetime.utcnow()
        active = Subscription.query.filter(
            Subscription.user_id == self.id,
            Subscription.end_date > now,
            Subscription.status == 'active'
        ).first()
        return (active is not None) or self.is_premium_member

class Subscription(db.Model):
    __tablename__ = 'laure_subscription'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('laure_user.id'), nullable=False)
    plan_type = db.Column(db.String(20))
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='active')
    transaction_id = db.Column(db.String(100), unique=True)

class Interaction(db.Model):
    __tablename__ = 'laure_interaction'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('laure_user.id'), nullable=False)
    last_message = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending') 
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Course(db.Model):
    __tablename__ = 'laure_course'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('laure_user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    target_group = db.Column(db.String(100))
    scheduled_time = db.Column(db.DateTime, nullable=False)
    is_sent = db.Column(db.Boolean, default=False)
    platform = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
