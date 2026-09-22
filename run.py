import subprocess
import sys

def main():
    command = sys.argv[1] if len(sys.argv) > 1 else "dashboard"
    if command == "seed":
        from app.seed import seed_database
        seed_database()
    elif command == "dashboard":
        subprocess.run([sys.executable, "-m", "streamlit", "run", "streamlit_app.py"], check=True)
    elif command == "api":
        subprocess.run([sys.executable, "-m", "uvicorn", "app.api:app", "--reload"], check=True)
    elif command == "test":
        subprocess.run([sys.executable, "-m", "pytest", "-q"], check=True)
    else:
        raise SystemExit("Usage: python run.py [seed|dashboard|api|test]")

if __name__ == "__main__":
    main()
