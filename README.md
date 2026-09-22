# NEXORAAI

AI-powered Business Intelligence and Autonomous Operations platform.

## Setup
```powershell
py -3.14 -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
venv\Scripts\activate
python -m pip install -r requirements.txt
python -m database.init_db
python -m database.seed_data
uvicorn backend.main:app --reload
```
Open http://127.0.0.1:8000
