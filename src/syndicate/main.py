import subprocess
from pathlib import Path


def main() -> None:
    app_path = Path(__file__).parent / "app.py"
    subprocess.run([
        "streamlit",
        "run",
        str(app_path),
        "--client.toolbarMode", "minimal"
    ])


if __name__ == "__main__":
    main()
