import psycopg2
import redis
import sys

print("--- DÉBUT DES TESTS INFRASTRUCTURE ---")

# 1. Test PostgreSQL
try:
    print("[*] Tentative de connexion à PostgreSQL...", end=" ")
    # Connexion sans mot de passe (host=localhost est important pour le pg_hba.conf)
    conn = psycopg2.connect(
        dbname="laure_db",
        user="laure_user",
        host="127.0.0.1",
        port="5432"
    )
    conn.close()
    print("OK ! (Connecté à laure_db)")
except Exception as e:
    print(f"ÉCHEC !\nErreur : {e}")
    sys.exit(1)

# 2. Test Redis
try:
    print("[*] Tentative de connexion à Redis...", end=" ")
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping() # Envoie un ping
    print("OK ! (Redis répond PONG)")
except Exception as e:
    print(f"ÉCHEC !\nErreur : {e}")
    sys.exit(1)

print("--- TOUS LES SYSTÈMES SONT OPÉRATIONNELS ---")

