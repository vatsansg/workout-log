# Workout Log

A lightweight Flask-based workout logging app with a vibrant dashboard.

## Features

- Log exercises with sets, reps, weight, and notes
- View today's workouts and recent history
- Track exercise progress by name
- Delete workout entries
- Dashboard summary cards for total volume and exercise streaks
- 7-day volume trend chart

## Setup

1. Activate the virtual environment:
   ```powershell
   & .\venv\Scripts\Activate.ps1
   ```

2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

3. Run the app:
   ```powershell
   python app.py
   ```

4. Open the app in your browser:
   ```text
   http://127.0.0.1:5000
   ```

## Notes

- Data is stored in SQLite by default at `~/.workout_log.db`
- You can override the database path with the `WORKOUT_DB_PATH` environment variable

## Repository

- Remote: `https://github.com/vatsansg/workout-log`
