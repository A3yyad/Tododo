from app import db
from datetime import datetime

task_tags = db.Table('task_tags',
    db.Column('task_id', db.Integer, db.ForeignKey('task.id'), primary_key=True),
    db.Column('tag_id',  db.Integer, db.ForeignKey('tag.id'),  primary_key=True)
)

class Tag(db.Model):
    id    = db.Column(db.Integer, primary_key=True)
    name  = db.Column(db.String(50), nullable=False, unique=True)
    color = db.Column(db.String(7), default="#6366f1")

class Task(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    priority    = db.Column(db.String(10), default="medium")
    status      = db.Column(db.String(20), default="todo")
    is_done     = db.Column(db.Boolean, default=False)
    due_date    = db.Column(db.Date, nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_starred  = db.Column(db.Boolean, default=False)
    is_archived = db.Column(db.Boolean, default=False)

    subtasks = db.relationship('Subtask', backref='task', lazy=True, cascade="all, delete-orphan")
    comments = db.relationship('Comment', backref='task', lazy=True, cascade="all, delete-orphan")
    tags     = db.relationship('Tag', secondary=task_tags, lazy='subquery',
                               backref=db.backref('tasks', lazy=True))

    @property
    def subtask_progress(self):
        if not self.subtasks:
            return None
        done = sum(1 for s in self.subtasks if s.is_done)
        return {"done": done, "total": len(self.subtasks),
                "pct": int(done / len(self.subtasks) * 100)}

class Subtask(db.Model):
    id      = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    title   = db.Column(db.String(200), nullable=False)
    is_done = db.Column(db.Boolean, default=False)
    order   = db.Column(db.Integer, default=0)

class Comment(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    task_id    = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    body       = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
