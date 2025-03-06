#!/usr/bin/env python
import os
import argparse
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='Repository Chat Assistant')
    parser.add_argument('--port', type=int, default=8080,
                        help='Port to run the web UI on (default: 8080)')
    args = parser.parse_args()

    # Determine web UI path
    current_dir = Path(__file__).parent
    web_ui_path = current_dir / "ui" / "web_ui" / "app.py"

    if web_ui_path.exists():
        web_ui_module = str(web_ui_path.parent).replace('/', '.').replace('\\', '.')
        sys.path.append(str(current_dir))

        # Run Flask web app
        try:
            from ui.web_ui.app import app
            print(f"Starting web UI on port {args.port}...")
            app.run(host='0.0.0.0', port=args.port, debug=True)
        except ImportError as e:
            print(f"Error loading web UI: {str(e)}")
            print("Make sure Flask is installed: pip install flask")
            sys.exit(1)
    else:
        print(f"Error: Web UI module not found at {web_ui_path}")
        sys.exit(1)

if __name__ == "__main__":
    main()