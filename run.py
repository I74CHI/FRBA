import os
import sys
import time
import webbrowser
import uvicorn
from app.db.database import init_db
from app.db.seed import seed_database

def main():
    if "--test-db" in sys.argv:
        print("[System Check] Testing Database Initialization and Seed...")
        init_db()
        seed_database()
        print("[System Check] Database Test Complete!")
        return

    print("=" * 65)
    print("  VisionAttend - Face Recognition Attendance System")
    print("  College Presentation Edition (FastAPI + OpenCV + Dlib)")
    print("=" * 65)
    print("[Starting Server] Hosting web application at http://127.0.0.1:8000")
    print("[Press Ctrl+C to terminate server]")
    print("-" * 65)

    # Open web browser automatically after 1.5 seconds
    def open_browser():
        time.sleep(1.5)
        webbrowser.open("http://127.0.0.1:8000")

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    # Start Uvicorn Server
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)

if __name__ == "__main__":
    main()
