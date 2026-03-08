from flask import Blueprint, render_template, request, redirect, url_for
from app import db
from app.models import Task
from datetime import datetime, date, timedelta

main = Blueprint("main", __name__)

@main.route("/")
def index():
    status     = request.args.get("status", "")
    priority   = request.args.get("priority", "")
    due_filter = request.args.get("due", "")
    sort       = request.args.get("sort", "created_desc")

    query = Task.query

    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)

    today = date.today()
    if due_filter == "overdue":
        query = query.filter(Task.due_date < today, Task.is_done == False)
    elif due_filter == "today":
        query = query.filter(Task.due_date == today)
    elif due_filter == "this_week":
        query = query.filter(Task.due_date >= today,
                             Task.due_date <= today + timedelta(days=7))

    sort_map = {
        "created_desc":  Task.created_at.desc(),
        "created_asc":   Task.created_at.asc(),
        "due_asc":       Task.due_date.asc(),
        "due_desc":      Task.due_date.desc(),
        "priority_high": db.case(
            (Task.priority == "high",   1),
            (Task.priority == "medium", 2),
            (Task.priority == "low",    3),
            else_=4
        ),
        "priority_low": db.case(
            (Task.priority == "low",    1),
            (Task.priority == "medium", 2),
            (Task.priority == "high",   3),
            else_=4
        ),
        "alpha_asc":  Task.title.asc(),
        "alpha_desc": Task.title.desc(),
    }
    query = query.order_by(sort_map.get(sort, Task.created_at.desc()))
    tasks = query.all()

    return render_template("index.html", tasks=tasks,
                           status=status, priority=priority,
                           due_filter=due_filter, sort=sort)

@main.route("/add", methods=["POST"])
def add():
    title = request.form.get("title", "").strip()
    priority = request.form.get("priority", "medium")
    due_date_str = request.form.get("due_date", "")
    due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date() if due_date_str else None
    if title:
        db.session.add(Task(title=title, priority=priority, due_date=due_date))
        db.session.commit()
    return redirect(url_for("main.index"))

@main.route("/toggle/<int:task_id>")
def toggle(task_id):
    task = Task.query.get_or_404(task_id)
    task.is_done = not task.is_done
    task.status = "done" if task.is_done else "todo"
    db.session.commit()
    return redirect(url_for("main.index"))

@main.route("/delete/<int:task_id>")
def delete(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for("main.index"))

@main.route("/search")
def search():
    q = request.args.get("q", "").strip()
    tasks = []
    if q:
        pattern = f"%{q}%"
        tasks = Task.query.filter(
            db.or_(Task.title.ilike(pattern),
                   Task.description.ilike(pattern))
        ).order_by(Task.created_at.desc()).all()
    return render_template("search.html", tasks=tasks, q=q)

@main.route("/stats")
def stats():
    return render_template("stats.html")
