import os
import secrets
import calendar
from datetime import datetime, date
from flask import render_template, url_for, flash, redirect, request, send_file, Response
from app import app, db, bcrypt
from app.forms import RegistrationForm, LoginForm, UpdateAccountForm, OvertimeForm, AttendanceForm
from app.models import User, Overtime, Attendance
from flask_login import login_user, current_user, logout_user, login_required
import pandas as pd
from io import BytesIO
from fpdf import FPDF

from functools import wraps
from flask import abort

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'super_admin':
            flash('Access Denied. Super Admin only.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/health")
def health():
    return "Alive", 200

@app.route("/")
@app.route("/dashboard")
@login_required
def dashboard():
    # Calculate stats
    now = datetime.now()
    current_year = now.year
    
    # Get month from request or default to current
    try:
        selected_month = int(request.args.get('month', now.month))
    except ValueError:
        selected_month = now.month

    overtimes = Overtime.query.filter_by(user_id=current_user.id).filter(db.extract('month', Overtime.date) == selected_month, db.extract('year', Overtime.date) == current_year).all()
    all_attendances = Attendance.query.filter_by(user_id=current_user.id).filter(db.extract('month', Attendance.date) == selected_month, db.extract('year', Attendance.date) == current_year).all()
    present_attendances = [a for a in all_attendances if a.status == 'Present']
    
    total_ot_hours = sum(ot.hours for ot in overtimes)
    total_ot_money = total_ot_hours * current_user.ot_rate
    attendance_days = len(present_attendances)
    
    # Calculate salary based on attendance (percentage/days worked)
    days_in_month = calendar.monthrange(current_year, selected_month)[1]
    daily_salary = current_user.monthly_salary / days_in_month if days_in_month > 0 else 0
    salary_earned = daily_salary * attendance_days
    total_salary = salary_earned + total_ot_money
    
    # Prepare data for chart
    # Group by date
    ot_by_date = {}
    for ot in overtimes:
        d = ot.date.strftime('%d-%m')
        ot_by_date[d] = ot_by_date.get(d, 0) + ot.hours
    
    chart_labels = sorted(ot_by_date.keys())
    chart_data = [ot_by_date[label] for label in chart_labels]

    return render_template('dashboard.html', title='Dashboard', 
                           total_ot_hours=total_ot_hours, 
                           total_ot_money=total_ot_money, 
                           attendance_days=attendance_days,
                           total_salary=total_salary,
                           chart_labels=chart_labels, 
                           chart_data=chart_data,
                           now=now,
                           selected_month=selected_month,
                           overtimes=overtimes,
                           attendances=all_attendances,
                           daily_salary=daily_salary,
                           salary_earned=salary_earned)

@app.route("/history", methods=['GET', 'POST'])
@login_required
def history():
    now = datetime.now()
    month = request.args.get('month', now.month, type=int)
    year = request.args.get('year', now.year, type=int)
    
    overtimes = Overtime.query.filter_by(user_id=current_user.id).filter(db.extract('month', Overtime.date) == month, db.extract('year', Overtime.date) == year).order_by(Overtime.date).all()
    attendances = Attendance.query.filter_by(user_id=current_user.id).filter(db.extract('month', Attendance.date) == month, db.extract('year', Attendance.date) == year).order_by(Attendance.date).all()
    
    total_ot_hours = sum(ot.hours for ot in overtimes)
    total_ot_money = total_ot_hours * current_user.ot_rate
    attendance_days = len([a for a in attendances if a.status == 'Present'])
    
    # Calculate salary based on attendance
    days_in_month = calendar.monthrange(year, month)[1]
    daily_salary = current_user.monthly_salary / days_in_month if days_in_month > 0 else 0
    salary_earned = daily_salary * attendance_days
    total_salary = salary_earned + total_ot_money
    
    return render_template('history.html', title='History', 
                           overtimes=overtimes, attendances=attendances,
                           month=month, year=year,
                           total_ot_hours=total_ot_hours, total_ot_money=total_ot_money,
                           attendance_days=attendance_days, total_salary=total_salary)

@app.route("/admin_dashboard")
@login_required
@admin_required
def admin_dashboard():
    users = User.query.all()
    total_users = User.query.count()
    
    # Active users today (users who logged in today)
    today = date.today()
    active_users_today = User.query.filter(db.func.date(User.last_login) == today).count()
    
    # Total records
    total_ot_records = Overtime.query.count()
    total_att_records = Attendance.query.count()
    total_records = total_ot_records + total_att_records
    
    # New users this month
    current_month = datetime.now().month
    current_year = datetime.now().year
    new_users_month = User.query.filter(db.extract('month', User.created_at) == current_month, 
                                        db.extract('year', User.created_at) == current_year).count()
    
    # Chart Data: New User Signups (Last 30 days)
    # Group by date
    from datetime import timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    new_users_query = db.session.query(db.func.date(User.created_at), db.func.count(User.id))\
        .filter(User.created_at >= start_date)\
        .group_by(db.func.date(User.created_at)).all()
        
    signup_dates = {}
    for d, count in new_users_query:
        signup_dates[str(d)] = count
        
    chart_labels = []
    chart_data = []
    for i in range(30):
        d = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
        chart_labels.append(d)
        chart_data.append(signup_dates.get(d, 0))

    return render_template('admin_dashboard.html', title='Admin Dashboard', 
                           users=users, total_users=total_users,
                           active_users_today=active_users_today,
                           total_records=total_records,
                           new_users_month=new_users_month,
                           chart_labels=chart_labels,
                           chart_data=chart_data)

@app.route("/admin/delete_user/<int:user_id>", methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'super_admin':
        flash('Cannot delete Super Admin.', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.username} has been deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route("/admin/block_user/<int:user_id>", methods=['POST'])
@login_required
@admin_required
def block_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'super_admin':
        flash('Cannot block Super Admin.', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    user.is_blocked = not user.is_blocked
    status = "blocked" if user.is_blocked else "unblocked"
    db.session.commit()
    flash(f'User {user.username} has been {status}.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route("/admin/impersonate/<int:user_id>")
@login_required
@admin_required
def impersonate_user(user_id):
    user = User.query.get_or_404(user_id)
    login_user(user)
    flash(f'You are now logged in as {user.username}.', 'info')
    return redirect(url_for('dashboard'))

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if this is the first user
        is_first_user = User.query.count() == 0
        
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password,
                    employee_id=form.employee_id.data, designation=form.designation.data, department=form.department.data,
                    is_admin=is_first_user) # First user is admin
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You can now log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            if user.is_blocked:
                flash('Your account has been blocked. Please contact Admin.', 'danger')
                return render_template('login.html', title='Login', form=form)
            
            user.last_login = datetime.now()
            user.last_ip = request.remote_addr
            db.session.commit()
            
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/profile", methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.username.data != current_user.username:
            user = User.query.filter_by(username=form.username.data).first()
            if user:
                flash('That username is taken. Please choose a different one.', 'danger')
                return render_template('profile.html', title='Profile', form=form)
        
        if form.email.data != current_user.email:
            user = User.query.filter_by(email=form.email.data).first()
            if user:
                flash('That email is taken. Please choose a different one.', 'danger')
                return render_template('profile.html', title='Profile', form=form)

        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.employee_id = form.employee_id.data
        current_user.designation = form.designation.data
        current_user.department = form.department.data
        current_user.monthly_salary = form.monthly_salary.data
        current_user.ot_rate = form.ot_rate.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.employee_id.data = current_user.employee_id
        form.designation.data = current_user.designation
        form.department.data = current_user.department
        form.monthly_salary.data = current_user.monthly_salary
        form.ot_rate.data = current_user.ot_rate
    return render_template('profile.html', title='Profile', form=form)

@app.route("/add_ot", methods=['GET', 'POST'])
@login_required
def add_ot():
    form = OvertimeForm()
    if form.validate_on_submit():
        if form.date.data > date.today():
            flash('Cannot select a future date.', 'danger')
            return render_template('add_ot.html', title='Add Overtime', form=form)

        # Check for duplicate OT
        existing_ot = Overtime.query.filter_by(user_id=current_user.id, date=form.date.data).first()
        if existing_ot:
            flash('Overtime entry for this date already exists. Please delete it from History to update.', 'warning')
            return redirect(url_for('add_ot'))

        ot = Overtime(date=form.date.data, hours=form.hours.data, author=current_user)
        db.session.add(ot)
        
        # Auto-mark attendance as Present if not exists
        existing_att = Attendance.query.filter_by(user_id=current_user.id, date=form.date.data).first()
        if not existing_att:
            att = Attendance(date=form.date.data, status='Present', author=current_user)
            db.session.add(att)
            flash('Overtime added & Attendance marked as Present!', 'success')
        else:
            flash('Overtime added!', 'success')
            
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('add_ot.html', title='Add Overtime', form=form)

@app.route("/attendance", methods=['GET', 'POST'])
@login_required
def attendance():
    form = AttendanceForm()
    if form.validate_on_submit():
        if form.date.data > date.today():
            flash('Cannot select a future date.', 'danger')
            return redirect(url_for('attendance'))

        # Check for duplicate Attendance
        existing_att = Attendance.query.filter_by(user_id=current_user.id, date=form.date.data).first()
        if existing_att:
            flash('Attendance for this date already exists. Please delete it from History to update.', 'warning')
            return redirect(url_for('attendance'))

        att = Attendance(date=form.date.data, status=form.status.data, 
                         in_time=form.in_time.data, out_time=form.out_time.data, 
                         author=current_user)
        db.session.add(att)
        db.session.commit()
        flash('Attendance added!', 'success')
        return redirect(url_for('attendance'))
    
    # Show attendance history
    attendances = Attendance.query.filter_by(user_id=current_user.id).order_by(Attendance.date.desc()).all()
    return render_template('attendance.html', title='Attendance', form=form, attendances=attendances)

@app.route("/delete_ot/<int:ot_id>", methods=['POST'])
@login_required
def delete_ot(ot_id):
    ot = Overtime.query.get_or_404(ot_id)
    if ot.author != current_user:
        abort(403)
    db.session.delete(ot)
    db.session.commit()
    flash('Overtime record deleted.', 'success')
    return redirect(url_for('history'))

@app.route("/delete_attendance/<int:att_id>", methods=['POST'])
@login_required
def delete_attendance(att_id):
    att = Attendance.query.get_or_404(att_id)
    if att.author != current_user:
        abort(403)
    db.session.delete(att)
    db.session.commit()
    flash('Attendance record deleted.', 'success')
    return redirect(url_for('history'))

@app.route("/export_excel")
@login_required
def export_excel():
    overtimes = Overtime.query.filter_by(user_id=current_user.id).all()
    attendances = Attendance.query.filter_by(user_id=current_user.id).all()
    
    # Calculate Summary Data
    total_ot_hours = sum(ot.hours for ot in overtimes)
    total_ot_money = total_ot_hours * current_user.ot_rate
    present_days = len([a for a in attendances if a.status == 'Present'])
    
    # Assuming current month for salary calculation in report or just total earned so far?
    # Let's provide a summary row.
    # For accurate salary, we need to know the month context. 
    # Since this is a dump of ALL data, let's just show the raw totals.
    
    # To make it more useful, let's group by Month-Year
    data = []
    # Combine dates
    dates = set([ot.date for ot in overtimes] + [att.date for att in attendances])
    sorted_dates = sorted(list(dates))
    
    for d in sorted_dates:
        ot = next((o for o in overtimes if o.date == d), None)
        att = next((a for a in attendances if a.date == d), None)
        
        ot_hours = ot.hours if ot else 0
        ot_amount = ot_hours * current_user.ot_rate
        status = att.status if att else 'Absent' # Default to absent if no record? Or just empty.
        
        # Daily Salary Calculation (Approximate based on 30 days for simplicity in this row-by-row view)
        # A better approach is to just list the data and let the user sum it up, 
        # BUT the user asked for "Total Pay" to be added.
        # Let's add a "Daily Earnings" column = (Monthly/30 if Present) + OT Amount
        daily_base = current_user.monthly_salary / 30 if status == 'Present' else 0
        total_daily_pay = daily_base + ot_amount
        
        data.append({
            'Date': d,
            'Status': status,
            'In Time': att.in_time if att else '',
            'Out Time': att.out_time if att else '',
            'OT Hours': ot_hours,
            'OT Amount': ot_amount,
            'Daily Salary (Approx)': daily_base,
            'Total Pay (Day)': total_daily_pay
        })
        
    df = pd.DataFrame(data)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Detailed Report', index=False)
    
    output.seek(0)
    return send_file(output, download_name='timepay_report.xlsx', as_attachment=True)

@app.route("/change_password", methods=['POST'])
@login_required
def change_password():
    new_password = request.form.get('new_password')
    if new_password:
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        current_user.password = hashed_password
        db.session.commit()
        flash('Password updated successfully!', 'success')
    else:
        flash('Password cannot be empty.', 'danger')
    return redirect(url_for('profile'))

@app.route("/export_pdf")
@login_required
def export_pdf():
    overtimes = Overtime.query.filter_by(user_id=current_user.id).all()
    attendances = Attendance.query.filter_by(user_id=current_user.id).all()
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.cell(200, 10, txt=f"Detailed Report for {current_user.username}", ln=1, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt=f"Emp ID: {current_user.employee_id} | Dept: {current_user.department}", ln=1, align='C')
    pdf.ln(10)
    
    # Table Header
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(30, 10, "Date", 1)
    pdf.cell(25, 10, "Status", 1)
    pdf.cell(20, 10, "OT Hrs", 1)
    pdf.cell(30, 10, "OT Amt", 1)
    pdf.cell(30, 10, "Daily Pay", 1)
    pdf.cell(30, 10, "Total Pay", 1)
    pdf.ln()
    
    pdf.set_font("Arial", size=10)
    
    dates = set([ot.date for ot in overtimes] + [att.date for att in attendances])
    sorted_dates = sorted(list(dates))
    
    total_ot_amt = 0
    total_salary_amt = 0
    
    for d in sorted_dates:
        ot = next((o for o in overtimes if o.date == d), None)
        att = next((a for a in attendances if a.date == d), None)
        
        ot_hours = ot.hours if ot else 0
        ot_amount = ot_hours * current_user.ot_rate
        status = att.status if att else 'Absent'
        
        daily_base = current_user.monthly_salary / 30 if status == 'Present' else 0
        total_daily_pay = daily_base + ot_amount
        
        total_ot_amt += ot_amount
        total_salary_amt += total_daily_pay
        
        pdf.cell(30, 10, d.strftime('%d-%m-%Y'), 1)
        pdf.cell(25, 10, status, 1)
        pdf.cell(20, 10, str(ot_hours), 1)
        pdf.cell(30, 10, f"{ot_amount:.2f}", 1)
        pdf.cell(30, 10, f"{daily_base:.2f}", 1)
        pdf.cell(30, 10, f"{total_daily_pay:.2f}", 1)
        pdf.ln()
        
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(75, 10, "Totals", 1)
    pdf.cell(30, 10, f"{total_ot_amt:.2f}", 1)
    pdf.cell(30, 10, "", 1)
    pdf.cell(30, 10, f"{total_salary_amt:.2f}", 1)
    
    output = BytesIO()
    s = pdf.output(dest='S')
    if isinstance(s, str):
        s = s.encode('latin-1')
    output.write(s)
    output.seek(0)
    
    return send_file(output, download_name='detailed_report.pdf', as_attachment=True, mimetype='application/pdf')

@app.route("/admin/export_pdf")
@login_required
@admin_required
def admin_export_pdf():
    users = User.query.all()
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.cell(200, 10, txt="User Summary Report", ln=1, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt=f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=1, align='C')
    pdf.ln(10)
    
    # Table Header
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(35, 10, "Name", 1)
    pdf.cell(45, 10, "Email", 1)
    pdf.cell(20, 10, "Role", 1)
    pdf.cell(20, 10, "Status", 1)
    pdf.cell(25, 10, "Joined", 1)
    pdf.cell(20, 10, "OT Hrs", 1)
    pdf.cell(25, 10, "Attendance", 1)
    pdf.ln()
    
    pdf.set_font("Arial", size=9)
    
    for user in users:
        total_ot = sum(ot.hours for ot in user.overtimes)
        total_att = len([a for a in user.attendances if a.status == 'Present'])
        
        pdf.cell(35, 10, user.username, 1)
        pdf.cell(45, 10, user.email, 1)
        pdf.cell(20, 10, user.role, 1)
        pdf.cell(20, 10, 'Blocked' if user.is_blocked else 'Active', 1)
        pdf.cell(25, 10, user.created_at.strftime('%Y-%m-%d'), 1)
        pdf.cell(20, 10, str(total_ot), 1)
        pdf.cell(25, 10, f"{total_att} Days", 1)
        pdf.ln()
        
    output = BytesIO()
    s = pdf.output(dest='S')
    if isinstance(s, str):
        s = s.encode('latin-1')
    output.write(s)
    output.seek(0)
    
    return send_file(output, download_name='admin_user_report.pdf', as_attachment=True, mimetype='application/pdf')

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response
