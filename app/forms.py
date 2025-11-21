from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, FloatField, DateField, SelectField, TimeField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from app.models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    employee_id = StringField('Employee ID', validators=[DataRequired(), Length(min=2, max=20)])
    designation = StringField('Designation', validators=[DataRequired()])
    department = StringField('Department', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')
    
    def validate_employee_id(self, employee_id):
        user = User.query.filter_by(employee_id=employee_id.data).first()
        if user:
            raise ValidationError('That Employee ID is already registered.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class UpdateAccountForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    employee_id = StringField('Employee ID', validators=[DataRequired(), Length(min=2, max=20)])
    designation = StringField('Designation', validators=[DataRequired()])
    department = StringField('Department', validators=[DataRequired()])
    monthly_salary = FloatField('Monthly Salary (INR)', validators=[DataRequired()])
    ot_rate = FloatField('Overtime Rate (per hour in INR)', validators=[DataRequired()])
    submit = SubmitField('Update')

    def validate_username(self, username):
        # Check if username is different from current user's username
        # This validation logic needs 'current_user' which is not available here directly
        # We will handle this in the route or pass current_user
        pass 

    def validate_email(self, email):
        pass

class OvertimeForm(FlaskForm):
    date = DateField('Date', validators=[DataRequired()])
    hours = FloatField('Hours', validators=[DataRequired()])
    submit = SubmitField('Add Overtime')

class AttendanceForm(FlaskForm):
    date = DateField('Date', validators=[DataRequired()])
    status = SelectField('Status', choices=[('Present', 'Present'), ('Absent', 'Absent'), ('Leave', 'Leave')], validators=[DataRequired()])
    in_time = TimeField('In Time', validators=[Optional()])
    out_time = TimeField('Out Time', validators=[Optional()])
    submit = SubmitField('Add Attendance')
