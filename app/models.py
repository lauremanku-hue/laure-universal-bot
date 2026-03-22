import os
from datetime import datetime, timedelta # Ajout de timedelta
from .extensions import db
from datetime import datetime, timedelta  # <--- Ajoute timedelta ici

class User(db.Model):
    __tablename__ = 'laure_user'
    
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(20), default='whatsapp')
    platform_id = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    balance = db.Column(db.Float, default=0.0)
    
    # Paramètres de quota et bonus
    is_premium_member = db.Column(db.Boolean, default=False)
    bonus_given = db.Column(db.Boolean, default=False) # Bonus 100 FCFA
    data_bonus_given = db.Column(db.Boolean, default=False) # Bonus 500 Mo
    trial_started_at = db.Column(db.DateTime, default=datetime.utcnow) # Début des 3 jours d'essai
    current_state = db.Column(db.String(50), default='idle') # Pour le guide de configuration
    state_data = db.Column(db.Text) # Données temporaires du guide (JSON)
    
    # Relations
    subscriptions = db.relationship('Subscription', backref='owner', lazy=True, cascade="all, delete-orphan")
    interactions = db.relationship('Interaction', backref='user', lazy=True, cascade="all, delete-orphan")

    __table_args__ = (db.UniqueConstraint('platform', 'platform_id', name='_user_platform_uc'),)

    @property
    def is_premium(self):
        # 1. Liste des numéros Admin (Hardcoded + Env Var)
        # On ajoute les numéros que tu as fournis pour être sûr
        admins = ["237659867487", "237686683246", "2376697236373", "659867487", "686683246", "6697236373"]
        
        # Ajout des numéros depuis les variables d'environnement
        env_admins = os.getenv("ADMIN_NUMBERS", "").split(",")
        admins.extend([a.strip() for a in env_admins if a.strip()])
        
        if self.platform_id in admins:
            return True
            
        now = datetime.utcnow()
        
        # 2. Vérifier la période d'essai de 3 jours
        # Si trial_started_at est nul (ancien utilisateur), on lui donne 3 jours à partir de maintenant
        if not self.trial_started_at:
            return True # On considère qu'il est en essai s'il n'a pas de date (sera fixé au prochain commit)
            
        trial_end = self.trial_started_at + timedelta(days=3)
        if now < trial_end:
            return True

        # 3. Vérifier les abonnements actifs (VIP payant)
        active = Subscription.query.filter(
            Subscription.user_id == self.id,
            Subscription.end_date > now,
            Subscription.status == 'active'
        ).first()
        
        return (active is not None) or self.is_premium_member

    @property
    def trial_days_left(self):
        if not self.trial_started_at:
            return 0
        now = datetime.utcnow()
        trial_end = self.trial_started_at + timedelta(days=3)
        delta = trial_end - now
        return max(0, delta.days + (1 if delta.seconds > 0 else 0))

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

class MessageLog(db.Model):
    __tablename__ = 'laure_message_log'
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(20))
    platform_id = db.Column(db.String(100)) # ID de l'utilisateur ou du groupe
    message_id = db.Column(db.String(100)) # ID unique du message sur la plateforme
    content = db.Column(db.Text)
    sender_name = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class QuizSession(db.Model):
    __tablename__ = 'laure_quiz_session'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.String(100)) # ID du groupe ou de l'utilisateur
    quiz_data = db.Column(db.Text) # JSON contenant les questions et réponses
    responses = db.Column(db.Text) # JSON contenant les réponses des participants {user_id: [answers]}
    status = db.Column(db.String(20), default='active') # active, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
