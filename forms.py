from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, IntegerField, SelectField, TextAreaField, HiddenField, DateField
from wtforms.validators import DataRequired, Email, Length, ValidationError, EqualTo, NumberRange, Optional
import re

def password_check(form, field):
    if len(field.data) < 6:
        raise ValidationError('Password must be at least 6 characters long.')
    if not re.search(r"[A-Z]", field.data):
        raise ValidationError('Password must contain at least one uppercase letter.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ResetPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class NewPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), password_check])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), password_check])
    role = SelectField('Role', choices=[
        ('PRINCIPAL', 'Principal'),
        ('BURSER', 'Burser'),
        ('ACCOUNTANT', 'Accountant'),
        ('SECRETARY', 'Secretary')
    ])
    submit = SubmitField('Add User')

    def validate_email(self, email):
        from models import User
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered. Please choose a different one.')

    def validate_username(self, username):
        from models import User
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')

class IncomeForm(FlaskForm):
    amount = FloatField('Amount', validators=[DataRequired()])
    source = StringField('Source', validators=[DataRequired()])
    description = TextAreaField('Description')
    submit = SubmitField('Save Income')

class ExpenseForm(FlaskForm):
    amount = FloatField('Amount', validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('MAINTENANCE', 'Maintenance'),
        ('UTILITIES', 'Utilities'),
        ('SUPPLIES', 'Supplies'),
        ('SALARY', 'Salary'),
        ('OTHER', 'Other')
    ])
    description = TextAreaField('Description')
    submit = SubmitField('Save Expense')

class StaffForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    position = StringField('Position', validators=[DataRequired()])
    department = StringField('Department', validators=[DataRequired()])
    salary_type = SelectField('Payment Type', choices=[
        ('FIXED', 'Fixed monthly salary'),
        ('HOURLY', 'Paid per hour'),
        ('MIXED', 'Fixed salary plus hourly teaching')
    ], default='FIXED')
    salary = FloatField('Salary (Monthly/Fixed)', validators=[Optional()])
    hourly_rate = FloatField('Hourly Rate (FCFA per hour)', default=0.0, validators=[Optional()])
    hours_per_week = IntegerField('Hours per Week', validators=[DataRequired(), NumberRange(min=0)])
    teaching_details = TextAreaField('Teaching Details', description='JSON format: [{"class": "Class1", "subject": "Math", "periods": 10}, ...]')
    email = StringField('Email')
    phone = StringField('Phone')
    academic_year = StringField('Academic Year', validators=[DataRequired()])
    submit = SubmitField('Add Staff')

    def validate_salary(self, salary):
        if self.salary_type.data in ['FIXED', 'MIXED']:
            if salary.data is None or salary.data < 0:
                raise ValidationError('Salary must be zero or a positive number for fixed or mixed payment types.')
        elif self.salary_type.data == 'HOURLY':
            if salary.data not in (None, 0.0, 0):
                raise ValidationError('Hourly paid staff should not have a fixed salary. Leave salary blank or set it to 0.')
            salary.data = 0.0

    def validate_hourly_rate(self, hourly_rate):
        if hourly_rate.data is None:
            hourly_rate.data = 0.0
        if hourly_rate.data < 0:
            raise ValidationError('Hourly rate must be zero or a positive number.')
        if self.salary_type.data == 'HOURLY' and hourly_rate.data <= 0:
            raise ValidationError('Hourly rate must be greater than 0 for hourly payment type.')
        if self.salary_type.data == 'MIXED':
            permanent_positions = {'PRINCIPAL', 'BURSER', 'ACCOUNTANT', 'SECRETARY'}
            position = (self.position.data or '').strip().upper()
            if position not in permanent_positions and hourly_rate.data <= 0:
                raise ValidationError('Hourly rate must be greater than 0 for mixed payment types unless the staff is Principal, Burser, Accountant, or Secretary.')

    def validate_email(self, email):
        if email.data:
            from models import Staff
            staff = Staff.query.filter_by(email=email.data).first()
            if staff and getattr(self, 'existing_email', None) != email.data:
                raise ValidationError('That email is already in use for another staff member.')

class PayrollForm(FlaskForm):
    month = SelectField('Month', choices=[(i, str(i)) for i in range(1, 13)], coerce=int, validators=[DataRequired()])
    year = StringField('Year', validators=[DataRequired()])
    period_rate = FloatField('Period Rate for Fixed Staff (FCFA)', validators=[DataRequired()])
    payroll_data = TextAreaField('Payroll Data', validators=[DataRequired()])
    submit = SubmitField('Create Payroll Expense')

class BudgetForm(FlaskForm):
    category = StringField('Category', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])
    month = SelectField('Month', choices=[(i, str(i)) for i in range(1, 13)], coerce=int)
    year = StringField('Year', validators=[DataRequired()])
    submit = SubmitField('Set Budget')
