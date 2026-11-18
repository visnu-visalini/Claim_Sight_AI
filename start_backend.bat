@echo off
rem --------------------------------------------------------------
rem  ClaimSightAI – Backend auto‑setup & start script
rem  1) Create (or reuse) a virtual environment
rem  2) Install / upgrade required Python packages
rem  3) Run the Flask development server
rem --------------------------------------------------------------

rem ---- 1) Ensure a venv exists ------------------------------------------------
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
) else (
    echo Virtual environment already exists.
)

rem ---- 2) Activate the venv ----------------------------------------------------
call venv\Scripts\activate

rem ---- 3) Upgrade pip (optional but recommended) -------------------------------
python -m pip install --upgrade pip

rem ---- 4) Install project requirements -----------------------------------------
echo Installing Python dependencies...
pip install -r Backend\requirements.txt

rem ---- 5) Run the Flask app ----------------------------------------------------
echo Starting ClaimSightAI backend on http://127.0.0.1:5000/
python Backend\run.py

