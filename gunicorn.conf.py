import os

# Port dynamique pour Railway
port = os.environ.get("PORT", "3000")
bind = f"0.0.0.0:{port}"
workers = 1
threads = 8
timeout = 600
accesslog = "-"
errorlog = "-"
