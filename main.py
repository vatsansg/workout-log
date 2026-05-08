from datetime import datetime

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import FloatPrompt, IntPrompt, Prompt
from rich.table import Table

import database as db

console = Console()


# ── helpers ──────────────────────────────────────────────────────────────────

def _fmt_weight(w):
    return f"{w:g}" if w else "BW"


def _workout_table(title, rows, border="blue"):
    t = Table(title=title, box=box.ROUNDED, border_style=border, show_lines=True)
    t.add_column("ID",       style="dim",       width=5)
    t.add_column("Date",     style="cyan")
    t.add_column("Exercise", style="bold white")
    t.add_column("Sets",     justify="center")
    t.add_column("Reps",     justify="center")
    t.add_column("Weight",   justify="center")
    t.add_column("Notes",    style="dim")
    for r in rows:
        t.add_row(str(r[0]), r[1], r[2], str(r[3]), str(r[4]),
                  _fmt_weight(r[5]), r[6] or "—")
    return t


# ── actions ───────────────────────────────────────────────────────────────────

def log_exercise():
    console.print("\n[bold green]─── Log Exercise ───[/bold green]")

    exercises = db.get_all_exercises()
    if exercises:
        console.print("[dim]Known exercises: " + ", ".join(exercises) + "[/dim]")

    exercise = Prompt.ask("Exercise name").strip()
    if not exercise:
        console.print("[red]Exercise name cannot be empty.[/red]")
        return

    sets   = IntPrompt.ask("Sets",                      default=3)
    reps   = IntPrompt.ask("Reps per set",               default=10)
    weight = FloatPrompt.ask("Weight (kg/lbs, 0 = bodyweight)", default=0.0)
    notes  = Prompt.ask("Notes (optional)",              default="")

    db.log_workout(exercise, sets, reps, weight, notes)
    label = f"{weight:g}" if weight else "bodyweight"
    console.print(f"\n[green]✓ Logged:[/green] {exercise} — {sets}×{reps} @ {label}")


def view_today():
    rows  = db.get_today_workouts()
    today = datetime.now().strftime("%Y-%m-%d")
    if not rows:
        console.print(f"[yellow]No workouts logged for today ({today}).[/yellow]")
        return
    console.print(f"\n[bold]Total exercises today:[/bold] {len(rows)}")
    console.print(_workout_table(f"Today — {today}", rows, border="green"))


def view_all():
    rows = db.get_all_workouts(limit=100)
    if not rows:
        console.print("[yellow]No workouts logged yet.[/yellow]")
        return
    console.print(_workout_table("All Workouts (last 100)", rows, border="blue"))


def track_progress():
    exercises = db.get_all_exercises()
    if not exercises:
        console.print("[yellow]No exercises logged yet.[/yellow]")
        return

    console.print("\n[bold]Logged exercises:[/bold]")
    for i, ex in enumerate(exercises, 1):
        console.print(f"  [cyan]{i}.[/cyan] {ex}")

    search = Prompt.ask("\nEnter exercise name (or part of it)").strip()
    if not search:
        return

    history = db.get_exercise_history(search)
    if not history:
        console.print(f"[yellow]No history found for '{search}'.[/yellow]")
        return

    t = Table(title=f"Progress: {history[0][2]}", box=box.ROUNDED,
              border_style="magenta", show_lines=True)
    t.add_column("Date",    style="cyan")
    t.add_column("Sets",    justify="center")
    t.add_column("Reps",    justify="center")
    t.add_column("Weight",  justify="center")
    t.add_column("Volume (s×r×w)", justify="center", style="yellow")
    t.add_column("Notes",   style="dim")

    for r in history:
        w      = r[5] if r[5] else 1
        volume = r[3] * r[4] * w
        t.add_row(r[1], str(r[3]), str(r[4]),
                  _fmt_weight(r[5]), f"{volume:.0f}", r[6] or "—")

    console.print(t)

    if len(history) > 1:
        first, last = history[0], history[-1]
        console.print("\n[bold]Progress summary:[/bold]")
        console.print(f"  First: [cyan]{first[1]}[/cyan] — "
                      f"{first[3]}×{first[4]} @ {_fmt_weight(first[5])}")
        console.print(f"  Latest:[cyan]{last[1]}[/cyan] — "
                      f"{last[3]}×{last[4]} @ {_fmt_weight(last[5])}")
        if first[5] and last[5]:
            diff  = last[5] - first[5]
            color = "green" if diff >= 0 else "red"
            console.print(f"  Weight change: [{color}]{diff:+.2g}[/{color}]")


def delete_entry():
    rows = db.get_all_workouts(limit=20)
    if not rows:
        console.print("[yellow]No workouts to delete.[/yellow]")
        return

    console.print(_workout_table("Recent Workouts", rows))
    wid = IntPrompt.ask("\nEnter ID to delete (0 = cancel)", default=0)
    if wid == 0:
        return

    db.delete_workout(wid)
    console.print(f"[red]Deleted entry #{wid}.[/red]")


# ── main loop ─────────────────────────────────────────────────────────────────

MENU = """[bold cyan]1[/bold cyan] Log exercise
[bold cyan]2[/bold cyan] View today's workout
[bold cyan]3[/bold cyan] View all workouts
[bold cyan]4[/bold cyan] Track exercise progress
[bold cyan]5[/bold cyan] Delete an entry
[bold cyan]0[/bold cyan] Exit"""

ACTIONS = {
    "1": log_exercise,
    "2": view_today,
    "3": view_all,
    "4": track_progress,
    "5": delete_entry,
}


def main():
    db.init_db()
    console.print(Panel("[bold cyan]Workout Log[/bold cyan]  —  track your gains",
                        border_style="cyan"))

    while True:
        console.print()
        console.print(Panel(MENU, title="Menu", border_style="cyan", expand=False))
        choice = Prompt.ask("Choose", choices=list(ACTIONS) + ["0"], default="0")

        if choice == "0":
            console.print("\n[cyan]Stay consistent. See you next session![/cyan]")
            break

        ACTIONS[choice]()


if __name__ == "__main__":
    main()
