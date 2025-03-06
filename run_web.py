
import os
from ui.web_ui.app import app

if __name__ == "__main__":
    # Get port from environment or use default 8080
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
