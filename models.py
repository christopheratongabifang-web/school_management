from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)  # Increased to 512 for scrypt hash
    role = db.Column(db.String(20), nullable=False)  # SUPER_ADMIN, PRINCIPAL, BURSER, ACCOUNTANT, SECRETARY
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Income(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    source = db.Column(db.String(100), nullable=False)
    student_name = db.Column(db.String(100))
    student_session = db.Column(db.String(100))  # Anglophone or Francophone
    student_class = db.Column(db.String(100))
    section = db.Column(db.String(100))
    pta_level = db.Column(db.String(100))
    description = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    added_by = db.Column(db.Integer, db.ForeignKey('user.id'))

class SchoolSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<SchoolSetting {self.key}={self.value}>'

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    added_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(20), default='PENDING')  # PENDING, APPROVED, REJECTED
    approved_principal = db.Column(db.Boolean, default=False)
    approved_burser = db.Column(db.Boolean, default=False)
    approved_accountant = db.Column(db.Boolean, default=False)

class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    salary_type = db.Column(db.String(20), nullable=False, default='FIXED')
    salary = db.Column(db.Float, nullable=False)
    hourly_rate = db.Column(db.Float, default=0.0)
    hours_worked_month = db.Column(db.Float, default=0.0)
    hours_per_week = db.Column(db.Integer, nullable=False)
    teaching_details = db.Column(db.Text, default='[]')  # JSON list of {'class': str, 'subject': str, 'periods': int}
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(20))
    academic_year = db.Column(db.String(20), nullable=False)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='APPROVED')  # APPROVED, PENDING
    pending_action = db.Column(db.String(20), default='NONE')  # NONE, ADD, EDIT
    pending_changes = db.Column(db.Text)
    added_by = db.Column(db.Integer, db.ForeignKey('user.id'))

    @property
    def teaching_list(self):
        import json
        try:
            return json.loads(self.teaching_details or '[]')
        except:
            return []

    @property
    def total_periods_month(self):
        return sum(item.get('periods', 0) for item in self.teaching_list)

    @property
    def monthly_pay(self):
        if self.salary_type == 'HOURLY':
            return (self.hourly_rate or 0.0) * self.total_periods_month
        if self.salary_type == 'MIXED':
            return (self.salary or 0.0) + (self.hourly_rate or 0.0) * self.total_periods_month
        return self.salary or 0.0

    @property
    def payment_description(self):
        if self.salary_type == 'HOURLY':
            return f"Hourly ({self.hourly_rate or 0:.0f} FCFA x {self.total_periods_month} periods)"
        if self.salary_type == 'MIXED':
            return f"Fixed {self.salary or 0:.0f} + Hourly {self.hourly_rate or 0:.0f} x {self.total_periods_month}"
        return f"Fixed {self.salary or 0:.0f}"

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)

class Payroll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    staff_data = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))

class SystemLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(255), nullable=False)
    module = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f'<SystemLog {self.action} by user {self.user_id} at {self.timestamp}>'