
import os
from datetime import datetime, timedelta

class PaymentModule:
    def __init__(self):
        # Configuration des clés (simulation)
        self.api_key = os.environ.get("PAYMENT_API_KEY", "test_key")
        self.site_id = os.environ.get("PAYMENT_SITE_ID", "test_id")

    def generate_payment_url(self, user_id, plan_type):
        """Génère un lien de paiement pour le test."""
        prices = {"2w": 500, "1m": 1000, "1y": 10000, "2y": 18000}
        amount = prices.get(plan_type, 1000)
        transaction_id = f"PAY-{user_id}-{int(datetime.now().timestamp())}"
        
        return {
            "status": "success",
            "payment_url": f"https://checkout.laure-universel.com/pay/{transaction_id}",
            "transaction_id": transaction_id
        }

    def verify_payment(self, transaction_id):
        """Vérifie le statut d'une transaction."""
        return True

def get_subscription_duration(plan_type):
    """Calcule la durée de l'abonnement."""
    durations = {
        "2w": timedelta(weeks=2),
        "1m": timedelta(days=30),
        "1y": timedelta(days=365),
        "2y": timedelta(days=730)
    }
    return durations.get(plan_type, timedelta(days=30))
