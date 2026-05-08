# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```powershell
# Activate virtual environment (required first)
& .\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run the Flask web app (http://127.0.0.1:5000)
python app.py

# Run the CLI interface
python main.py
```

Override the database location:
```powershell
$env:WORKOUT_DB_PATH = "C:\path\to\custom.db"
```

## Architecture

The project has two independent interfaces backed by a single data layer:

- **`database.py`** — all SQLite operations. Called as `import database as db` by both interfaces. `init_db()` creates the `workouts` table if missing; `app.py` calls it at module load time (line 36).
- **`app.py`** — Flask web app with four routes: `GET /` (dashboard), `POST /log`, `POST /delete/<id>`, `GET+POST /progress`, `GET /all`. Templates live in `templates/`, CSS in `static/style.css`.
- **`main.py`** — interactive CLI using the `rich` library; same DB functions, different UI layer.

**Database:** SQLite at `~/.workout_log.db` (overridable via `WORKOUT_DB_PATH`). Single table:
```sql
workouts(id, date TEXT, exercise TEXT, sets INT, reps INT, weight REAL, notes TEXT)
```
Row tuples returned by all `db.get_*` functions follow index order: `[0]=id, [1]=date, [2]=exercise, [3]=sets, [4]=reps, [5]=weight, [6]=notes`.

**Volume trend chart** (`app.py:_build_volume_trend`): computed server-side and passed to `index.html` as pre-calculated SVG `<polyline>` point strings. No JS charting library is used.

**Volume metric**: defined as `sets × reps × weight` (weight defaults to 1 for bodyweight exercises), used consistently across `get_total_volume`, `get_daily_volume`, and the CLI's `track_progress`.

## Git Workflow

After completing any meaningful change, commit and push to GitHub:

```powershell
git add <specific files>
git commit -m "concise description of what changed and why"
git push origin main
```

- Stage specific files rather than `git add .` to avoid committing cache or env files
- Write commit messages that describe intent, not just mechanics (e.g. "fix streak calculation for same-day duplicates", not "update database.py")
- Push after every commit so there is always a saved version on GitHub

## Notes

- `app.config["SECRET_KEY"]` in `app.py` is a hardcoded placeholder — replace before any non-local deployment.
- `get_exercise_history` uses a `LIKE %query%` match, so the progress page accepts partial exercise names.
