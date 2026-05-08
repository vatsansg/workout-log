import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(os.getenv("WORKOUT_DB_PATH", Path.home() / ".workout_log.db"))


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS workouts (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                date     TEXT    NOT NULL,
                exercise TEXT    NOT NULL,
                sets     INTEGER NOT NULL,
                reps     INTEGER NOT NULL,
                weight   REAL    DEFAULT 0,
                notes    TEXT    DEFAULT ''
            )
        """)
        conn.commit()


def log_workout(exercise, sets, reps, weight=0.0, notes="", date=None):
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO workouts (date, exercise, sets, reps, weight, notes) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (date, exercise.strip(), sets, reps, weight, notes.strip()),
        )
        conn.commit()


def get_all_workouts(limit=100):
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT id, date, exercise, sets, reps, weight, notes "
            "FROM workouts ORDER BY date DESC, id DESC LIMIT ?",
            (limit,),
        )
        return cur.fetchall()


def get_today_workouts():
    today = datetime.now().strftime("%Y-%m-%d")
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT id, date, exercise, sets, reps, weight, notes "
            "FROM workouts WHERE date = ? ORDER BY id ASC",
            (today,),
        )
        return cur.fetchall()


def get_exercise_history(exercise):
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT id, date, exercise, sets, reps, weight, notes "
            "FROM workouts WHERE exercise LIKE ? ORDER BY date ASC, id ASC",
            (f"%{exercise}%",),
        )
        return cur.fetchall()


def get_all_exercises():
    with get_connection() as conn:
        cur = conn.execute("SELECT DISTINCT exercise FROM workouts ORDER BY exercise")
        return [row[0] for row in cur.fetchall()]


def get_total_volume():
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT SUM(sets * reps * CASE WHEN weight > 0 THEN weight ELSE 1 END) "
            "FROM workouts"
        )
        row = cur.fetchone()
        return row[0] or 0


def get_daily_volume(days=7):
    cutoff = (datetime.now().date() - timedelta(days=days - 1)).strftime("%Y-%m-%d")
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT date, SUM(sets * reps * CASE WHEN weight > 0 THEN weight ELSE 1 END) "
            "FROM workouts WHERE date >= ? "
            "GROUP BY date ORDER BY date ASC",
            (cutoff,),
        )
        rows = cur.fetchall()

    date_to_volume = {row[0]: row[1] or 0 for row in rows}
    volumes = []
    for offset in range(days):
        day = datetime.now().date() - timedelta(days=days - 1 - offset)
        date_str = day.strftime("%Y-%m-%d")
        volumes.append((date_str, date_to_volume.get(date_str, 0)))
    return volumes


def _calculate_streak(dates):
    streak = 0
    expected = None
    for date_str in dates:
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            continue

        if expected is None:
            streak = 1
            expected = date - timedelta(days=1)
        elif date == expected:
            streak += 1
            expected = date - timedelta(days=1)
        else:
            break

    return streak


def get_exercise_streaks():
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT exercise, date FROM workouts "
            "ORDER BY exercise ASC, date DESC, id DESC"
        )
        rows = cur.fetchall()

    streaks = []
    current_exercise = None
    seen_dates = []

    for exercise, date_str in rows:
        if exercise != current_exercise:
            if current_exercise is not None:
                streaks.append((current_exercise, _calculate_streak(seen_dates)))
            current_exercise = exercise
            seen_dates = [date_str]
        elif seen_dates[-1] != date_str:
            seen_dates.append(date_str)

    if current_exercise is not None:
        streaks.append((current_exercise, _calculate_streak(seen_dates)))

    streaks.sort(key=lambda item: item[1], reverse=True)
    return streaks


def delete_workout(workout_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM workouts WHERE id = ?", (workout_id,))
        conn.commit()
