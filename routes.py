<<<<<<< HEAD
from flask import render_template, url_for, flash, redirect, request, send_file, session, abort, jsonify
import os
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy import or_, func
from models import db, User, Income, Expense, Staff, Budget, Payroll, SchoolSetting, SystemLog
from forms import LoginForm, UserForm, IncomeForm, ExpenseForm, StaffForm, BudgetForm, ResetPasswordForm, NewPasswordForm, PayrollForm, SchoolSettingsForm, ConfirmForm
=======
from flask import render_template, url_for, flash, redirect, request, send_file
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy import or_
from models import db, User, Income, Expense, Staff, Budget, Payroll
from forms import LoginForm, UserForm, IncomeForm, ExpenseForm, StaffForm, BudgetForm, ResetPasswordForm, NewPasswordForm, PayrollForm
>>>>>>> 833bb768ed7c6fccffd359ca260d50e7b6fd6f09
from datetime import datetime, timedelta
import pandas as pd
import io
import json

<<<<<<< HEAD
def get_school_setting(key, default=None):
    setting = SchoolSetting.query.filter_by(key=key).first()
    return setting.value if setting else default


def set_school_setting(key, value):
    setting = SchoolSetting.query.filter_by(key=key).first()
    if setting:
        setting.value = str(value)
    else:
        setting = SchoolSetting(key=key, value=str(value))
        db.session.add(setting)
    db.session.commit()


def parse_fee_schedule_rows(section_classes, sections, classes, fee_amount, pta_amount):
    rows = []
    section_classes = section_classes or ''
    for line in section_classes.splitlines():
        line = line.strip()
        if not line or ':' not in line:
            continue
        section_name, classes_str = line.split(':', 1)
        section_name = section_name.strip()
        class_names = [c.strip() for c in classes_str.split(',') if c.strip()]
        for class_name in class_names:
            rows.append({
                'section': section_name,
                'class': class_name,
                'fees': fee_amount,
                'pta': pta_amount
            })

    if not rows:
        class_items = [c.strip() for c in (classes or '').replace(',', '\n').splitlines() if c.strip()]
        section_items = [s.strip() for s in (sections or '').replace(',', '\n').splitlines() if s.strip()]
        if class_items:
            for class_name in class_items:
                rows.append({'section': '', 'class': class_name, 'fees': fee_amount, 'pta': pta_amount})
        elif section_items:
            for section_name in section_items:
                rows.append({'section': section_name, 'class': '', 'fees': fee_amount, 'pta': pta_amount})
    return rows


def group_fee_rows_by_section(section_classes, sections, classes, fee_amount, pta_amount):
    ordered_sections = [s.strip() for s in (sections or '').replace(',', '\n').splitlines() if s.strip()]
    section_map = {}
    for line in (section_classes or '').splitlines():
        line = line.strip()
        if not line:
            continue
        if ':' in line:
            section_name, classes_str = line.split(':', 1)
            section_name = section_name.strip()
            class_names = [c.strip() for c in classes_str.split(',') if c.strip()]
            section_map.setdefault(section_name, []).extend(class_names)
        else:
            section_name = line.strip()
            section_map.setdefault(section_name, [])

    global_classes = [c.strip() for c in (classes or '').replace(',', '\n').splitlines() if c.strip()]
    grouped = []
    used_sections = set()
    if ordered_sections:
        for section_name in ordered_sections:
            class_names = section_map.get(section_name)
            if class_names is None:
                class_names = []
            if not class_names and global_classes:
                class_names = global_classes
            grouped.append({
                'section': section_name,
                'rows': [{'class': class_name, 'fees': fee_amount, 'pta': pta_amount} for class_name in class_names]
            })
            used_sections.add(section_name)

    for section_name, class_names in section_map.items():
        if section_name in used_sections:
            continue
        if not class_names and global_classes:
            class_names = global_classes
        grouped.append({
            'section': section_name,
            'rows': [{'class': class_name, 'fees': fee_amount, 'pta': pta_amount} for class_name in class_names]
        })

    if not grouped and global_classes:
        class_names = [c.strip() for c in (classes or '').replace(',', '\n').splitlines() if c.strip()]
        grouped.append({'section': '', 'rows': [{'class': class_name, 'fees': fee_amount, 'pta': pta_amount} for class_name in class_names]})

    return grouped


def log_activity(user_id, action, module, details=None):
    """Log system activity"""
    log_entry = SystemLog(user_id=user_id, action=action, module=module, details=details)
    db.session.add(log_entry)
    db.session.commit()


def register_routes(app):
    @app.route('/set-section', methods=['POST'])
    @login_required
    def set_section():
        role = (current_user.role or '').upper()
        if role != 'SUPER_ADMIN':
            flash('Access Denied', 'danger')
            return redirect(url_for('dashboard'))

        section = request.form.get('section')
        school_sections = get_school_setting('sections', '') or ''
        available_sections = [s.strip() for s in school_sections.replace(',', '\n').splitlines() if s.strip()]
        if section not in available_sections:
            flash('Invalid section selection.', 'danger')
            return redirect(url_for('dashboard'))

        session['active_section'] = section
        flash(f'Active section changed to {section}.', 'info')
        return redirect(url_for('dashboard'))

=======
def register_routes(app):
>>>>>>> 833bb768ed7c6fccffd359ca260d50e7b6fd6f09
    @app.route('/')
    @app.route('/dashboard')
    @login_required
    def dashboard():
        # Summary metrics
        total_income = db.session.query(db.func.sum(Income.amount)).scalar() or 0
        total_expenses = db.session.query(db.func.sum(Expense.amount)).filter(Expense.status == 'APPROVED').scalar() or 0
        balance = total_income - total_expenses
        
        # Data for charts (last 6 months)
        labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
        income_data = [total_income * 0.1, total_income * 0.15, total_income * 0.2, total_income * 0.18, total_income * 0.22, total_income * 0.15]
        expense_data = [total_expenses * 0.12, total_expenses * 0.1, total_expenses * 0.15, total_expenses * 0.2, total_expenses * 0.18, total_expenses * 0.25]
        staff_members = Staff.query.filter_by(status='APPROVED').order_by(Staff.date_joined.desc()).all()
        role = (current_user.role or '').upper()
        show_payroll = request.args.get('show_payroll') == '1'
        payroll_form = PayrollForm()
        payroll_month = request.args.get('payroll_month', type=int) or datetime.utcnow().month
        payroll_year = request.args.get('payroll_year', type=int) or datetime.utcnow().year
        month_names = [None, 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
        payroll_record = None
        payroll_rows = []
        allow_edit_payroll = False
        if role in ['SECRETARY', 'SUPER_ADMIN', 'PRINCIPAL', 'ACCOUNTANT'] and show_payroll:
            payroll_record = Payroll.query.filter_by(month=payroll_month, year=payroll_year).order_by(Payroll.created_at.desc()).first()
            if payroll_record:
                payroll_rows = json.loads(payroll_record.staff_data or '[]')
            elif role == 'SECRETARY':
                allow_edit_payroll = True
                for staff in staff_members:
                    payroll_rows.append({
                        'id': staff.id,
                        'name': staff.name,
                        'position': staff.position,
                        'department': staff.department,
                        'salary_type': staff.salary_type,
                        'fixed_salary': staff.salary or 0.0,
                        'hourly_rate': staff.hourly_rate or 0.0,
                        'hours': 0,
                        'total_salary': 0.0
                    })
        if role == 'SECRETARY':
            payroll_form.month.data = payroll_month
            payroll_form.year.data = payroll_year
            payroll_form.period_rate.data = 0.0
        pending_staff = []
        if role in ['SUPER_ADMIN', 'PRINCIPAL']:
            pending_staff = Staff.query.filter(
                or_(Staff.status == 'PENDING', Staff.pending_action == 'EDIT')
            ).order_by(Staff.date_joined.desc()).all()
        pending_expenses = []
        approved_expenses = []
<<<<<<< HEAD
        confirm_form = ConfirmForm()
=======
>>>>>>> 833bb768ed7c6fccffd359ca260d50e7b6fd6f09
        if role in ['PRINCIPAL', 'BURSER', 'ACCOUNTANT']:
            pending_expenses = Expense.query.filter_by(status='PENDING').order_by(Expense.date.desc()).all()
        if role in ['SUPER_ADMIN', 'PRINCIPAL', 'BURSER', 'ACCOUNTANT']:
            approved_expenses = Expense.query.filter_by(status='APPROVED').order_by(Expense.date.desc()).all()
<<<<<<< HEAD

        school_fee_amount = float(get_school_setting('fee_amount', '0') or 0)
        school_pta_amount = float(get_school_setting('pta_amount', '0') or 0)
        school_sections = get_school_setting('sections', '')
        school_classes = get_school_setting('classes', '')
        school_section_classes = get_school_setting('section_classes', '')

        available_sections = [s.strip() for s in school_sections.replace(',', '\n').splitlines() if s.strip()]
        active_section = session.get('active_section', available_sections[0] if available_sections else None) if role == 'SUPER_ADMIN' else None

=======
>>>>>>> 833bb768ed7c6fccffd359ca260d50e7b6fd6f09
        return render_template('dashboard.html', 
                             total_income=total_income, 
                             total_expenses=total_expenses, 
                             balance=balance,
                             labels=labels,
                             income_data=income_data,
                             expense_data=expense_data,
                             staff_members=staff_members,
                             staff_count=len(staff_members),
                             pending_staff=pending_staff,
                             pending_expenses=pending_expenses,
                             approved_expenses=approved_expenses,
                             show_payroll=show_payroll,
                             payroll_form=payroll_form,
                             payroll_month=payroll_month,
                             payroll_year=payroll_year,
                             month_names=month_names,
                             payroll_record=payroll_record,
                             payroll_rows=payroll_rows,
<<<<<<< HEAD
                             allow_edit_payroll=allow_edit_payroll,
                             school_fee_amount=school_fee_amount,
                             school_pta_amount=school_pta_amount,
                             school_sections=school_sections,
                             school_classes=school_classes,
                             school_section_classes=school_section_classes,
                             available_sections=available_sections,
                             active_section=active_section,
                             confirm_form=confirm_form)
=======
                             allow_edit_payroll=allow_edit_payroll)
>>>>>>> 833bb768ed7c6fccffd359ca260d50e7b6fd6f09

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        form = LoginForm()
        if form.validate_on_submit():
<<<<<<< HEAD
            identifier = (form.email.data or '').strip().lower()
            user = User.query.filter(
                or_(func.lower(User.email) == identifier,
                    func.lower(User.username) == identifier)
            ).first()
            success = False
            try:
                if user and user.check_password(form.password.data):
                    success = True
            except Exception:
                # If password check itself raises, treat as failure but log it
                success = False

            if success:
                login_user(user)
                log_activity(user.id, 'LOGIN', 'AUTH', f'User {user.username} logged in')
                return redirect(url_for('dashboard'))
            else:
                # Log debug info to file (no plaintext passwords)
                try:
                    log_path = app.instance_path if hasattr(app, 'instance_path') else 'instance'
                    log_file = os.path.join(log_path, 'login_debug.log')
                    os.makedirs(os.path.dirname(log_file), exist_ok=True)
                    with open(log_file, 'a', encoding='utf-8') as f:
                        f.write(f"{datetime.utcnow().isoformat()} - login failed - identifier={identifier} - user_found={bool(user)}\n")
                except Exception:
                    pass
                flash('Login Unsuccessful. Please check email and password', 'danger')
        elif request.method == 'POST':
            # Form failed CSRF or validation - show specific field errors for debugging
            errors = []
            for field, errs in form.errors.items():
                for e in errs:
                    errors.append(f"{field}: {e}")
            if errors:
                for msg in errors:
                    flash(msg, 'danger')
        return render_template('login.html', title='Login', form=form)

    @app.route('/__dev/admin_status')
    def dev_admin_status():
        if app.config.get('ENV') == 'production':
            abort(404)

        email = (request.args.get('email') or 'ankandjeu7@gmail.com').strip().lower()
        user = User.query.filter(func.lower(User.email) == email).first()
        return jsonify({
            'db_uri': app.config.get('SQLALCHEMY_DATABASE_URI'),
            'email': email,
            'user_found': bool(user),
            'username': user.username if user else None,
            'role': user.role if user else None,
        })

    @app.route('/__dev/reset_admin', methods=['GET', 'POST'])
    def dev_reset_admin():
        """Development-only: reset an existing user's password.

        Use only when `ENV` != 'production'. If `DEV_RESET_TOKEN` is set in the
        environment, the same token must be provided in the `token` form field,
        query string, or `X-DEV-TOKEN` header. Accepts `email` and `password`
        via form or query string.
        """
        if app.config.get('ENV') == 'production':
            abort(404)

        required_token = os.environ.get('DEV_RESET_TOKEN')
        provided = (request.form.get('token') or request.args.get('token') or request.headers.get('X-DEV-TOKEN'))
        if required_token and provided != required_token:
            return ('Unauthorized', 403)

        email = (request.values.get('email') or '').strip().lower()
        password = request.values.get('password')
        if not email or not password:
            return ('email and password required', 400)

        user = User.query.filter(func.lower(User.email) == email).first()
        if not user:
            return ('user not found', 404)

        user.set_password(password)
        db.session.commit()
        return ('ok', 200)

    @app.route('/logout', methods=['POST'])
    @login_required
=======
            user = User.query.filter_by(email=form.email.data).first()
            if user and user.check_password(form.password.data):
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                flash('Login Unsuccessful. Please check email and password', 'danger')
        return render_template('login.html', title='Login', form=form)

    @app.route('/logout')
>>>>>>> 833bb768ed7c6fccffd359ca260d50e7b6fd6f09
    def logout():
        logout_user()
        return redirect(url_for('login'))

    @app.route('/reset_password', methods=['GET', 'POST'])
    def reset_password():
        form = ResetPasswordForm()
        if form.validate_on_submit():
            flash('An email has been sent with instructions to reset your password.', 'info')
            return redirect(url_for('login'))
        return render_template('reset_password.html', title='Reset Password', form=form)

    # User Management (Super Admin only)
    @app.route('/users/add', methods=['GET', 'POST'])
    @login_required
    def add_user():
        if current_user.role != 'SUPER_ADMIN':
            flash('Access Denied', 'danger')
            return redirect(url_for('dashboard'))
        form = UserForm()
        if form.validate_on_submit():
<<<<<<< HEAD
            user = User(username=form.username.data.strip(), email=form.email.data.strip().lower(), role=form.role.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            log_activity(current_user.id, 'CREATE_USER', 'USER_MGMT', f'Created user {user.username} with role {user.role}')
=======
            user = User(username=form.username.data, email=form.email.data, role=form.role.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
>>>>>>> 833bb768ed7c6fccffd359ca260d50e7b6fd6f09
            flash(f'User {user.username} added successfully!', 'success')
            return redirect(url_for('dashboard'))
        return render_template('add_user.html', form=form)

    # Income Management
    @app.route('/income/add', methods=['GET', 'POST'])
    @login_required
    def add_income():
        role = (current_user.role or '').upper()
        if role != 'BURSER':
            flash('Access Denied', 'danger')
            return redirect(url_for('dashboard'))
<<<<<<< HEAD

        form = IncomeForm()
        
        # Parse available sessions
        raw_sections = get_school_setting('sections', 'Anglophone,Francophone') or ''
        parsed_sessions = [s.strip() for s in raw_sections.replace(',', '\n').splitlines() if s.strip()]
        if parsed_sessions:
            form.student_session.choices = [(session, session) for session in parsed_sessions]
        
        # Parse classes by section for dynamic filtering
        section_classes_raw = get_school_setting('section_classes', 'Anglophone:\nFrancophone:') or ''
        session_classes_map = {}
        for line in section_classes_raw.split('\n'):
            if ':' in line:
                session_name, classes_str = line.split(':', 1)
                session_name = session_name.strip()
                classes = [c.strip() for c in classes_str.split(',') if c.strip()]
                session_classes_map[session_name] = classes

        default_fee_amount = float(get_school_setting('fee_amount', '0') or 0)
        default_pta_amount = float(get_school_setting('pta_amount', '0') or 0)
        
        if request.method == 'GET':
            if form.source.data == 'FEES':
                form.amount.data = default_fee_amount
            else:
                form.amount.data = default_pta_amount

        if form.validate_on_submit():
            income = Income(
                amount=form.amount.data,
                source=form.source.data,
                student_name=form.student_name.data,
                student_session=form.student_session.data,
                student_class=form.student_class.data,
                section=form.section.data,
                pta_level=form.pta_level.data,
                description=form.description.data,
                added_by=current_user.id
            )
            db.session.add(income)
            db.session.commit()
            log_activity(current_user.id, 'ADD_INCOME', 'FINANCE', f'{form.source.data} - {form.amount.data} FCFA from {form.student_name.data or "Unknown"} ({form.student_session.data or form.student_class.data or form.pta_level.data or "Unknown"})')
            flash('Income added!', 'success')
            return redirect(url_for('view_income'))
        
        return render_template('income/add_income.html', form=form, default_fee_amount=default_fee_amount, 
                             default_pta_amount=default_pta_amount, session_classes_map=session_classes_map,
                             parsed_sessions=parsed_sessions)

    @app.route('/settings/school', methods=['GET', 'POST'])
    @login_required
    def school_settings():
        if current_user.role != 'SUPER_ADMIN':
            flash('Access Denied', 'danger')
            return redirect(url_for('dashboard'))

        form = SchoolSettingsForm()
        if request.method == 'GET':
            form.fees_amount.data = float(get_school_setting('fee_amount', '0') or 0)
            form.pta_amount.data = float(get_school_setting('pta_amount', '0') or 0)
            form.sections.data = get_school_setting('sections', 'Anglophone,Francophone').replace(',', '\n')
            form.classes.data = get_school_setting('classes', '').replace(',', '\n')
            form.section_classes.data = get_school_setting('section_classes', 'Anglophone:\nFrancophone:')

        if form.validate_on_submit():
            set_school_setting('fee_amount', form.fees_amount.data)
            set_school_setting('pta_amount', form.pta_amount.data)
            set_school_setting('sections', '\n'.join([line.strip() for line in form.sections.data.splitlines() if line.strip()]))
            set_school_setting('classes', '\n'.join([line.strip() for line in form.classes.data.splitlines() if line.strip()]))
            set_school_setting('section_classes', form.section_classes.data.strip())
            log_activity(current_user.id, 'UPDATE_SETTINGS', 'ADMIN', f'Updated school settings - Fees: {form.fees_amount.data}, PTA: {form.pta_amount.data}')
            flash('School settings updated successfully.', 'success')
            return redirect(url_for('school_settings'))

        fee_table_rows = parse_fee_schedule_rows(
            form.section_classes.data,
            form.sections.data,
            form.classes.data,
            form.fees_amount.data or 0,
            form.pta_amount.data or 0
        )
        return render_template('school_settings.html', form=form, fee_table_rows=fee_table_rows)

    @app.route('/school/fees')
    @login_required
    def school_fees():
        if current_user.role != 'SUPER_ADMIN':
            flash('Access Denied', 'danger')
            return redirect(url_for('dashboard'))

        school_fee_amount = float(get_school_setting('fee_amount', '0') or 0)
        school_pta_amount = float(get_school_setting('pta_amount', '0') or 0)
        school_sections = get_school_setting('sections', '')
        school_classes = get_school_setting('classes', '')
        school_section_classes = get_school_setting('section_classes', '')
        school_fee_groups = group_fee_rows_by_section(school_section_classes, school_sections, school_classes, school_fee_amount, school_pta_amount)

        return render_template('school_fees.html', school_fee_groups=school_fee_groups)
=======
        form = IncomeForm()
        if form.validate_on_submit():
            income = Income(amount=form.amount.data, source=form.source.data, 
                           description=form.description.data, added_by=current_user.id)
            db.session.add(income)
            db.session.commit()
            flash('Income added!', 'success')
            return redirect(url_for('view_income'))
        return render_template('income/add_income.html', form=form)
>>>>>>> 833bb768ed7c6fccffd359ca260d50e7b6fd6f09

    @app.route('/income/view')
    @login_required
    def view_income():
        role = (current_user.role or '').upper()
<<<<<<< HEAD
        if role not in ['SUPER_ADMIN', 'PRINCIPAL', 'BURSER', 'ACCOUNTANT']:
            flash('Access Denied', 'danger')
            return redirect(url_for('dashboard'))
        
        try:
            # Get current year for display
            current_year = datetime.utcnow().year
            
            # Query all incomes
            incomes = Income.query.order_by(Income.date.desc()).all()
            
            return render_template('income/view_income.html', incomes=incomes, year=current_year)
        except Exception as e:
            flash(f'Error loading income records: {str(e)}', 'danger')
            return redirect(url_for('dashboard'))

    @app.route('/income/edit/<int:income_id>', methods=['GET', 'POST'])
    @login_required
    def edit_income(income_id):
        role = (current_user.role or '').upper()
        if role != 'BURSER':
            flash('Access Denied', 'danger')
            return redirect(url_for('dashboard'))

        income = Income.query.get_or_404(income_id)
        form = IncomeForm(obj=income)

        raw_sections = get_school_setting('sections', 'Anglophone,Francophone') or ''
        parsed_sessions = [s.strip() for s in raw_sections.replace(',', '\n').splitlines() if s.strip()]
        if parsed_sessions:
            form.student_session.choices = [(session, session) for session in parsed_sessions]

        if form.validate_on_submit():
            income.amount = form.amount.data
            income.source = form.source.data
            income.student_name = form.student_name.data
            income.student_session = form.student_session.data
            income.student_class = form.student_class.data
            income.section = form.section.data
            income.pta_level = form.pta_level.data
            income.description = form.description.data
            db.session.commit()
            log_activity(current_user.id, 'EDIT_INCOME', 'FINANCE', f'Updated income ID {income_id} for {income.student_name or "Unknown"} - {income.amount} FCFA')
            flash('Income record updated successfully.', 'success')
            return redirect(url_for('view_income'))

        return render_template('income/edit_income.html', form=form, income=income)
=======
        if role not in ['SUPER_ADMIN', 'PRINCIPAL', 'BURSER']:
            flash('Access Denied', 'danger')
            return redirect(url_for('dashboard'))
        incomes = Income.query.order_by(Income.date.desc()).all()
        return render_template('income/view_income.html', incomes=incomes)
>>>>>>> 833bb768ed7c6fccffd359ca260d50e7b6fd6f09

    # Expense Management
    @app.route('/expenses/add', methods=['GET', 'POST'])
    @login_required
    def add_expense():
        role = (current_user.role or '').upper()
        if role not in ['PRINCIPAL', 'BURSER', 'ACCOUNTANT']:
            flash('Access Denied', 'danger')
            return redirect(url_for('dashboard'))
        form = ExpenseForm()
        if form.validate_on_submit():
            expense = Expense(
                amount=form.amount.data,
                category=form.category.data,
                description=form.description.data,
                added_by=current_user.id,
                status='PENDING',
                approved_principal=(role == 'PRINCIPAL'),
                approved_burser=(role == 'BURSER'),
                approved_accountant=(role == 'ACCOUNTANT')
            )
            db.session.add(expense)
            db.session.commit()
<<<<<<< HEAD
            log_activity(current_user.id, 'ADD_EXPENSE', 'FINANCE', f'{form.category.data} - {form.amount.data} FCFA')
=======
>>>>>>> 833bb768ed7c6fccffd359ca260d50e7b6fd6f09
            flash('Expense submitted and waiting for final approval.', 'info')
            return redirect(url_for('view_expenses'))
        return render_template('expenses/add_expense.html', form=form)

    @app.route('/expenses/payroll', methods=['GET', 'POST'])
    @login_required
    def add_payroll_expense():
        role = (current_user.role or '').upper()
        if role != 'SECRETARY':
            flash('Access Denied', 'danger')
            return redirect(url_for('dashboard'))
        staff_members = Staff.query.filter_by(status='APPROVED').order_by(Staff.name).all()
        form = PayrollForm()
        if form.validate_on_submit():
            payroll_items = json.loads(form.payroll_data.data or '[]')
            if not payroll_items:
                flash('Please provide payroll details for at least one staff member.', 'danger')
                return render_template('expenses/payroll.html', form=form, staff_members=staff_members)
            total_amount = 0.0
            record_items = []
            description_lines = [f'Payroll for {form.month.data}/{form.year.data}']
            for item in payroll_items:
                staff = Staff.query.get(item.get('id'))
                if not staff:
                    continue
                hours = float(item.get('hours') or 0)
                if staff.salary_type == 'HOURLY':
                    subtotal = (staff.hourly_rate or 0.0) * hours
                    description_lines.append(f'{staff.name}: Hourly {staff.hourly_rate:.0f} x {hours:.0f} = {subtotal:.0f}')
                elif staff.salary_type == 'MIXED':
                    subtotal = (staff.salary or 0.0) + (staff.hourly_rate or 0.0) * hours
                    description_lines.append(f'{staff.name}: Fixed {staff.salary:.0f} + Hourly {staff.hourly_rate:.0f} x {hours:.0f} = {subtotal:.0f}')
                else:
                    subtotal = (staff.salary or 0.0) + (form.period_rate.data or 0.0) * hours
                    description_lines.append(f'{staff.name}: Fixed {staff.salary:.0f} + Hours {hours:.0f} x {form.period_rate.data:.0f} = {subtotal:.0f}')
                total_amount += subtotal
                record_items.append({
                    'id': staff.id,
                    'name': staff.name,
                    'position': staff.position,
                    'department': staff.department,
                    'salary_type': staff.salary_type,
                    'fixed_salary': staff.salary or 0.0,
                    'hourly_rate': staff.hourly_rate or 0.0,
                    'hours': hours,
                    'total_salary': subtotal
                })
            expense = Expense(
                amount=total_amount,
                category='SALARY',
                description='\n'.join(description_lines),
                added_by=current_user.id,
                status='PENDING',
                approved_principal=False,
                approved_burser=False,
                approved_accountant=False
            )
            db.session.add(expense)
            payroll_record = Payroll(
                month=form.month.data,
                year=form.year.data,
                total_amount=total_amount,
                staff_data=json.dumps(record_items),
                created_by=current_user.id
            )
            db.session.add(payroll_record)
            db.session.commit()
            flash('Payroll expense created and sent for approval.', 'success')
            return redirect(url_for('view_expenses'))
        return render_template('expenses/payroll.html', form=form, staff_members=staff_members)

    @app.route('/expenses/view')
    @login_required
    def view_expenses():
        role = (current_user.role or '').upper()
        if role not in ['SUPER_ADMIN', 'PRINCIPAL', 'BURSER', 'ACCOUNTANT', 'SECRETARY']:
            flash('Access Denied', 'danger')
            return redirect(url_for('dashboard'))
        expenses = Expense.query.filter(Expense.status != 'REJECTED').order_by(Expense.date.desc()).all()
<<<<<<< HEAD
        confirm_form = ConfirmForm()
        return render_template('expenses/view_expenses.html', expenses=expenses, confirm_form=confirm_form)

    @app.route('/expenses/approve/<int:expense_id>', methods=['POST'])
    @login_required
    def approve_expense(expense_id):
        form = ConfirmForm()
        if not form.validate_on_submit():
            flash('Invalid request.', 'danger')
            return redirect(url_for('view_expenses'))

=======
        return render_template('expenses/view_expenses.html', expenses=expenses)

    @app.route('/expenses/approve/<int:expense_id>')
    @login_required
    def approve_expense(expense_id):
>>>>>>> 833bb768ed7c6fccffd359ca260d50e7b6fd6f09
        role = (current_user.role or '').upper()
        if role not in ['PRINCIPAL', 'BURSER', 'ACCOUNTANT']:
            flash('Access Denied', 'danger')
            return redirect(url_for('dashboard'))
        expense = Expense.query.get_or_404(expense_id)
        if expense.status != 'PENDING':
            flash('This expense cannot be approved.', 'warning')
            return redirect(url_for('view_expenses'))
        if role == 'PRINCIPAL':
            expense.approved_principal = True
        elif role == 'BURSER':
            expense.approved_burser = True
        else:
            expense.approved_accountant = True
        if expense.approved_principal and expense.approved_burser and expense.approved_accountant:
            expense.status = 'APPROVED'
<<<<<<< HEAD
            log_activity(current_user.id, 'APPROVE_EXPENSE', 'FINANCE', f'Expense ID {expense_id} ({expense.category}) - {expense.amount} FCFA FULLY APPROVED')
            flash('Expense is now fully approved and will be recorded.', 'success')
        else:
            log_activity(current_user.id, 'APPROVE_EXPENSE', 'FINANCE', f'Expense ID {expense_id} ({expense.category}) - {expense.amount} FCFA approved by {role}')
=======
            flash('Expense is now fully approved and will be recorded.', 'success')
        else:
>>>>>>> 833bb768ed7c6fccffd359ca260d50e7b6fd6f09
            flash('Your approval has been recorded. Waiting for other approvers.', 'info')
        db.session.commit()
        return redirect(url_for('view_expenses'))

<<<<<<< HEAD
    @app.route('/expenses/reject/<int:expense_id>', methods=['POST'])
    @login_required
    def reject_expense(expense_id):
        form = ConfirmForm()
        if not form.validate_on_submit():
            flash('Invalid request.', 'danger')
            return redirect(url_for('view_expenses'))

=======
    @app.route('/expenses/reject/<int:expense_id>')
    @login_required
    def reject_expense(expense_id):
>>>>>>> 833bb768ed7c6fccffd359ca260d50e7b6fd6f09
        role = (current_user.role or '').upper()
        if role not in ['PRINCIPAL', 'BURSER', 'ACCOUNTANT']:
            flash('Access Denied', 'danger')
            return redirect(url_for('dashboard'))
        expense = Expense.query.get_or_404(expense_id)
        if expense.status != 'PENDING':
            flash('This expense cannot be rejected.', 'warning')
            return redirect(url_for('view_expenses'))
        expense.status = 'REJECTED'
        db.session.commit()
<<<<<<< HEAD
        log_activity(current_user.id, 'REJECT_EXPENSE', 'FINANCE', f'Expense ID {expense_id} ({expense.category}) - {expense.amount} FCFA rejected')
=======
>>>>>>> 833bb768ed7c6fccffd359ca260d50e7b6fd6f09
        flash('Expense has been rejected and will not be spent.', 'warning')
        return redirect(url_for('view_expenses'))

    # Staff Management
    @app.route('/staff/add', methods=['GET', 'POST'])
    @login_required
    def add_staff():
        role = (current_user.role or '').upper()
        if role not in ['PRINCIPAL', 'SECRETARY']:
            flash('Access Denied', 'danger')
            return redirect(url_for('dashboard'))
        form = StaffForm()
        if form.validate_on_submit():
            status = 'PENDING' if role == 'SECRETARY' else 'APPROVED'
            pending_action = 'ADD' if role == 'SECRETARY' else 'NONE'
            staff = Staff(
                name=form.name.data,
                position=form.position.data,
                department=form.department.data,
                salary_type=form.salary_type.data,
                salary=0.0 if form.salary_type.data == 'HOURLY' else (form.salary.data or 0.0),
                hourly_rate=form.hourly_rate.data,
                hours_per_week=form.hours_per_week.data,
                teaching_details=form.teaching_details.data or '[]',
                email=form.email.data,
                phone=form.phone.data,
                academic_year=form.academic_year.data,
                status=status,
                pending_action=pending_action,
                added_by=current_user.id
            )
            db.session.add(staff)
            db.session.commit()
            if status == 'PENDING':
                flash('Staff request sent to Principal for validation.', 'info')
                return redirect(url_for('view_staff'))
            flash('Successfully added staff member!', 'success')
            return redirect(url_for('view_staff'))
        return render_template('staff/add_staff.html', form=form)

    @app.route('/staff/edit/<int:staff_id>', methods=['GET', 'POST'])
    @login_required
    def edit_staff(staff_id):
        role = (current_user.role or '').upper()
        if role not in ['PRINCIPAL', 'SECRETARY']:
            flash('Access Denied', 'danger')
            return redirect(url_for('dashboard'))
        staff = Staff.query.get_or_404(staff_id)
        form = StaffForm(obj=staff)
        form.existing_email = staff.email
        if form.validate_on_submit():
            if role == 'PRINCIPAL':
                staff.name = form.name.data
                staff.position = form.position.data
                staff.department = form.department.data
                staff.salary_type = form.salary_type.data
                staff.salary = 0.0 if form.salary_type.data == 'HOURLY' else (form.salary.data or 0.0)
                staff.hourly_rate = form.hourly_rate.data
                staff.hours_per_week = form.hours_per_week.data
                staff.teaching_details = form.teaching_details.data or '[]'
                staff.email = form.email.data
                staff.phone = form.phone.data
                staff.academic_year = form.academic_year.data
                staff.status = 'APPROVED'
                staff.pending_action = 'NONE'
                staff.pending_changes = None
                db.session.commit()
                flash('Staff information updated successfully.', 'success')
                return redirect(url_for('view_staff'))
            # Secretary edits create a pending change request for approved staff, or update the pending add request
            if staff.status == 'PENDING' and staff.pending_action == 'ADD':
                staff.name = form.name.data
                staff.position = form.position.data
                staff.department = form.department.data
                staff.salary_type = form.salary_type.data
                staff.salary = 0.0 if form.salary_type.data == 'HOURLY' else (form.salary.data or 0.0)
                staff.hourly_rate = form.hourly_rate.data
                staff.hours_per_week = form.hours_per_week.data
                staff.teaching_details = form.teaching_details.data or '[]'
                staff.email = form.email.data
                staff.phone = form.phone.data
                staff.academic_year = form.academic_year.data
                db.session.commit()
                flash('Pending staff request updated.', 'info')
                return redirect(url_for('view_staff'))
            requested_changes = {}
            for field_name in [
                'name', 'position', 'department', 'salary_type', 'salary',
                'hourly_rate', 'hours_per_week',
                'teaching_details', 'email', 'phone', 'academic_year'
            ]:
                current_value = getattr(staff, field_name)
                new_value = getattr(form, field_name).data
                if current_value != new_value:
                    requested_changes[field_name] = new_value
            if requested_changes:
                staff.pending_action = 'EDIT'
                staff.pending_changes = json.dumps(requested_changes)
                db.session.commit()
                flash('Your update request has been submitted to the Principal for approval.', 'info')
            else:
                flash('No changes were detected.', 'info')
            return redirect(url_for('view_staff'))
        # Prepopulate form with pending edit data if the secretary is viewing an existing edit request
        if request.method == 'GET' and staff.pending_action == 'EDIT' and staff.pending_changes:
            pending = json.loads(staff.pending_changes)
            for key, value in pending.items():
                if hasattr(form, key):
                    getattr(form, key).data = value
        return render_template('staff/edit_staff.html', form=form, staff=staff, role=role)

    @app.route('/staff/view')
    @login_required
    def view_staff():
        # All admin users can see approved staff
        staff_members = Staff.query.filter_by(status='APPROVED').order_by(Staff.date_joined.desc()).all()
        pending_staff = []
        role = (current_user.role or '').upper()
        if role in ['SUPER_ADMIN', 'PRINCIPAL']:
            pending_staff = Staff.query.filter(
                or_(Staff.status == 'PENDING', Staff.pending_action == 'EDIT')
            ).order_by(Staff.date_joined.desc()).all()
        elif role == 'SECRETARY':
            pending_staff = Staff.query.filter(
                Staff.added_by == current_user.id,
                or_(Staff.status == 'PENDING', Staff.pending_action == 'EDIT')
            ).order_by(Staff.date_joined.desc()).all()
<<<<<<< HEAD
        confirm_form = ConfirmForm()
        return render_template('staff/view_staff.html', 
                             staff_members=staff_members, 
                             pending_staff=pending_staff,
                             confirm_form=confirm_form)

    @app.route('/staff/approve/<int:staff_id>', methods=['POST'])
    @login_required
    def approve_staff(staff_id):
        form = ConfirmForm()
        if not form.validate_on_submit():
            flash('Invalid request.', 'danger')
            return redirect(url_for('view_staff'))

=======
        return render_template('staff/view_staff.html', 
                             staff_members=staff_members, 
                             pending_staff=pending_staff)

    @app.route('/staff/approve/<int:staff_id>')
    @login_required
    def approve_staff(staff_id):
>>>>>>> 833bb768ed7c6fccffd359ca260d50e7b6fd6f09
        role = (current_user.role or '').upper()
        if role not in ['SUPER_ADMIN', 'PRINCIPAL']:
            flash('Access Denied', 'danger')
            return redirect(url_for('dashboard'))
        staff = Staff.query.get_or_404(staff_id)
        if staff.pending_action == 'EDIT' and staff.pending_changes:
            changes = json.loads(staff.pending_changes)
            for key, value in changes.items():
                setattr(staff, key, value)
        staff.pending_action = 'NONE'
        staff.pending_changes = None
        if staff.status == 'PENDING':
            staff.status = 'APPROVED'
        db.session.commit()
<<<<<<< HEAD
        log_activity(current_user.id, 'APPROVE_STAFF', 'STAFF', f'Staff member {staff.name} ({staff.position}) approved')
        flash(f'Staff member {staff.name} has been approved.', 'success')
        return redirect(url_for('dashboard'))

    @app.route('/staff/reject/<int:staff_id>', methods=['POST'])
    @login_required
    def reject_staff(staff_id):
        form = ConfirmForm()
        if not form.validate_on_submit():
            flash('Invalid request.', 'danger')
            return redirect(url_for('view_staff'))

=======
        flash(f'Staff member {staff.name} has been approved.', 'success')
        return redirect(url_for('dashboard'))

    @app.route('/staff/reject/<int:staff_id>')
    @login_required
    def reject_staff(staff_id):
>>>>>>> 833bb768ed7c6fccffd359ca260d50e7b6fd6f09
        role = (current_user.role or '').upper()
        if role not in ['SUPER_ADMIN', 'PRINCIPAL']:
            flash('Access Denied', 'danger')
            return redirect(url_for('dashboard'))
        staff = Staff.query.get_or_404(staff_id)
        if staff.pending_action == 'EDIT':
            staff.pending_action = 'NONE'
            staff.pending_changes = None
            db.session.commit()
<<<<<<< HEAD
            log_activity(current_user.id, 'REJECT_STAFF', 'STAFF', f'Pending changes for {staff.name} rejected')
=======
>>>>>>> 833bb768ed7c6fccffd359ca260d50e7b6fd6f09
            flash(f'Pending changes for {staff.name} have been rejected.', 'warning')
            return redirect(url_for('dashboard'))
        if staff.status == 'PENDING':
            db.session.delete(staff)
            db.session.commit()
<<<<<<< HEAD
            log_activity(current_user.id, 'REJECT_STAFF', 'STAFF', f'Staff member {staff.name} ({staff.position}) rejected and removed')
=======
>>>>>>> 833bb768ed7c6fccffd359ca260d50e7b6fd6f09
            flash(f'Staff member {staff.name} has been rejected and removed.', 'warning')
            return redirect(url_for('dashboard'))
        flash('This staff request cannot be rejected.', 'warning')
        return redirect(url_for('dashboard'))

    # Reporting and Excel Export
    @app.route('/reports/<type>')
    @login_required
    def view_report(type):
        if type == 'weekly':
<<<<<<< HEAD
            template_name = 'reports/weekly_report.html'
            start_date = datetime.utcnow() - timedelta(days=7)
        elif type == 'monthly':
            template_name = 'reports/monthly_report.html'
            start_date = datetime.utcnow() - timedelta(days=30)
        elif type == 'yearly':
            template_name = 'reports/yearly_report.html'
            start_date = datetime.utcnow() - timedelta(days=365)
        else:
            abort(404)
=======
            start_date = datetime.utcnow() - timedelta(days=7)
        elif type == 'monthly':
            start_date = datetime.utcnow() - timedelta(days=30)
        else: # yearly
            start_date = datetime.utcnow() - timedelta(days=365)
>>>>>>> 833bb768ed7c6fccffd359ca260d50e7b6fd6f09
            
        incomes = Income.query.filter(Income.date >= start_date).all()
        expenses = Expense.query.filter(Expense.date >= start_date).all()
        
<<<<<<< HEAD
        return render_template(template_name, incomes=incomes, expenses=expenses)
=======
        return render_template(f'reports/{type}_report.html', incomes=incomes, expenses=expenses)
>>>>>>> 833bb768ed7c6fccffd359ca260d50e7b6fd6f09

    @app.route('/export/<type>')
    @login_required
    def export_excel(type):
        if type == 'weekly':
            start_date = datetime.utcnow() - timedelta(days=7)
        elif type == 'monthly':
            start_date = datetime.utcnow() - timedelta(days=30)
<<<<<<< HEAD
        elif type == 'yearly':
            start_date = datetime.utcnow() - timedelta(days=365)
        else:
            abort(404)
=======
        else: # yearly
            start_date = datetime.utcnow() - timedelta(days=365)
>>>>>>> 833bb768ed7c6fccffd359ca260d50e7b6fd6f09

        incomes = Income.query.filter(Income.date >= start_date).all()
        expenses = Expense.query.filter(Expense.date >= start_date).all()
        
        income_df = pd.DataFrame([{
            'Date': i.date,
            'Source': i.source,
            'Amount': i.amount,
            'Description': i.description
        } for i in incomes])
        
        expense_df = pd.DataFrame([{
            'Date': e.date,
            'Category': e.category,
            'Amount': e.amount,
            'Description': e.description
        } for e in expenses])
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            income_df.to_excel(writer, sheet_name='Income', index=False)
            expense_df.to_excel(writer, sheet_name='Expenses', index=False)
        
        output.seek(0)
        return send_file(output, as_attachment=True, download_name=f'school_report_{type}.xlsx')
<<<<<<< HEAD

    @app.route('/system-logs')
    @login_required
    def view_system_logs():
        if current_user.role != 'SUPER_ADMIN':
            flash('Access Denied', 'danger')
            return redirect(url_for('dashboard'))
        
        page = request.args.get('page', 1, type=int)
        per_page = 50
        logs = SystemLog.query.order_by(SystemLog.timestamp.desc()).paginate(page=page, per_page=per_page)
        return render_template('system_logs.html', logs=logs)
=======
>>>>>>> 833bb768ed7c6fccffd359ca260d50e7b6fd6f09
