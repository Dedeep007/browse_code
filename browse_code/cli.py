import os
import sys

def main():
    print("\n" + "="*60)
    print("Welcome to Browse Code!")
    print("Make sure you have the 'Browse Code Bridge' extension installed from the Chrome Web Store.")
    print("="*60 + "\n")
    
    print("Starting AI session server...\n")
    # Now we need to start the FastAPI server.
    # The original server.py is in the same package
    try:
        from .server import app
    except ImportError:
        # Fallback if run directly during dev
        from server import app
        
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5505, access_log=False)

if __name__ == "__main__":
    main()
