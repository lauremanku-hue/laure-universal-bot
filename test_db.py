from app import create_app
# CORRECTION ICI : from app.extensions import db
from app.extensions import db
from app.models import User, Subscription

app = create_app()

with app.app_context():
    # Nettoyage
    db.drop_all()
    db.create_all()
    print("🧹 Base de données nettoyée.")

    # Création User
    new_user = User(phone_number="33612345678", username="TestUser")
    db.session.add(new_user)
    db.session.commit()
    print(f"👤 Utilisateur créé : {new_user.phone_number}")

    # Création Abo
    sub = Subscription(user_id=new_user.id, plan_type="Premium_2w")
    db.session.add(sub)
    db.session.commit()
    print(f"💎 Abonnement ajouté : {sub.plan_type}")

    # Vérif
    u = User.query.filter_by(phone_number="33612345678").first()
    print(f"🔍 Vérification : {u.username} est {u.subscription.plan_type}")


