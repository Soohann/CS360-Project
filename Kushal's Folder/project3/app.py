import os
import io
from flask import Flask, render_template, request, send_file
import mysql.connector

app = Flask(__name__)

# Connect to the database
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="project_database"
)

# Create the uploads directory if it does not exist
uploads_dir = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(uploads_dir, exist_ok=True)

# Route to display the HTML form for uploading PDF files at the root URL
@app.route('/')
def upload_form():
    return render_template('upload_form.html')

# Route to handle file upload
@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        # Check if the POST request has the file part
        if 'pdf_file' not in request.files:
            return 'No file part'

        file = request.files['pdf_file']

        # If the user does not select a file, the browser submits an empty file without a filename
        if file.filename == '':
            return 'No selected file'

        # Save the file to the uploads directory
        file_path = os.path.join(uploads_dir, file.filename)
        file.save(file_path)

        # Insert the file data into the database (you may need to modify this)
        cursor = conn.cursor()
        with open(file_path, 'rb') as f:
            file_data = f.read()
        cursor.execute("INSERT INTO pdf_files (file_name, file_data) VALUES (%s, %s)", (file.filename, file_data))
        conn.commit()
        cursor.close()

        return 'File uploaded successfully'

# Route to show uploaded projects
@app.route('/projects')
def show_projects():
    cursor = conn.cursor()
    cursor.execute("SELECT id, file_name FROM pdf_files")
    projects = cursor.fetchall()
    cursor.close()
    return render_template('projects.html', projects=projects)

# Route to download a project
@app.route('/project/<int:project_id>')
def download_project(project_id):
    cursor = conn.cursor()
    cursor.execute("SELECT file_name, file_data FROM pdf_files WHERE id = %s", (project_id,))
    project = cursor.fetchone()
    cursor.close()
    if project:
        file_name, file_data = project
        return send_file(
            io.BytesIO(file_data),
            mimetype='application/pdf',
            download_name=file_name,
            as_attachment=True
        )
    else:
        return 'Project not found'

if __name__ == '__main__':
    app.run(debug=True)

