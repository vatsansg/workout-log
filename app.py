from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, url_for

import database as db

app = Flask(__name__)
app.config["SECRET_KEY"] = "replace-with-a-secure-key"


def _fmt_weight(weight):
    return f"{weight:g}" if weight else "BW"


def _exercise_summary(history):
    first, last = history[0], history[-1]
    summary = {
        "first_date": first[1],
        "first_sets": first[3],
        "first_reps": first[4],
        "first_weight": _fmt_weight(first[5]),
        "latest_date": last[1],
        "latest_sets": last[3],
        "latest_reps": last[4],
        "latest_weight": _fmt_weight(last[5]),
        "weight_change": None,
        "weight_change_class": None,
    }
    if first[5] is not None and last[5] is not None:
        diff = last[5] - first[5]
        summary["weight_change"] = f"{diff:+.2g}"
        summary["weight_change_class"] = "positive" if diff >= 0 else "negative"
    return summary


db.init_db()


def _build_volume_trend(data):
    if not data:
        return {
            "path": "",
            "labels": [],
            "values": [],
            "max": 0,
            "min": 0,
        }

    values = [item[1] for item in data]
    labels = [item[0][5:] for item in data]
    max_value = max(values) or 1
    min_value = min(values)
    width = 560
    height = 140
    padding = 18
    point_count = len(values)
    x_step = (width - 2 * padding) / max(point_count - 1, 1)

    points = []
    for index, value in enumerate(values):
        x = padding + index * x_step
        ratio = (value - min_value) / (max_value - min_value) if max_value > min_value else 0.5
        y = padding + (height - 2 * padding) * (1 - ratio)
        points.append(f"{x:.1f},{y:.1f}")

    return {
        "path": " ".join(points),
        "labels": labels,
        "values": values,
        "max": max_value,
        "min": min_value,
    }


@app.route("/")
def index():
    today = db.get_today_workouts()
    recent = db.get_all_workouts(limit=50)
    exercises = db.get_all_exercises()
    total_volume = db.get_total_volume()
    streaks = db.get_exercise_streaks()
    daily_volume = db.get_daily_volume(days=7)
    volume_trend = _build_volume_trend(daily_volume)
    return render_template(
        "index.html",
        today=today,
        recent=recent,
        exercises=exercises,
        total=len(recent),
        total_volume=total_volume,
        streaks=streaks,
        volume_trend=volume_trend,
        fmt_weight=_fmt_weight,
    )


@app.route("/log", methods=["POST"])
def log_exercise():
    exercise = request.form.get("exercise", "").strip()
    sets = request.form.get("sets", "").strip()
    reps = request.form.get("reps", "").strip()
    weight = request.form.get("weight", "0").strip()
    notes = request.form.get("notes", "").strip()

    if not exercise:
        flash("Exercise name cannot be empty.", "error")
        return redirect(url_for("index"))

    try:
        sets = int(sets)
        reps = int(reps)
        weight = float(weight)
    except ValueError:
        flash("Sets, reps, and weight must be valid numbers.", "error")
        return redirect(url_for("index"))

    db.log_workout(exercise, sets, reps, weight, notes)
    label = f"{weight:g}" if weight else "bodyweight"
    flash(f"Logged {exercise} — {sets}×{reps} @ {label}.", "success")
    return redirect(url_for("index"))


@app.route("/delete/<int:workout_id>", methods=["POST"])
def delete_entry(workout_id):
    db.delete_workout(workout_id)
    flash(f"Deleted workout #{workout_id}.", "info")
    return redirect(url_for("index"))


@app.route("/progress", methods=["GET", "POST"])
def progress():
    exercise_query = request.values.get("exercise", "").strip()
    history = []
    summary = None

    if exercise_query:
        history = db.get_exercise_history(exercise_query)
        if not history:
            flash(f"No history found for '{exercise_query}'.", "warning")
        else:
            summary = _exercise_summary(history)

    exercises = db.get_all_exercises()
    return render_template(
        "progress.html",
        history=history,
        exercise_query=exercise_query,
        exercises=exercises,
        fmt_weight=_fmt_weight,
        summary=summary,
    )


@app.route("/all")
def all_workouts():
    rows = db.get_all_workouts(limit=200)
    return render_template(
        "all.html",
        workouts=rows,
        fmt_weight=_fmt_weight,
    )


if __name__ == "__main__":
    app.run(debug=True)
