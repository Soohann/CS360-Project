from http import client
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask import jsonify
from flask_cors import CORS
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from flask import session
from flask import session, jsonify
from flask import request, jsonify, session
from sqlalchemy.exc import IntegrityError
from flask import Flask, request, jsonify, session, redirect, url_for
from flask import Flask, request, jsonify
from openai import OpenAI
import os 
from flask import Flask




app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/ankit' 
db = SQLAlchemy(app)

# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
    id = db.Column(db.Integer, primary_key=True)
    community_member_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    department = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)

    # Relationship (if you have a User model and want to use backref)
    community_member = db.relationship('User', backref=db.backref('projects', lazy=True))


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


app = Flask(__name__)

@app.route('/upload_project', methods=['POST'])
def upload_project():
    if request.method == 'POST':
        # Extract data from the form
        department = request.form.get('projectDepartment')
        title = request.form.get('projectTitle')
        description = request.form.get('projectDescription')

        # Assume community_member_id is obtained through session or login (placeholder here)
        community_member_id = 1  # Placeholder: replace with actual logic to get current user's ID

        # Create a new Project instance
        new_project = Project(
            community_member_id=community_member_id,
            department=department,
            title=title,
            description=description
        )

        # Add to the session and commit to the database
        db.session.add(new_project)
        db.session.commit()

        # Redirect or respond as necessary
        return jsonify({'message': 'Project uploaded successfully!'}), 200
    else:
        return jsonify({'error': 'Invalid request method.'}), 405



@app.before_request
def before_request():
    print(request.path)




@app.route('/request_project/<int:project_id>', methods=['POST'])
def request_project(project_id):
    print("Received request for project_id:", project_id)

    # Assuming the session['user_id'] holds the ID of the currently logged-in student
    student_id = session.get('user_id')

    # Check if a student is logged in by ensuring student_id is present
    if not student_id:
        return jsonify({"error": "Student is not logged in"}), 403

    # Check if a request from this student for this project already exists to avoid duplicates
    existing_request = Request.query.filter_by(project_id=project_id, student_id=student_id).first()
    if existing_request:
        return jsonify({"error": "Request for this project already exists"}), 409

    # Create a new project request without specifying a professor_id
    new_request = Request(
        project_id=project_id,
        student_id=student_id,
        status='pending'
    )

    # Add the new request to the database session and commit it
    db.session.add(new_request)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(e)  # Log the exception
        return jsonify({"error": "An error occurred while submitting the request"}), 500

    # Return a success message
    return jsonify({"message": "Project request submitted successfully"}), 200








@app.route('/review_request/<int:request_id>/<action>', methods=['POST'])
def review_request(request_id, action):
    # Only professors can review project requests
    if session.get('role') != 'Professor':
        flash('You do not have permission to review project requests.')
        return redirect(url_for('dashboard', role=session.get('role')))
    
    project_request = Request.query.get(request_id)
    if action == 'approve':
        project_request.status = 'approved'

        
        # Placeholder for syllabus generation
        # syllabus_content = generate_syllabus_content(project_request.project_id)
        # syllabus = Syllabus(project_id=project_request.project_id, syllabus_content=syllabus_content)
        # db.session.add(syllabus)
    elif action == 'reject':
        project_request.status = 'rejected'
    db.session.commit()
    flash('Project request has been ' + action + 'd.')
    return redirect(url_for('dashboard', role='Professor'))



@app.route('/get_projects')
def get_projects():
    projects = Project.query.all()  # Assuming Project is your model for projects
    projects_data = []

    for project in projects:
        projects_data.append({
            'project_id': project.project_id,
            'title': project.title,
            'description': project.description,
            # Add other fields as needed
        })
    
    return jsonify({'projects': projects_data})


@app.route('/get_uploaded_projects')
def get_uploaded_projects():
    projects = Project.query.filter_by(community_member_id=session.get('user_id')).all()
    projects_data = [{
        'project_id': project.project_id,
        'title': project.title,
        'description': project.description
    } for project in projects]

    return jsonify(projects=projects_data)


@app.route('/delete_project/<int:project_id>', methods=['POST'])
def delete_project(project_id):
    if 'user_id' not in session:
        return jsonify({'message': 'User not authenticated'}), 401
    
    # Additional checks here to ensure the user is allowed to delete this project
    
    project_to_delete = Project.query.get(project_id)
    if not project_to_delete:
        return jsonify({'message': 'Project not found'}), 404

    db.session.delete(project_to_delete)
    db.session.commit()

    return jsonify({'message': 'Project deleted successfully'})



@app.route('/get_project_requests')
def get_project_requests():
    if 'user_id' not in session:
        return jsonify({'message': 'User not authenticated'}), 401

    # Ensuring that only professors can access the project requests
    user_role = session.get('role')
    if user_role != 'Professor':
        return jsonify({'message': 'Unauthorized'}), 403

    # Fetch the requests along with student and project information
    project_requests = db.session.query(
        Request.request_id,
        Request.project_id,
        User.first_name.label('student_first_name'),
        User.last_name.label('student_last_name'),
        Project.title.label('project_title'),
        Project.description.label('project_description')
    ).join(User, User.id == Request.student_id
    ).join(Project, Project.project_id == Request.project_id
    ).all()

    requests_data = [{
        'request_id': req.request_id,
        'first_name': req.student_first_name,
        'last_name': req.student_last_name,
        'project_title': req.project_title,
        'description': req.project_description
    } for req in project_requests]

    return jsonify(requests_data)



from openai import OpenAI

import os



@app.route('/accept_project_request/<int:request_id>', methods=['POST'])
def accept_project_request(request_id):
    project_request = db.session.get(Request, request_id)
    # Initialize syllabus_content with a default value
    syllabus_content = "Syllabus content could not be generated."
    
    if project_request:
        project_request.status = 'accepted'
        db.session.commit()
        
        project = db.session.get(Project, project_request.project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404

        try:
            # API call with correct structure
            response = client.completions.create(
                model="davinci-002",  # Ensure this model is available to your account
                prompt=f"Generate a syllabus based on the following project description:\n\n{project.description}",
                temperature=0.5,
                max_tokens=1024,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0,
                n=1  # Ensure this parameter is set if needed, depending on your account's model access
            )
            syllabus_content = response.choices[0].text.strip()
        except Exception as e:
            print(f'Failed to generate syllabus: {e}')

        # Use syllabus_content even if the API call fails
        new_syllabus = Syllabus(project_id=project_request.project_id, syllabus_content=syllabus_content)
        db.session.add(new_syllabus)
        db.session.commit()
        
        return jsonify({'message': 'Request accepted and syllabus generated', 'syllabus': syllabus_content})
    else:
        return jsonify({'message': 'Request not found'}), 404



@app.route('/reject_project_request/<int:request_request_id>', methods=['POST'])
def reject_project_request(request_request_id):
    # Authenticate the user to ensure they are logged in and are a professor
    if 'user_id' not in session or session.get('role') != 'Professor':
        return jsonify({'message': 'Unauthorized'}), 403

    # Fetch the project request using the request_id
    project_request = Request.query.get(request_request_id)
    if not project_request:
        return jsonify({'message': 'Project request not found'}), 404

    # Update the status of the project request to 'rejected'
    project_request.status = 'rejected'
    db.session.commit()

    # Fetch the student's details to send them a notification
    student = User.query.get(project_request.student_id)
    if student:
        # This assumes you have some way to notify the student (e.g., email, in-app notification)
        # Here you would call that function, e.g., send_notification(student.email, "Your project request has been rejected.")
        # For simplicity, we'll just print a message (you should replace this with actual notification logic)
        print(f"Notification sent to {student.email}: Your project request has been rejected.")

    return jsonify({'message': 'Project request rejected successfully'})



# Mock function to represent sending notifications
def send_notification(user, message):
    # Here you would implement the actual logic to send a notification to the user
    print(f"Notification sent to {user.username}: {message}")

# @app.route('/get_syllabus/<int:project_id>')
# def get_syllabus(project_id):
#     # Ensure you are referencing the globally defined Project and Syllabus classes
#     project = Project.query.get(project_id)
#     if not project:
#         return jsonify({'message': 'Project not found'}), 404

#     syllabus = Syllabus.query.filter_by(project_id=project_id).first()
#     if syllabus:
#         return jsonify({
#             'project_title': project.title,
#             'syllabus_content': syllabus.syllabus_content
#         })

#     return jsonify({'message': 'Syllabus not found for the selected project'}), 404
    

@app.route('/get_syllabus/<int:project_id>')
def get_syllabus(project_id):
    syllabus = Syllabus.query.filter_by(project_id=project_id).first()
    if syllabus:
        return jsonify({'project_title': syllabus.project.title, 'syllabus_content': syllabus.syllabus_content})
    else:
        return jsonify({'message': 'Syllabus not found'}), 404





from openai import OpenAI


# Make sure to set your OpenAI API key

def generate_syllabus(description):
    try:
        # Replace 'text-davinci-003' with the model you intend to use, if different
        response = client.completions.create(model="davinci-002",  # or "davinci" or any other available engines
        prompt=f"Generate a short syllabus for a project based on the following project description:\n\n{description}\n\nSyllabus:",
        temperature=0.7,  # Controls randomness: lower values make the text more deterministic
        max_tokens=1000,  # Maximum length of the generated content
        top_p=1,  # Controls diversity
        frequency_penalty=0,  # Penalizes new tokens based on their existing frequency in the text so far
        presence_penalty=0  # Penalizes new tokens based on whether they appear in the text so far)
        # Extract the generated text from the response object
        )
        syllabus_text = response.choices[0].text.strip()
        return syllabus_text
    except Exception as e:
        print(f"Error generating syllabus: {e}")
        return None 


def save_syllabus_to_database(project_id, syllabus_content):
    new_syllabus = Syllabus(project_id=project_id, syllabus_content=syllabus_content)
    db.session.add(new_syllabus)
    db.session.commit()
 



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
        syllabus = Syllabus.query.filter_by(project_id=req.project_id).first()
        if syllabus:
            syllabuses.append(syllabus)
    
    return render_template('student_dashboard.html', syllabuses=syllabuses)




@app.route('/get_all_syllabuses')
def get_all_syllabuses():
    # Check if the user is logged in
    if 'user_id' not in session or 'role' not in session:
        return jsonify({'error': 'Not logged in'}), 401  # Send an unauthorized status code

    # Get the role and user_id from the session
    role = session.get('role')
    user_id = session.get('user_id')

    syllabuses_data = []

    if role == 'Professor':
        # Fetch all accepted requests where the current user is the professor
        accepted_requests = Request.query.filter_by(professor_id=user_id, status='accepted').all()
        # Iterate over the accepted requests and fetch the corresponding syllabuses
        for req in accepted_requests:
            syllabus = Syllabus.query.filter_by(project_id=req.project_id).first()
            if syllabus:
                # Append the project title and syllabus content to the list
                project = Project.query.get(req.project_id)
                syllabuses_data.append({
                    'project_title': project.title if project else "No title",  # Safety check in case project is None
                    'syllabus_content': syllabus.syllabus_content
                })
    elif role == 'Student':
        # Fetch all accepted requests where the current user is the student
        accepted_requests = Request.query.filter_by(student_id=user_id, status='accepted').all()
        # Similar logic to fetch syllabuses for students
        for req in accepted_requests:
            syllabus = Syllabus.query.filter_by(project_id=req.project_id).first()
            if syllabus:
                project = Project.query.get(req.project_id)
                syllabuses_data.append({
                    'project_title': project.title if project else "No title",
                    'syllabus_content': syllabus.syllabus_content
                })

    # If there are no syllabuses, you might want to handle that with a message
    if not syllabuses_data:
        return jsonify({'message': 'No syllabuses available'}), 200

    return jsonify(syllabuses_data)








def add_notification_for_student(student_id, message):
    # Create a new notification instance
    new_notification = Notification(student_id=student_id, message=message)
    
    # Add the new notification to the session and commit it to the database
    db.session.add(new_notification)
    try:
        db.session.commit()
        print("Notification added successfully.")
    except Exception as e:
        db.session.rollback()
        print(f"Failed to add notification: {e}")



from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Session






if __name__ == '__main__':
    app.run(debug=True)    



