from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = 'mysql://root:@localhost/register'
db = SQLAlchemy(app)

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

app.config['SECRET_KEY'] = 'your_secret_key'

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        registrationRole = request.form.get('registrationRole')
        firstName = request.form.get('registrationFirstName')
        lastName = request.form.get('registrationLastName')
        username = request.form.get('registrationUsername')
        email = request.form.get('registrationEmail')
        password = request.form.get('registrationPassword')

        hashed_password = generate_password_hash(password)

        new_user = Users(role=registrationRole, first_name=firstName, last_name=lastName, 
                         username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! You are registered as a {}.'.format(registrationRole))
        return redirect(url_for('login'))
    return render_template('registration.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        user = Users.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password) and user.role == role:
            session['role'] = user.role
            session['username'] = user.username
            return redirect(url_for('dashboard', role=user.role))
        flash('Invalid credentials or role mismatch. Please try again.')
        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/<role>')
def dashboard(role):
    valid_roles = ['Student', 'Professor', 'Community']
    if 'role' not in session or session.get('role') != role or role not in valid_roles:
        flash('Please log in to access this dashboard.')
        return redirect(url_for('login'))
    username = session.get('username')
    if not username:
        flash('An error occurred. Please log in again.')
        return redirect(url_for('login'))

    # Fetch user details directly from the database
    user = Users.query.filter_by(username=username).first()
    if not user:
        flash('User not found. Please log in again.')
        return redirect(url_for('login'))

    # Pass the user's name to the template
    return render_template(f'{role.lower()}.html', first_name=user.first_name, last_name=user.last_name)


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been successfully logged out.')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

