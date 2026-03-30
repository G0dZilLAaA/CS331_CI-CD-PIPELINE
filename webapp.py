from flask import Flask, request, render_template, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo
from flask_sqlalchemy import SQLAlchemy
import bcrypt
import requests
import os
from app import process_submission, SUPPORTED_EXT

app = Flask(__name__)
app.secret_key = "dev-secret"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///employees.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

BASE_DIR = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
SAMPLES_DIR = os.path.join(BASE_DIR, "samples")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# API backend url (when running in containers, the service name 'api' is resolvable)
API_URL = os.environ.get("API_URL", "http://api:3000")

# Database Model
class Employee(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(50), nullable=False)  # admin or developer
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

@login_manager.user_loader
def load_user(user_id):
    return Employee.query.get(int(user_id))

# Forms
class LoginForm(FlaskForm):
    employee_id = StringField('Employee ID', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class SignupForm(FlaskForm):
    employee_id = StringField('Employee ID', validators=[DataRequired(), Length(min=1, max=50)])
    name = StringField('Name', validators=[DataRequired(), Length(min=1, max=100)])
    position = SelectField('Position', choices=[('admin', 'Admin'), ('developer', 'Developer')], validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    samples = []
    if os.path.isdir(SAMPLES_DIR):
        samples = [f for f in os.listdir(SAMPLES_DIR) if os.path.splitext(f)[1] in SUPPORTED_EXT]

    if request.method == "POST":
        # sample selected
        sample = request.form.get("sample")
        if sample:
            path = os.path.join(SAMPLES_DIR, sample)
            result = process_submission(path)
            return render_template("result.html", filename=sample, result=result)

        # file uploaded
        uploaded = request.files.get("file")
        if uploaded and uploaded.filename:
            filename = uploaded.filename
            save_path = os.path.join(UPLOAD_FOLDER, filename)
            uploaded.save(save_path)
            result = process_submission(save_path)
            return render_template("result.html", filename=filename, result=result)

        flash("No file uploaded or sample selected")
        return redirect(url_for("index"))

    return render_template("index.html", samples=samples)


@app.route("/webhooks", methods=["GET"])
@login_required
def show_webhooks():
    """Fetch recent webhook entries from the Node API and render them."""
    try:
        resp = requests.get(f"{API_URL}/webhooks", timeout=5)
        if resp.status_code == 200:
            entries = resp.json()
        else:
            entries = []
            flash(f"API returned status {resp.status_code}")
    except Exception as e:
        entries = []
        flash(f"Failed to reach API at {API_URL}: {e}")

    return render_template("webhooks.html", entries=entries)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        employee = Employee.query.filter_by(employee_id=form.employee_id.data).first()
        if employee and employee.check_password(form.password.data):
            login_user(employee)
            return redirect(url_for('dashboard'))
        flash('Invalid employee ID or password')
    return render_template('login.html', form=form)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        if Employee.query.filter_by(employee_id=form.employee_id.data).first():
            flash('Employee ID already exists')
            return redirect(url_for('signup'))
        employee = Employee(employee_id=form.employee_id.data, name=form.name.data, position=form.position.data)
        employee.set_password(form.password.data)
        db.session.add(employee)
        db.session.commit()
        flash('Account created successfully')
        return redirect(url_for('login'))
    return render_template('signup.html', form=form)


@app.route("/dashboard")
@login_required
def dashboard():
    # For now, admin and developer dashboards are the same
    return render_template('dashboard.html')


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    # Bind to 0.0.0.0 so the app is reachable from outside the container
    app.run(debug=True, host="0.0.0.0", port=5000)