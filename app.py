import os
from flask import Flask
from config import Config
from models import db, User
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from routes import register_routes

csrf = CSRFProtect()


def ensure_schema_columns(app):
    with app.app_context():
        conn = db.engine.connect()
        for table, column, column_type, default in [
            ('expense', 'status', 'VARCHAR(20)', "'PENDING'"),
            ('expense', 'approved_principal', 'INTEGER', '0'),
            ('expense', 'approved_burser', 'INTEGER', '0'),
            ('expense', 'approved_accountant', 'INTEGER', '0'),
            ('staff', 'academic_year', 'VARCHAR(20)', "''"),
            ('staff', 'department', 'VARCHAR(100)', "''"),
            ('staff', 'salary_type', 'VARCHAR(20)', "'FIXED'"),
            ('staff', 'salary', 'FLOAT', '0'),
            ('staff', 'hourly_rate', 'FLOAT', '0'),
            ('staff', 'hours_worked_month', 'FLOAT', '0'),
            ('staff', 'hours_per_week', 'INTEGER', '0'),
            ('staff', 'teaching_details', 'TEXT', "'[]'"),
            ('staff', 'pending_action', 'VARCHAR(20)', "'NONE'"),
            ('staff', 'pending_changes', 'TEXT', "''"),
            ('user', 'is_active', 'INTEGER', '1'),
            ('user', 'is_muted', 'INTEGER', '0')
        ]:
            result = conn.exec_driver_sql(f"PRAGMA table_info({table})")
            columns = [row[1] for row in result]
            if column not in columns:
                conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {column} {column_type} DEFAULT {default}")
        conn.close()


def ensure_default_staff(app):
    from models import Staff
    with app.app_context():
        default_entries = [
            {
                'name': 'School Principal',
                'position': 'Principal',
                'department': 'Administration',
                'salary_type': 'FIXED',
                'salary': 0.0,
                'hourly_rate': 0.0,
                'hours_worked_month': 0.0,
                'hours_per_week': 0,
                'teaching_details': '[]',
                'academic_year': '2024-2025'
            },
            {
                'name': 'School Burser',
                'position': 'Burser',
                'department': 'Finance',
                'salary_type': 'FIXED',
                'salary': 0.0,
                'hourly_rate': 0.0,
                'hours_worked_month': 0.0,
                'hours_per_week': 0,
                'teaching_details': '[]',
                'academic_year': '2024-2025'
            },
            {
                'name': 'School Accountant',
                'position': 'Accountant',
                'department': 'Finance',
                'salary_type': 'FIXED',
                'salary': 0.0,
                'hourly_rate': 0.0,
                'hours_worked_month': 0.0,
                'hours_per_week': 0,
                'teaching_details': '[]',
                'academic_year': '2024-2025'
            },
            {
                'name': 'School Secretary',
                'position': 'Secretary',
                'department': 'Administration',
                'salary_type': 'FIXED',
                'salary': 0.0,
                'hourly_rate': 0.0,
                'hours_worked_month': 0.0,
                'hours_per_week': 0,
                'teaching_details': '[]',
                'academic_year': '2024-2025'
            }
        ]
        for entry in default_entries:
            existing = Staff.query.filter_by(position=entry['position'], status='APPROVED').first()
            if not existing:
                staff = Staff(
                    name=entry['name'],
                    position=entry['position'],
                    department=entry['department'],
                    salary_type=entry['salary_type'],
                    salary=entry['salary'],
                    hourly_rate=entry['hourly_rate'],
                    hours_worked_month=entry['hours_worked_month'],
                    hours_per_week=entry['hours_per_week'],
                    teaching_details=entry['teaching_details'],
                    academic_year=entry['academic_year'],
                    status='APPROVED'
                )
                db.session.add(staff)
        db.session.commit()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    csrf.init_app(app)
    
    login_manager = LoginManager()
    login_manager.login_view = 'login'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    with app.app_context():
        db.create_all()
        ensure_schema_columns(app)
        ensure_default_staff(app)

        initial_admin_email = os.environ.get('INITIAL_ADMIN_EMAIL')
        initial_admin_password = os.environ.get('INITIAL_ADMIN_PASSWORD')
        flask_env = app.config.get('ENV', os.environ.get('FLASK_ENV', 'development')).lower()
        if flask_env != 'production':
            initial_admin_email = initial_admin_email or 'ankandjeu7@gmail.com'
            initial_admin_password = initial_admin_password or 'Admin123!'

        if initial_admin_email and initial_admin_password:
            existing_admin = User.query.filter_by(role='SUPER_ADMIN').first()
            if not existing_admin:
                super_admin = User(
                    username=os.environ.get('INITIAL_ADMIN_USERNAME', 'SUPER_ADMIN'),
                    email=initial_admin_email,
                    role='SUPER_ADMIN'
                )
                super_admin.set_password(initial_admin_password)
                db.session.add(super_admin)
                db.session.commit()
                if flask_env == 'production':
                    print('Created SUPER_ADMIN account from environment variables.')
                else:
                    print('Created local SUPER_ADMIN account:')
                    print(f'  Email: {initial_admin_email}')
                    print(f'  Password: {initial_admin_password}')
            elif flask_env != 'production':
                existing_admin.email = initial_admin_email
                existing_admin.username = os.environ.get('INITIAL_ADMIN_USERNAME', 'SUPER_ADMIN')
                existing_admin.set_password(initial_admin_password)
                db.session.commit()
                print('Reset local SUPER_ADMIN account:')
                print(f'  Email: {initial_admin_email}')
                print(f'  Password: {initial_admin_password}')

    register_routes(app)
    try:
        csrf.exempt(app.view_functions['login'])
        csrf.exempt(app.view_functions['logout'])
        csrf.exempt(app.view_functions['add_user'])
        csrf.exempt(app.view_functions['manage_users'])
        csrf.exempt(app.view_functions['edit_user'])
        csrf.exempt(app.view_functions['toggle_mute_user'])
        csrf.exempt(app.view_functions['toggle_active_user'])
        csrf.exempt(app.view_functions['delete_user'])
        csrf.exempt(app.view_functions['delete_all_users'])
        app.logger.info('CSRF exempted for user management routes')
    except Exception:
        pass
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=False)
