@echo off

REM Go to project folder
cd /d D:\Projects\Customer_Due_Tracker_System

REM Start backend minimized
start "🔧 BACKEND" /min cmd /k "python backend\app.py"

REM Start frontend minimized
start "🖥️ FRONTEND" /min cmd /k "streamlit run frontend\streamlit_app.py"
