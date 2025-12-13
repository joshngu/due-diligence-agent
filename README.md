# Endowment Simulator

A simple guide to set up and run the Streamlit app.

## Quick Start (Windows)
- **Clone or open the project:** Ensure you have this folder locally.
- **Install Python 3.10+:** Verify Python is available on your PATH.
- **Create and activate a virtual environment:**
	- PowerShell:
		```powershell
		python -m venv .venv
		.\.venv\Scripts\Activate.ps1
		```
- **Install dependencies:**
	```powershell
	pip install -r requirements.txt
	```
- **Run the app:**
	```powershell
	streamlit run app.py
	```

The app will open in your browser (usually http://localhost:8501).

## Project Structure
- `app.py`: Streamlit application entry point.
- `requirements.txt`: Python dependencies.
- `scripts/check_scripts/`: Optional environment checks.

## Optional: Environment Checks
You can run small checks to verify your setup:
- **Python/Streamlit check:**
	```powershell
	python scripts/check_scripts/check_streamlit_env.py
	```
- **LangChain version check:**
	```powershell
	python scripts/check_scripts/check_langchain_version.py
	```

## Optional: Using Ollama (Local LLM)
If the app uses a local LLM via Ollama, install and run a model first:
- **Install Ollama:** https://ollama.com
- **Start a model:**
	```powershell
	ollama run llama3.2
	```
Then launch the app as usual: `streamlit run app.py`.

## Troubleshooting
- **Command not found (streamlit/pip):** Ensure the virtual environment is activated (`.\.venv\Scripts\Activate.ps1`).
- **Port already in use:** Run `streamlit run app.py --server.port 8502` or close the existing session.
- **Dependency issues:** Reinstall dependencies with `pip install -r requirements.txt`.
- **Firewall prompts:** Allow local network access for Streamlit when prompted.

## Development Tips
- Keep the venv active while working.
- After editing `requirements.txt`, run `pip install -r requirements.txt`.
- Streamlit offers hot-reload; changes in `app.py` refresh the app automatically.
