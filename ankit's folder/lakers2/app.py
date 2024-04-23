from http import client
from django.http import JsonResponse
from flask import Flask, Request, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import openai
from werkzeug.security import generate_password_hash, check_password_hash
from flask import jsonify
from flask_cors import CORS
from sqlalchemy import ForeignKey
from sqlalchemy.exc import SQLAlchemyError 
from sqlalchemy.orm import relationship, aliased
from flask import session
from flask import session, jsonify
from flask import request, jsonify, session
from sqlalchemy.exc import IntegrityError
from flask import Flask, request, jsonify, session, redirect, url_for
from flask import Flask, request, jsonify
from openai import OpenAI
import os 
from flask import Flask
import logging





app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/ankit' 
db = SQLAlchemy(app)


# app.config['SESSION_COOKIE_SECURE'] = True  # Only send cookies over HTTPS.
# app.config['REMEMBER_COOKIE_SECURE'] = True # If using Flask-Login and remember me feature

openai.api_key = os.getenv("OPENAI_API_KEY")

# database started from here

def create_tables():
    db.create_all()


class User(db.Model):
    __tablename__ = 'Users'
    user_id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(255), nullable=False)
    department = db.Column(db.String(255), nullable=True)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


class Project(db.Model):
    __tablename__ = 'projects'
    project_id = db.Column(db.Integer, primary_key=True)
    community_member_id = db.Column(db.Integer, db.ForeignKey('Users.user_id'), nullable=False)
    project_department = db.Column(db.String(255), nullable=False)  # Ensure column name matches your database
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    # Relationship
    community_member = db.relationship('User', backref=db.backref('projects', lazy=True))




class Notification(db.Model):
    __tablename__ = 'notifications'
    notification_id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.project_id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('Users.user_id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('Users.user_id'), nullable=False)
    notification_type = db.Column(db.String(255), nullable=False)  # Types like 'Project Request', 'Syllabus Submission'
    status = db.Column(db.String(255), default='Pending')  # States like 'Pending', 'Accepted', 'Rejected', 'Viewed'
    message = db.Column(db.Text, nullable=True)  # Optional message from the student
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, onupdate=db.func.current_timestamp())

    # Relationships
    project = db.relationship('Project', backref='notifications')
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref=db.backref('received_notifications', lazy=True))
    sender = db.relationship('User', foreign_keys=[sender_id], backref=db.backref('sent_notifications', lazy=True))



class Syllabus(db.Model):
    __tablename__ = 'syllabuses'
    syllabus_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.project_id'), nullable=False)
    auto_syllabus = db.Column(db.Text)
    notification_id = db.Column(db.Integer, db.ForeignKey('notifications.notification_id'), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, onupdate=db.func.current_timestamp())
    # ... other fields and relationships ...

    # Relationships
    notification = db.relationship('Notification', backref='syllabus', foreign_keys=[notification_id])
    project = db.relationship('Project', backref='syllabus')

    




app.config['SECRET_KEY'] = 'your_secret_key'

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        # Updated to match the form's input names
        role = request.form.get('role')
        department = request.form.get('department')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        # Optional: confirm_password = request.form.get('registrationConfirmPassword')

        hashed_password = generate_password_hash(password)
        new_user = User(role=role, department=department, first_name=first_name, last_name=last_name, 
                         username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! You are registered as a {}.'.format(role))
        return redirect(url_for('login'))
    return render_template('registration.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password) and user.role == role:
            session['role'] = user.role
            session['username'] = user.username
            session['user_id'] = user.user_id
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
    return render_template(f'{role.lower()}.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been successfully logged out.')
    return redirect(url_for('login')) 

# ////////////////////////////////////////////////////////////////////////////////////

@app.route('/upload_project', methods=['POST'])
def upload_project():
    if 'user_id' not in session or session.get('role') != 'Community':
        return jsonify({'error': 'Unauthorized access'}), 401

    # Use request.get_json() to get data sent as JSON
    data = request.get_json()

    # Extract data from the JSON payload
       # Create new project instance
    new_project = Project(
        community_member_id=session.get('user_id'),
        project_department=project_department,
        title=title,
        description=description
    )

    # Attempt to save to the database
    try:
        db.session.add(new_project)
        db.session.commit()
        return jsonify({'message': 'Project uploaded successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error uploading project: {}'.format(e)}), 500






















# //////////////////////////////////////////////////

@app.route('/get_uploaded_projects', methods=['GET'])
def get_my_projects():
    app.logger.debug("Attempting to fetch projects")
    user_id = session.get('user_id')
    if not user_id:
        app.logger.warning("Session user_id not found, sending 403 response")
        return jsonify({'error': 'Authentication required'}), 403

    try:
        app.logger.debug(f"Fetching projects for user_id: {user_id}")
        projects = Project.query.filter_by(community_member_id=user_id).all()
        project_list = [{
            'project_id': project.project_id,
            'title': project.title,
            'department': project.project_department,
            'description': project.description
        } for project in projects]
        app.logger.debug("Projects fetched successfully")
        return jsonify(project_list)
    except Exception as e:
        app.logger.error(f"Failed to fetch projects: {str(e)}")
        return jsonify({'error': str(e)}), 500

# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

@app.route('/api/projects/<department>', methods=['GET'])
def get_projects(department):
    projects = Project.query.filter_by(project_department=department).all()
    professors = User.query.filter_by(department=department).all()

    professor_list = [{"id": prof.user_id, "name": f"{prof.first_name} {prof.last_name}"} for prof in professors]

    results = [
        {
            "project_id": project.project_id,
            "title": project.title,
            "description": project.description,
            "professors": professor_list  # Include all professors in each project
        } for project in projects
    ]
    return jsonify(results)





@app.route('/api/apply/<int:project_id>', methods=['POST'])
def apply_to_project(project_id):
    logging.basicConfig(level=logging.DEBUG)
    if 'user_id' not in session:
        logging.error("User ID not found in session")
        return jsonify({'error': 'Authentication required'}), 401
    
    user_id = session['user_id']
    logging.debug(f"Applying with user ID: {user_id}")
    data = request.get_json()
    professor_id = data.get('professorId')

    try:
        notification = Notification(
            project_id=project_id,
            recipient_id=professor_id,
            sender_id=user_id,
            notification_type='Project Request',
            status='Pending',
            message='Student has applied for a project'
        )
        db.session.add(notification)
        db.session.commit()
        logging.info("Notification created successfully")
        return jsonify({'message': 'Application submitted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to submit application: {e}")
        return jsonify({'error': 'Failed to submit application: {}'.format(e)}), 500






# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    if 'user_id' not in session or session['role'] != 'Professor':
        return jsonify({'error': 'Unauthorized'}), 401

    professor_id = session['user_id']
    try:
        # Fetch notifications where the logged-in professor is the recipient
        notifications = Notification.query\
            .join(Project, Notification.project_id == Project.project_id)\
            .join(User, Notification.sender_id == User.user_id)\
            .filter(Notification.recipient_id == professor_id, Notification.status == 'Pending')\
            .add_columns(
                User.first_name,
                User.last_name,
                User.user_id,
                Project.title,
                Project.description,
                Notification.notification_id
            ).all()

        formatted_notifications = [{
            'submission_id': notif.notification_id,
            'student_name': f"{notif.first_name} {notif.last_name}",
            'student_id': notif.user_id,
            'project_title': notif.title,
            'project_description': notif.description
        } for notif in notifications]

        return jsonify(formatted_notifications)
    except Exception as e:
        print(e)  # Consider using logging.debug(e) or logging.error(e)
        return jsonify({'error': str(e)}), 500


@app.route('/api/accepted_notifications', methods=['GET'])
def get_accepted_notifications():
    if 'user_id' not in session or session['role'] != 'Professor':
        return jsonify({'error': 'Unauthorized'}), 401

    professor_id = session['user_id']
    try:
        notifications = Notification.query\
            .join(Project, Notification.project_id == Project.project_id)\
            .join(User, Notification.sender_id == User.user_id)\
            .filter(Notification.recipient_id == professor_id, Notification.status == 'Accepted')\
            .add_columns(
                User.first_name,
                User.last_name,
                User.user_id,
                Project.title,
                Project.description,
                Notification.notification_id
            ).all()

        formatted_notifications = [{
            'notification_id': notif.Notification.notification_id,
            'student_first_name': notif.first_name,
            'student_last_name': notif.last_name,
            'student_id': notif.user_id,
            'project_title': notif.title,
            'project_description': notif.description
        } for notif in notifications]

        return jsonify(formatted_notifications)
    except Exception as e:
        return jsonify({'error': str(e)}), 500





@app.route('/api/syllabus/<int:notification_id>', methods=['GET'])
def get_syllabus(notification_id):
    try:
        # Attempt to retrieve the Syllabus associated with the provided notification_id
        syllabus = Syllabus.query.filter_by(notification_id=notification_id).first()
        if syllabus:
            # If a Syllabus entry is found, return the auto_syllabus content
            return jsonify({
                'syllabus_id': syllabus.syllabus_id,
                'auto_syllabus': syllabus.auto_syllabus
            }), 200
        else:
            # If no Syllabus entry is found for the notification_id, return an error message
            return jsonify({'message': 'Syllabus not found'}), 404
    except Exception as e:
        # Log the exception and return an internal server error message
        app.logger.error(f'Failed to fetch syllabus for notification ID {notification_id}: {str(e)}')
        return jsonify({'error': 'Internal Server Error'}), 500






















@app.route('/dashboard/professor')
def professor_dashboard():
    if 'user_id' not in session or session['role'] != 'Professor':
        flash('Unauthorized access.')
        return redirect(url_for('login'))

    professor_id = session['user_id']
    # Fetching requests that have been accepted by this professor
    accepted_requests = Request.query.filter_by(professor_id=professor_id, status='accepted').all()
    
    syllabuses = [Syllabus.query.filter_by(project_id=req.project_id).first() for req in accepted_requests]
    
    return render_template('professor_dashboard.html', syllabuses=syllabuses)




@app.route('/dashboard/student')
def student_dashboard():
    if 'user_id' not in session or session['role'] != 'Student':
        flash('Unauthorized access.')
        return redirect(url_for('login'))

    student_id = session['user_id']
    # Fetching requests made by this student that have been accepted
    accepted_requests = Request.query.filter_by(student_id=student_id, status='accepted').all()
    
    syllabuses = []
    for req in accepted_requests:
        syllabus = syllabus.query.filter_by(project_id=req.project_id).first()
        if syllabus:
            syllabuses.append(syllabus)
    
    return render_template('student_dashboard.html', syllabuses=syllabuses)

# ///////////////////////////////////////////////////////////////
# /////////////////////////////////////////////////////
# ///////////////////////////////////////////////////////
# /////////////////////////////////////////









@app.route('/api/accept_notification/<int:notification_id>', methods=['POST'])
def accept_notification(notification_id):
    if 'user_id' not in session or session['role'] != 'Professor':
        return jsonify({'error': 'Unauthorized'}), 401

    notification = Notification.query.get(notification_id)
    if not notification:
        return jsonify({'error': 'Notification not found'}), 404

    # Change the status of the notification to 'Accepted'
    notification.status = 'Accepted'

    # Retrieve the project details
    project = Project.query.get(notification.project_id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404

    # Generate syllabus
    syllabus_content = generate_syllabus(project.description)
    if syllabus_content:
        # Save the generated syllabus to the database, including the notification_id
        new_syllabus = Syllabus(
            project_id=project.project_id, 
            auto_syllabus=syllabus_content,
            notification_id=notification_id  # Set the notification_id for the new syllabus
        )
        db.session.add(new_syllabus)
        db.session.commit()
        return jsonify({'message': 'Notification accepted and syllabus generated', 'syllabus': syllabus_content})
    else:
        return jsonify({'error': 'Failed to generate syllabus'}), 500






from openai import OpenAI


from openai import OpenAI
import os
import openai



openai.api_key = os.getenv('OPENAI_API_KEY')

def generate_syllabus(description):
    # Directly setting the API key (not recommended for production)

    prompt = (
        f"Generate a syllabus based on the following project description:\n\n"
        f"{description}\n\n"
        "The syllabus should be strictly for a 12-week period with 3 credits earned. "
        "It should include a detailed timeline, milestones, and a grading system. "
        "There should be no quizzes or assignments, and the difficulty level and evaluation criteria should be clearly stated."
    )
    
    try:
        response = openai.completions.create(model="gpt-3.5-turbo-instruct",  # Check for the exact model name and availability
        prompt=prompt,
        temperature=0.5,  # Moderate creativity
        max_tokens=2000,
        top_p=1.0,
        frequency_penalty=0.0, 
        presence_penalty=0.0)
        syllabus_text = response.choices[0].text.strip()
        return syllabus_text
    except Exception as e:
        print(f"Error generating syllabus: {e}")
        return None


# /////////////////////////////////////////////////////
# //////////////////////
# //////////////////////////
# //////////////////////////////
# //////////////////








if __name__ == '__main__':
    app.run(debug=True) 