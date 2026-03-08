from flask import Blueprint, render_template, request, redirect, url_for
from app import db
from app.models import Task, Subtask, Comment, Tag
from datetime import datetime, date, timedelta

main = Blueprint("main", __name__)

def build_task_query():
    status     = request.args.get("status", "")
    priority   = request.args.get("priority", "")
    due_filter = request.args.get("due", "")
    sort       = request.args.get("sort", "created_desc")
    q          = request.args.get("q", "").strip()
    tag_filter = request.args.get("tag", "")
    archived   = request.args.get("archived", "")

    query = Task.query.filter(Task.is_archived == (archived == "1"))

    if q:
        pattern = f"%{q}%"
        query = query.filter(
            db.or_(Task.title.ilike(pattern), Task.description.ilike(pattern))
        )
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    if tag_filter:
        query = query.filter(Task.tags.any(Tag.name == tag_filter))

    today = date.today()
    if due_filter == "overdue":
        query = query.filter(Task.due_date < today, Task.is_done == False)
    elif due_filter == "today":
        query = query.filter(Task.due_date == today)
    elif due_filter == "this_week":
        query = query.filter(Task.due_date >= today,
                             Task.due_date <= today + timedelta(days=7))
    elif due_filter == "starred":
        query = query.filter(Task.is_starred == True)

    sort_map = {
        "created_desc":  Task.created_at.desc(),
        "created_asc":   Task.created_at.asc(),
        "due_asc":       Task.due_date.asc(),
        "due_desc":      Task.due_date.desc(),
        "priority_high": db.case(
            (Task.priority == "high",   1),
            (Task.priority == "medium", 2),
            (Task.priority == "low",    3), else_=4),
        "priority_low": db.case(
            (Task.priority == "low",    1),
            (Task.priority == "medium", 2),
            (Task.priority == "high",   3), else_=4),
        "alpha_asc":  Task.title.asc(),
        "alpha_desc": Task.title.desc(),
    }
    query = query.order_by(sort_map.get(sort, Task.created_at.desc()))
    return query, dict(status=status, priority=priority, due_filter=due_filter,
                       sort=sort, q=q, tag_filter=tag_filter, archived=archived)

@main.route("/")
def index():
    query, filters = build_task_query()
    tasks  = query.all()
    tags   = Tag.query.order_by(Tag.name).all()
    today  = date.today()
    overdue_count = Task.query.filter(Task.due_date < today, Task.is_done == False, Task.is_archived == False).count()
    starred_count = Task.query.filter(Task.is_starred == True, Task.is_archived == False).count()
    today_count   = Task.query.filter(Task.due_date == today, Task.is_archived == False).count()
    total_active  = Task.query.filter(Task.is_archived == False).count()
    done_count    = Task.query.filter(Task.status == "done", Task.is_archived == False).count()
    return render_template("index.html", tasks=tasks, tags=tags,
                           overdue_count=overdue_count, starred_count=starred_count,
                           today_count=today_count, total_active=total_active,
                           done_count=done_count, today=today, **filters)

@main.route("/add", methods=["POST"])
def add():
    title        = request.form.get("title", "").strip()
    description  = request.form.get("description", "").strip()
    priority     = request.form.get("priority", "medium")
    due_date_str = request.form.get("due_date", "")
    due_date     = datetime.strptime(due_date_str, "%Y-%m-%d").date() if due_date_str else None
    tag_ids      = request.form.getlist("tag_ids")
    if title:
        task = Task(title=title, description=description, priority=priority, due_date=due_date)
        for tid in tag_ids:
            tag = Tag.query.get(int(tid))
            if tag:
                task.tags.append(tag)
        db.session.add(task)
        db.session.commit()
    return redirect(url_for("main.index"))

@main.route("/task/<int:task_id>")
def task_detail(task_id):
    task = Task.query.get_or_404(task_id)
    tags = Tag.query.order_by(Tag.name).all()
    return render_template("task_detail.html", task=task, tags=tags, today=date.today())

@main.route("/edit/<int:task_id>", methods=["POST"])
def edit(task_id):
    task = Task.query.get_or_404(task_id)
    task.title       = request.form.get("title", task.title).strip()
    task.description = request.form.get("description", "").strip()
    task.priority    = request.form.get("priority", "medium")
    task.status      = request.form.get("status", task.status)
    due_date_str     = request.form.get("due_date", "")
    task.due_date    = datetime.strptime(due_date_str, "%Y-%m-%d").date() if due_date_str else None
    task.updated_at  = datetime.utcnow()
    tag_ids   = request.form.getlist("tag_ids")
    task.tags = []
    for tid in tag_ids:
        tag = Tag.query.get(int(tid))
        if tag:
            task.tags.append(tag)
    db.session.commit()
    return redirect(url_for("main.task_detail", task_id=task_id))

@main.route("/toggle/<int:task_id>")
def toggle(task_id):
    task = Task.query.get_or_404(task_id)
    task.is_done = not task.is_done
    task.status  = "done" if task.is_done else "todo"
    task.updated_at = datetime.utcnow()
    db.session.commit()
    return redirect(request.referrer or url_for("main.index"))

@main.route("/star/<int:task_id>")
def star(task_id):
    task = Task.query.get_or_404(task_id)
    task.is_starred = not task.is_starred
    db.session.commit()
    return redirect(request.referrer or url_for("main.index"))

@main.route("/archive/<int:task_id>")
def archive(task_id):
    task = Task.query.get_or_404(task_id)
    task.is_archived = not task.is_archived
    db.session.commit()
    return redirect(request.referrer or url_for("main.index"))

@main.route("/delete/<int:task_id>")
def delete(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for("main.index"))

@main.route("/bulk", methods=["POST"])
def bulk():
    action   = request.form.get("action")
    task_ids = request.form.getlist("task_ids")
    tasks    = Task.query.filter(Task.id.in_([int(i) for i in task_ids])).all()
    for task in tasks:
        if action == "done":
            task.is_done = True
            task.status  = "done"
        elif action == "delete":
            db.session.delete(task)
        elif action == "archive":
            task.is_archived = True
        elif action == "star":
            task.is_starred = True
    db.session.commit()
    return redirect(url_for("main.index"))

@main.route("/task/<int:task_id>/subtask/add", methods=["POST"])
def add_subtask(task_id):
    title = request.form.get("title", "").strip()
    if title:
        count = Subtask.query.filter_by(task_id=task_id).count()
        db.session.add(Subtask(task_id=task_id, title=title, order=count))
        db.session.commit()
    return redirect(url_for("main.task_detail", task_id=task_id))

@main.route("/subtask/toggle/<int:sub_id>")
def toggle_subtask(sub_id):
    sub = Subtask.query.get_or_404(sub_id)
    sub.is_done = not sub.is_done
    db.session.commit()
    return redirect(url_for("main.task_detail", task_id=sub.task_id))

@main.route("/subtask/delete/<int:sub_id>")
def delete_subtask(sub_id):
    sub = Subtask.query.get_or_404(sub_id)
    task_id = sub.task_id
    db.session.delete(sub)
    db.session.commit()
    return redirect(url_for("main.task_detail", task_id=task_id))

@main.route("/task/<int:task_id>/comment/add", methods=["POST"])
def add_comment(task_id):
    body = request.form.get("body", "").strip()[:1000]
    if body:
        db.session.add(Comment(task_id=task_id, body=body))
        db.session.commit()
    return redirect(url_for("main.task_detail", task_id=task_id))

@main.route("/comment/delete/<int:comment_id>")
def delete_comment(comment_id):
    c = Comment.query.get_or_404(comment_id)
    task_id = c.task_id
    db.session.delete(c)
    db.session.commit()
    return redirect(url_for("main.task_detail", task_id=task_id))

@main.route("/tags")
def tags():
    all_tags = Tag.query.order_by(Tag.name).all()
    return render_template("tags.html", tags=all_tags)

@main.route("/tags/add", methods=["POST"])
def add_tag():
    name  = request.form.get("name", "").strip()[:50]
    color = request.form.get("color", "#6366f1")
    if name and not Tag.query.filter_by(name=name).first():
        db.session.add(Tag(name=name, color=color))
        db.session.commit()
    return redirect(url_for("main.tags"))

@main.route("/tags/delete/<int:tag_id>")
def delete_tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    db.session.delete(tag)
    db.session.commit()
    return redirect(url_for("main.tags"))

@main.route("/stats")
def stats():
    today    = date.today()
    week_ago = today - timedelta(days=7)
    total        = Task.query.filter(Task.is_archived == False).count()
    done         = Task.query.filter(Task.status == "done", Task.is_archived == False).count()
    todo         = Task.query.filter(Task.status == "todo", Task.is_archived == False).count()
    doing        = Task.query.filter(Task.status == "doing", Task.is_archived == False).count()
    overdue      = Task.query.filter(Task.due_date < today, Task.is_done == False, Task.is_archived == False).count()
    starred      = Task.query.filter(Task.is_starred == True).count()
    archived     = Task.query.filter(Task.is_archived == True).count()
    completed_7d = Task.query.filter(
        Task.is_done == True,
        Task.updated_at >= datetime.combine(week_ago, datetime.min.time())
    ).count()
    trend = []
    for i in range(6, -1, -1):
        day       = today - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end   = datetime.combine(day, datetime.max.time())
        count = Task.query.filter(
            Task.is_done == True,
            Task.updated_at >= day_start,
            Task.updated_at <= day_end
        ).count()
        trend.append({"day": day.strftime("%a"), "date": day.strftime("%b %d"), "count": count})
    priority_counts = {
        "high":   Task.query.filter(Task.priority == "high",   Task.is_archived == False).count(),
        "medium": Task.query.filter(Task.priority == "medium", Task.is_archived == False).count(),
        "low":    Task.query.filter(Task.priority == "low",    Task.is_archived == False).count(),
    }
    tag_counts = []
    for tag in Tag.query.all():
        tag_counts.append({"name": tag.name, "color": tag.color, "count": len(tag.tasks)})
    tag_counts.sort(key=lambda x: x["count"], reverse=True)
    completion_rate = round((done / total * 100), 1) if total else 0
    return render_template("stats.html",
        total=total, done=done, todo=todo, doing=doing,
        overdue=overdue, starred=starred, archived=archived,
        completed_7d=completed_7d, trend=trend,
        priority_counts=priority_counts, tag_counts=tag_counts,
        completion_rate=completion_rate, today=today)
