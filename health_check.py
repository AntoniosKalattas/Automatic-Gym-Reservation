import os
import sys
import socket
import requests

def check_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        return s.connect_ex(('127.0.0.1', port)) == 0

def run_health_check():
    print("=" * 60)
    print("      GYM RESERVATION PROJECT LOCAL HEALTH CHECK      ")
    print("=" * 60)

    # 1. Environment variables check
    print("\n[1] Checking .env configuration...")
    if not os.path.exists(".env"):
        print("❌ .env file not found!")
    else:
        print("✅ .env file exists.")
        from dotenv import load_dotenv
        load_dotenv()
        chrome_path = os.getenv("CHROME_PROFILE_PATH")
        if chrome_path:
            if os.path.exists(chrome_path):
                print(f"✅ CHROME_PROFILE_PATH exists: {chrome_path}")
            else:
                print(f"⚠️ CHROME_PROFILE_PATH directory does not exist: {chrome_path}")
        else:
            print("⚠️ CHROME_PROFILE_PATH not set in .env")

    # 2. Server status check
    api_running = check_port_open(5001)
    metro_running = check_port_open(8081)
    
    print("\n[2] Checking local servers...")
    print(f"{'Flask API (Port 5001):':<25} {'Running ✅' if api_running else 'Offline ❌'}")
    print(f"{'Expo Metro (Port 8081):':<25} {'Running ✅' if metro_running else 'Offline (Start with npm start in mobile/ if debugging)'}")

    # 3. API Functional Checks
    if api_running:
        print("\n[3] Testing API endpoints...")
        try:
            # Health endpoint
            res = requests.get("http://localhost:5001/health", timeout=3)
            if res.status_code == 200 and res.json().get("ok") is True:
                print("✅ GET /health -> OK")
            else:
                print(f"❌ GET /health returned invalid response: {res.text}")
                
            # Schedule endpoint
            res = requests.get("http://localhost:5001/schedule", timeout=3)
            if res.status_code == 200:
                print("✅ GET /schedule -> OK")
            else:
                print(f"❌ GET /schedule failed with status: {res.status_code}")
                
            # Sniper status endpoint
            res = requests.get("http://localhost:5001/snipe", timeout=3)
            if res.status_code == 200:
                print("✅ GET /snipe -> OK")
            else:
                print(f"❌ GET /snipe failed with status: {res.status_code}")
        except Exception as e:
            print(f"❌ API connection tests crashed: {e}")

    # 4. Proxy check
    if api_running and metro_running:
        print("\n[4] Testing API proxy to Metro...")
        try:
            # Fetch / from 5001 which should proxy to 8081
            res = requests.get("http://localhost:5001/", timeout=3)
            if res.status_code in [200, 304, 404]: # Metro might return 404/200 depending on platform headers
                print(f"✅ Reverse proxy connection -> OK (Status code: {res.status_code})")
            else:
                print(f"❌ Reverse proxy returned unexpected status: {res.status_code}")
        except Exception as e:
            print(f"❌ Reverse proxy test failed: {e}")

    print("\n" + "=" * 60)
    print("                    HEALTH CHECK COMPLETED                    ")
    print("=" * 60)

if __name__ == "__main__":
    run_health_check()
