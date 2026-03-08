from flask import Blueprint, render_template, request, redirect, url_for
from app import db
from app.models import Task
from datetime import datetime

main = Blueprint("main", __name__)

@main.route("/")
def index():
    tasks = Task.query.order_by(Task.created_at.desc()).all()
    return render_template("index.html", tasks=tasks)

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
            db.or_(
                Task.title.ilike(pattern),
                Task.description.ilike(pattern)
            )
        ).order_by(Task.created_at.desc()).all()
    return render_template("search.html", tasks=tasks, q=q)

@main.route("/stats")
def stats():
    return render_template("stats.html")
