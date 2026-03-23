from app import create_app
import threading
from app.modules.whatsapp_web import LaureWebBot

app = create_app()

def start_bot():
    """
    Start the WhatsApp bot in a separate thread.
    """
    with app.app_context():
        bot = LaureWebBot()
        app.bot = bot
        bot.start(app=app)

# Start the bot thread
bot_thread = threading.Thread(target=start_bot, daemon=True)
bot_thread.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
