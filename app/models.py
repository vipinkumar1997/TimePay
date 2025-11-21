from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    employee_id = db.Column(db.String(20), unique=True, nullable=True)
    designation = db.Column(db.String(50), nullable=True)
    department = db.Column(db.String(50), nullable=True)
    monthly_salary = db.Column(db.Float, nullable=False, default=0.0)
    ot_rate = db.Column(db.Float, nullable=False, default=0.0)
    is_admin = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    is_blocked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    last_ip = db.Column(db.String(50), nullable=True)
    overtimes = db.relationship('Overtime', backref='author', lazy=True, cascade="all, delete-orphan")
    attendances = db.relationship('Attendance', backref='author', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

class Overtime(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    hours = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Overtime('{self.date}', '{self.hours}')"

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False) # Present, Absent, Leave
    in_time = db.Column(db.Time, nullable=True)
    out_time = db.Column(db.Time, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Attendance('{self.date}', '{self.status}')"
