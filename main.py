
import os
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description='Repository Chat Assistant')
    parser.add_argument('--ui', type=str, choices=['streamlit', 'web'], default='streamlit',
                        help='UI type to run: "streamlit" (default) or "web"')
    parser.add_argument('--port', type=int, default=8080,
                        help='Port to run the web UI on (default: 8080)')
    args = parser.parse_args()
    
    if args.ui == 'streamlit':
        # Run Streamlit app
        os.system(f"streamlit run app.py")
    else:
        # Run Flask web app
        try:
            from ui.web_ui.app import app
            print(f"Starting web UI on port {args.port}...")
            app.run(host='0.0.0.0', port=args.port, debug=True)
        except ImportError as e:
            print(f"Error loading web UI: {str(e)}")
            print("Make sure Flask is installed: pip install flask")
            sys.exit(1)

if __name__ == "__main__":
    main()
