from flask import render_template, url_for, flash, redirect, request, send_file
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy import or_
from models import db, User, Income, Expense, Staff, Budget, Payroll
from forms import LoginForm, UserForm, IncomeForm, ExpenseForm, StaffForm, BudgetForm, ResetPasswordForm, NewPasswordForm, PayrollForm
from datetime import datetime, timedelta
import pandas as pd
import io
import json

def register_routes(app):
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
        if role in ['PRINCIPAL', 'BURSER', 'ACCOUNTANT']:
            pending_expenses = Expense.query.filter_by(status='PENDING').order_by(Expense.date.desc()).all()
        if role in ['SUPER_ADMIN', 'PRINCIPAL', 'BURSER', 'ACCOUNTANT']:
            approved_expenses = Expense.query.filter_by(status='APPROVED').order_by(Expense.date.desc()).all()
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
                             allow_edit_payroll=allow_edit_payroll)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and user.check_password(form.password.data):
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                flash('Login Unsuccessful. Please check email and password', 'danger')
        return render_template('login.html', title='Login', form=form)

    @app.route('/logout')
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
            user = User(username=form.username.data, email=form.email.data, role=form.role.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
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
        form = IncomeForm()
        if form.validate_on_submit():
            income = Income(amount=form.amount.data, source=form.source.data, 
                           description=form.description.data, added_by=current_user.id)
            db.session.add(income)
            db.session.commit()
            flash('Income added!', 'success')
            return redirect(url_for('view_income'))
        return render_template('income/add_income.html', form=form)

    @app.route('/income/view')
    @login_required
    def view_income():
        role = (current_user.role or '').upper()
        if role not in ['SUPER_ADMIN', 'PRINCIPAL', 'BURSER']:
            flash('Access Denied', 'danger')
            return redirect(url_for('dashboard'))
        incomes = Income.query.order_by(Income.date.desc()).all()
        return render_template('income/view_income.html', incomes=incomes)

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
        return render_template('expenses/view_expenses.html', expenses=expenses)

    @app.route('/expenses/approve/<int:expense_id>')
    @login_required
    def approve_expense(expense_id):
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
            flash('Expense is now fully approved and will be recorded.', 'success')
        else:
            flash('Your approval has been recorded. Waiting for other approvers.', 'info')
        db.session.commit()
        return redirect(url_for('view_expenses'))

    @app.route('/expenses/reject/<int:expense_id>')
    @login_required
    def reject_expense(expense_id):
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
        return render_template('staff/view_staff.html', 
                             staff_members=staff_members, 
                             pending_staff=pending_staff)

    @app.route('/staff/approve/<int:staff_id>')
    @login_required
    def approve_staff(staff_id):
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
        flash(f'Staff member {staff.name} has been approved.', 'success')
        return redirect(url_for('dashboard'))

    @app.route('/staff/reject/<int:staff_id>')
    @login_required
    def reject_staff(staff_id):
        role = (current_user.role or '').upper()
        if role not in ['SUPER_ADMIN', 'PRINCIPAL']:
            flash('Access Denied', 'danger')
            return redirect(url_for('dashboard'))
        staff = Staff.query.get_or_404(staff_id)
        if staff.pending_action == 'EDIT':
            staff.pending_action = 'NONE'
            staff.pending_changes = None
            db.session.commit()
            flash(f'Pending changes for {staff.name} have been rejected.', 'warning')
            return redirect(url_for('dashboard'))
        if staff.status == 'PENDING':
            db.session.delete(staff)
            db.session.commit()
            flash(f'Staff member {staff.name} has been rejected and removed.', 'warning')
            return redirect(url_for('dashboard'))
        flash('This staff request cannot be rejected.', 'warning')
        return redirect(url_for('dashboard'))

    # Reporting and Excel Export
    @app.route('/reports/<type>')
    @login_required
    def view_report(type):
        if type == 'weekly':
            start_date = datetime.utcnow() - timedelta(days=7)
        elif type == 'monthly':
            start_date = datetime.utcnow() - timedelta(days=30)
        else: # yearly
            start_date = datetime.utcnow() - timedelta(days=365)
            
        incomes = Income.query.filter(Income.date >= start_date).all()
        expenses = Expense.query.filter(Expense.date >= start_date).all()
        
        return render_template(f'reports/{type}_report.html', incomes=incomes, expenses=expenses)

    @app.route('/export/<type>')
    @login_required
    def export_excel(type):
        if type == 'weekly':
            start_date = datetime.utcnow() - timedelta(days=7)
        elif type == 'monthly':
            start_date = datetime.utcnow() - timedelta(days=30)
        else: # yearly
            start_date = datetime.utcnow() - timedelta(days=365)

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
