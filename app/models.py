from app import db
from datetime import datetime

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
