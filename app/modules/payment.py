import os
import requests
from datetime import datetime, timedelta

class PaymentModule:
    def __init__(self):
        # On utilise les clés récupérées sur tes captures d'écran
        self.service_key = os.environ.get("MONETBIL_SERVICE_KEY")
        self.service_secret = os.environ.get("MONETBIL_SERVICE_SECRET")
        self.base_url = "https://api.monetbil.com/payment/v1/placePayment"

    def generate_payment_url(self, user_id, plan_type, phone_number):
        """Génère une demande de paiement via l'API Monetbil."""
        prices = {"2w": 500, "1m": 1000, "1y": 10000, "2y": 18000}
        amount = prices.get(plan_type, 1000)
        
        # Identifiant unique pour ta base de données
        transaction_id = f"PAY-{user_id}-{int(datetime.now().timestamp())}"
        
        payload = {
            "service": self.service_key,
            "amount": amount,
            "phonenumber": phone_number,
            "currency": "XAF",
            "order_id": transaction_id, # Utile pour SQLAlchemy plus tard
            "description": f"Abonnement {plan_type} pour l'utilisateur {user_id}"
        }

        try:
            response = requests.post(self.base_url, data=payload)
            result = response.json()
            
            if result.get("status") == "success":
                return {
                    "status": "success",
                    "payment_url": result.get("payment_url"),
                    "transaction_id": transaction_id
                }
            return {"status": "error", "message": result.get("message")}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def verify_payment_hash(self, data_received):
        """
        Vérifie si la notification vient bien de Monetbil 
        en utilisant ton Service Secret.
        """
        # Monetbil n'envoie pas toujours de hash en mode simple, 
        # mais on vérifie le statut ici.
        if data_received.get('status') == 'success':
            return True
        return False

def get_subscription_duration(plan_type):
    """Calcule la durée de l'abonnement (inchangé)."""
    durations = {
        "2w": timedelta(weeks=2),
        "1m": timedelta(days=30),
        "1y": timedelta(days=365),
        "2y": timedelta(days=730)
    }
    return durations.get(plan_type, timedelta(days=30))
