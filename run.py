from app import app, db
import os

import threading
import time
import requests

def keep_alive():
    """
    Pings the application's own URL every 30 seconds to prevent Render from sleeping.
    """
    # Get the external URL from Render environment variable
    # If not set (local dev), we can skip or use localhost if needed.
    # For Render, RENDER_EXTERNAL_HOSTNAME is usually available or we can use a custom env var.
    # A common pattern is to just ping the known URL if we know it, or use localhost if running locally?
    # Actually, for Render free tier, we need to ping the PUBLIC URL.
    # Render provides RENDER_EXTERNAL_URL.
    
    url = os.environ.get('RENDER_EXTERNAL_URL')
    
    if not url:
        # If we are local, we might not want to ping, or we ping localhost
        # But the user specifically asked for Render.
        # Let's just print a message if no URL found.
        print("Keep-alive: No RENDER_EXTERNAL_URL found. Skipping pings.")
        return

    if not url.endswith('/health'):
        url = f"{url}/health"

    print(f"Keep-alive: Starting pings to {url} every 30 seconds.")
    
    while True:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print("Keep-alive: Ping successful")
            else:
                print(f"Keep-alive: Ping failed with status {response.status_code}")
        except Exception as e:
            print(f"Keep-alive: Ping error: {e}")
        
        time.sleep(30)

if __name__ == '__main__':
    # Start the keep-alive thread
    # We use a daemon thread so it dies when the main thread dies
    threading.Thread(target=keep_alive, daemon=True).start()

    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
