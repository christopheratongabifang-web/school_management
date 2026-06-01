from flask import Flask
<<<<<<< HEAD
import os
from config import Config
from models import db, User
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from routes import register_routes
from sqlalchemy import inspect, text

def ensure_schema_columns(app):
    """Ensure all required columns exist with proper PostgreSQL syntax"""
    with app.app_context():
        inspector = inspect(db.engine)
        
        # Define columns to check and add if missing
        columns_to_check = [
            ('expense', 'status', 'VARCHAR(20)', "'PENDING'"),
            ('expense', 'approved_principal', 'BOOLEAN', 'FALSE'),
            ('expense', 'approved_burser', 'BOOLEAN', 'FALSE'),
            ('expense', 'approved_accountant', 'BOOLEAN', 'FALSE'),
=======
from config import Config
from models import db, User
from flask_login import LoginManager
from routes import register_routes


def ensure_schema_columns(app):
    with app.app_context():
        conn = db.engine.connect()
        for table, column, column_type, default in [
            ('expense', 'status', 'VARCHAR(20)', "'PENDING'"),
            ('expense', 'approved_principal', 'INTEGER', '0'),
            ('expense', 'approved_burser', 'INTEGER', '0'),
            ('expense', 'approved_accountant', 'INTEGER', '0'),
>>>>>>> 833bb768ed7c6fccffd359ca260d50e7b6fd6f09
            ('staff', 'academic_year', 'VARCHAR(20)', "''"),
            ('staff', 'department', 'VARCHAR(100)', "''"),
            ('staff', 'salary_type', 'VARCHAR(20)', "'FIXED'"),
            ('staff', 'salary', 'FLOAT', '0'),
            ('staff', 'hourly_rate', 'FLOAT', '0'),
            ('staff', 'hours_worked_month', 'FLOAT', '0'),
            ('staff', 'hours_per_week', 'INTEGER', '0'),
            ('staff', 'teaching_details', 'TEXT', "'[]'"),
            ('staff', 'pending_action', 'VARCHAR(20)', "'NONE'"),
<<<<<<< HEAD
            ('staff', 'pending_changes', 'TEXT', "''"),
            ('income', 'student_name', 'VARCHAR(100)', "''"),
            ('income', 'student_class', 'VARCHAR(100)', "''"),
            ('income', 'section', 'VARCHAR(100)', "''"),
            ('income', 'pta_level', 'VARCHAR(100)', "''"),
            ('income', 'student_session', 'VARCHAR(100)', "''")
        ]
        
        for table, column, column_type, default in columns_to_check:
            try:
                # Check if table exists
                if table in inspector.get_table_names():
                    columns = [col['name'] for col in inspector.get_columns(table)]
                    if column not in columns:
                        # Use database-agnostic syntax (SQLite doesn't support IF NOT EXISTS in ALTER TABLE)
                        add_column_sql = text(f"ALTER TABLE {table} ADD COLUMN {column} {column_type} DEFAULT {default}")
                        db.session.execute(add_column_sql)
                        db.session.commit()
                        print(f"[SUCCESS] Added column {column} to table {table}")
            except Exception as e:
                print(f"[ERROR] Error adding column {column} to {table}: {e}")
                db.session.rollback()

def ensure_default_school_settings(app):
    """Initialize default school settings"""
    from models import SchoolSetting
    with app.app_context():
        defaults = {
            'fee_amount': '0',
            'pta_amount': '0',
            'sections': 'Anglophone,Francophone',
            'classes': '',
            'section_classes': 'Anglophone:\nFrancophone:'
        }
        for key, value in defaults.items():
            try:
                existing = SchoolSetting.query.filter_by(key=key).first()
                if not existing:
                    db.session.add(SchoolSetting(key=key, value=value))
            except Exception as e:
                print(f"[ERROR] Error adding setting {key}: {e}")
        db.session.commit()

def ensure_default_staff(app):
    """Initialize default staff entries"""
=======
            ('staff', 'pending_changes', 'TEXT', "''")
        ]:
            result = conn.exec_driver_sql(f"PRAGMA table_info({table})")
            columns = [row[1] for row in result]
            if column not in columns:
                conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {column} {column_type} DEFAULT {default}")
        conn.close()


def ensure_default_staff(app):
>>>>>>> 833bb768ed7c6fccffd359ca260d50e7b6fd6f09
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
<<<<<<< HEAD
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
    """Create admin user safely with proper error handling"""
    with app.app_context():
        try:
            admin_username = os.environ.get('INITIAL_ADMIN_USERNAME', 'ADMIN')
            admin_email = os.environ.get('INITIAL_ADMIN_EMAIL')
            admin_password = os.environ.get('INITIAL_ADMIN_PASSWORD')

            if app.config.get('ENV') != 'production':
                # In local development, create a default admin account if none exists.
                if not admin_email and not admin_password:
                    admin_email = 'admin@example.com'
                    admin_password = 'Admin123!'

            existing_admin = User.query.filter_by(role='SUPER_ADMIN').first()
            default_password = admin_password or 'Admin123!'
            default_email = admin_email or 'admin@example.com'

            if not existing_admin:
                if admin_email and admin_password:
                    super_admin = User(
                        username=admin_username,
                        email=admin_email,
                        role='SUPER_ADMIN'
                    )
                    super_admin.set_password(admin_password)
                    db.session.add(super_admin)
                    db.session.commit()
                elif app.config.get('ENV') != 'production':
                    super_admin = User(
                        username=admin_username,
                        email=default_email,
                        role='SUPER_ADMIN'
                    )
                    super_admin.set_password(default_password)
                    db.session.add(super_admin)
                    db.session.commit()
                    print('[SUCCESS] Created local SUPER_ADMIN account:', default_email)
                    print('[KEY] Use password:', default_password)
                else:
                    # No admin credentials available in production mode.
                    pass
            else:
                if app.config.get('ENV') != 'production':
                    if not admin_password:
                        existing_admin.set_password(default_password)
                        db.session.commit()
                        print('[SUCCESS] Reset local SUPER_ADMIN password for', existing_admin.email)
                        print('[KEY] New password:', default_password)
                    elif admin_password:
                        existing_admin.set_password(admin_password)
                        db.session.commit()
                        print('[SUCCESS] Updated SUPER_ADMIN password from env for', existing_admin.email)
        except Exception as e:
            print(f"[ERROR] Error creating admin user: {e}")
            db.session.rollback()
            
            try:
                inspector = inspect(db.engine)
                columns = [col['name'] for col in inspector.get_columns('user')]
                print(f"User table columns: {columns}")
                
                from sqlalchemy import text
                result = db.session.execute(text("SELECT column_name, data_type, character_maximum_length FROM information_schema.columns WHERE table_name = 'user' AND column_name = 'username'"))
                for row in result:
                    print(f"Username column info: {row}")
            except Exception as inspect_error:
                print(f"Could not inspect schema: {inspect_error}")

def fix_username_column(app):
    """Fix the username column if it has the wrong length (PostgreSQL only)"""
    with app.app_context():
        # Only run this query on PostgreSQL
        if 'postgresql' not in str(db.engine.url):
            print("[INFO] SQLite or non-PostgreSQL database detected; skipping username column fix.")
            return
            
        try:
            # Check current username column max length
            from sqlalchemy import text
            result = db.session.execute(text("""
                SELECT character_maximum_length 
                FROM information_schema.columns 
                WHERE table_name = 'user' AND column_name = 'username'
            """))
            
            current_length = result.fetchone()
            if current_length and current_length[0] != 64:
                print(f"[WARNING] Username column has length {current_length[0]}, fixing to 64...")
                # Alter the column to VARCHAR(64)
                db.session.execute(text('ALTER TABLE "user" ALTER COLUMN username TYPE VARCHAR(64);'))
                db.session.commit()
                print("[SUCCESS] Username column fixed!")
            else:
                print("[SUCCESS] Username column already has correct length")
        except Exception as e:
            print(f"[ERROR] Could not check/fix username column: {e}")
=======
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

>>>>>>> 833bb768ed7c6fccffd359ca260d50e7b6fd6f09

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
<<<<<<< HEAD
    # Ensure Flask's secret key is set on the app instance so sessions work
    # immediately (avoid RuntimeError about missing secret key).
    app.secret_key = app.config.get('SECRET_KEY')
    if app.config.get('ENV') == 'production' and app.secret_key in (None, '', 'change_this_dev_secret'):
        raise RuntimeError('SECRET_KEY must be set in environment for production deployment')
    
    CSRFProtect(app)
=======
    
>>>>>>> 833bb768ed7c6fccffd359ca260d50e7b6fd6f09
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.login_view = 'login'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    with app.app_context():
        db.create_all()
<<<<<<< HEAD
        fix_username_column(app)
        ensure_schema_columns(app)
        ensure_default_staff(app)
        ensure_default_school_settings(app)
        ensure_admin_user(app)

=======
        ensure_schema_columns(app)
        ensure_default_staff(app)
        
        # Seed Super Admin
        super_admin_email = 'ankandjeu7@gmail.com'
        if not User.query.filter_by(email=super_admin_email).first():
            super_admin = User(
                username='NKANDJEU WILLY',
                email=super_admin_email,
                role='SUPER_ADMIN'
            )
            super_admin.set_password('Willyarmel')
            db.session.add(super_admin)
            db.session.commit()
            print("Super Admin created successfully.")
            
>>>>>>> 833bb768ed7c6fccffd359ca260d50e7b6fd6f09
    register_routes(app)
    return app

app = create_app()

if __name__ == '__main__':
<<<<<<< HEAD
    app.run(debug=False)
=======
    app.run(debug=True)
>>>>>>> 833bb768ed7c6fccffd359ca260d50e7b6fd6f09
