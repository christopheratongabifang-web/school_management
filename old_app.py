import os
from flask import Flask
from config import Config
from models import db, User, Staff
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from routes import register_routes
from sqlalchemy import inspect, text

csrf = CSRFProtect()


def ensure_default_staff(app):
    from models import Staff
    with app.app_context():
        default_entries = [
            {'name': 'School Principal', 'position': 'Principal', 'department': 'Administration', 'salary_type': 'FIXED', 'salary': 0.0, 'hourly_rate': 0.0, 'hours_worked_month': 0.0, 'hours_per_week': 0, 'teaching_details': '[]', 'academic_year': '2024-2025'},
            {'name': 'School Burser', 'position': 'Burser', 'department': 'Finance', 'salary_type': 'FIXED', 'salary': 0.0, 'hourly_rate': 0.0, 'hours_worked_month': 0.0, 'hours_per_week': 0, 'teaching_details': '[]', 'academic_year': '2024-2025'},
            {'name': 'School Accountant', 'position': 'Accountant', 'department': 'Finance', 'salary_type': 'FIXED', 'salary': 0.0, 'hourly_rate': 0.0, 'hours_worked_month': 0.0, 'hours_per_week': 0, 'teaching_details': '[]', 'academic_year': '2024-2025'},
            {'name': 'School Secretary', 'position': 'Secretary', 'department': 'Administration', 'salary_type': 'FIXED', 'salary': 0.0, 'hourly_rate': 0.0, 'hours_worked_month': 0.0, 'hours_per_week': 0, 'teaching_details': '[]', 'academic_year': '2024-2025'},
        ]
        for entry in default_entries:
            try:
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
            except Exception as e:
                print(f"[ERROR] Error adding staff {entry['position']}: {e}")
        db.session.commit()


def ensure_admin_user(app):
    with app.app_context():
        try:
            admin_username = os.environ.get('INITIAL_ADMIN_USERNAME', 'ADMIN')
            admin_email = os.environ.get('INITIAL_ADMIN_EMAIL')
            admin_password = os.environ.get('INITIAL_ADMIN_PASSWORD')

            # PythonAnywhere environment detection
            is_production = app.config.get('ENV') == 'production' or os.environ.get('FLASK_ENV') == 'production'

            if not is_production:
                if not admin_email and not admin_password:
                    admin_email = 'ankandjeu7@gmail.com'
                    admin_password = 'Admin123!'

            existing_admin = User.query.filter_by(role='SUPER_ADMIN').first()
            default_password = admin_password or 'Admin123!'
            default_email = admin_email or 'admin@example.com'

            if not existing_admin:
                super_admin = User(username=admin_username, email=default_email, role='SUPER_ADMIN')
                super_admin.set_password(default_password)
                db.session.add(super_admin)
                db.session.commit()
                print('[SUCCESS] Created SUPER_ADMIN account:', default_email)
                print('[KEY] Use password:', default_password)
            else:
                if not is_production:
                    existing_admin.email = default_email
                    existing_admin.username = admin_username
                    existing_admin.set_password(default_password)
                    db.session.commit()
                    print('[SUCCESS] Reset local SUPER_ADMIN account to', default_email)
                    print('[KEY] Use password:', default_password)
        except Exception as e:
            print(f"[ERROR] Error creating admin user: {e}")
            try:
                db.session.rollback()
            except Exception:
                pass


def ensure_local_role_users(app):
    with app.app_context():
        is_production = app.config.get('ENV') == 'production' or os.environ.get('FLASK_ENV') == 'production'
        if is_production:
            return

        local_users = [
            ('Admin User', 'SUPER_ADMIN', 'admin@example.com', 'Admin123!'),
            ('Principal User', 'PRINCIPAL', 'principal@gmail.com', 'Principal123!'),
            ('Burser User', 'BURSER', 'burser@gmail.com', 'Burser123!'),
            ('Accountant User', 'ACCOUNTANT', 'accountant@gmail.com', 'Accountant123!'),
            ('Secretary User', 'SECRETARY', 'secretary@gmail.com', 'Secretary123!'),
        ]

        for username, role, email, password in local_users:
            existing_user = User.query.filter_by(role=role).first()
            if not existing_user:
                user = User(username=username, email=email, role=role)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                print(f'[SUCCESS] Created local {role} account: {email}')
                print(f'[KEY] Use password: {password}')
            else:
                existing_user.set_password(password)
                db.session.commit()
                print(f'[INFO] Reset local {role} password for: {existing_user.email}')


def ensure_income_columns(app):
    with app.app_context():
        inspector = inspect(db.engine)
        if 'income' not in inspector.get_table_names():
            return

        existing_columns = [col['name'] for col in inspector.get_columns('income')]
        required_columns = [
            ('student_name', 'TEXT', "''"),
            ('student_session', 'TEXT', "''"),
            ('student_class', 'TEXT', "''"),
            ('section', 'TEXT', "''"),
            ('pta_level', 'TEXT', "''")
        ]

        for column_name, column_type, default_value in required_columns:
            if column_name not in existing_columns:
                try:
                    db.session.execute(text(f'ALTER TABLE income ADD COLUMN {column_name} {column_type} DEFAULT {default_value}'))
                    db.session.commit()
                    print(f'[SUCCESS] Added income column {column_name}')
                except Exception as e:
                    print(f'[ERROR] Could not add income column {column_name}: {e}')
                    db.session.rollback()


def ensure_user_columns(app):
    with app.app_context():
        conn = db.engine.connect()
        result = conn.exec_driver_sql("PRAGMA table_info('user')")
        existing_columns = [row[1] for row in result]
        for column_name, column_type, default_value in [
            ('is_active', 'INTEGER', '1'),
            ('is_muted', 'INTEGER', '0')
        ]:
            if column_name not in existing_columns:
                try:
                    conn.exec_driver_sql(f"ALTER TABLE 'user' ADD COLUMN {column_name} {column_type} DEFAULT {default_value}")
                    print(f'[SUCCESS] Added user column {column_name}')
                except Exception as e:
                    print(f'[ERROR] Could not add user column {column_name}: {e}')
        conn.close()


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
        ensure_income_columns(app)
        ensure_user_columns(app)
        ensure_default_staff(app)
        ensure_admin_user(app)
        ensure_local_role_users(app)

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
    print('[INFO] SQLALCHEMY_DATABASE_URI =', app.config.get('SQLALCHEMY_DATABASE_URI'))
    return app


# This exposes the 'app' variable for PythonAnywhere's WSGI interface
app = create_app()

if __name__ == '__main__':
    # Used only for local development testing
    app.run(debug=True)