from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
import csv
import os
import logging
import re
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resumes')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

app.secret_key = 'your_secret_key'  # Add a secret key for flashing messages

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure the UPLOAD_FOLDER directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def sanitize_filename(filename):
    filename = re.sub(r'[^\w\.-]', '_', filename)  # Replace non-alphanumeric characters
    max_length = 255
    name, ext = os.path.splitext(filename)
    if len(name) > max_length - len(ext):
        name = name[:max_length - len(ext)]  # Ensure filename length is within limit
    return name + ext

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf', 'doc', 'docx', 'txt'}

# Define a custom filter to format the date
@app.template_filter('datetimeformat')
def datetimeformat(value):
    try:
        date_obj = datetime.strptime(value, '%Y-%m-%d')  # Assuming the date format in CSV is YYYY-MM-DD
        return date_obj.strftime('%m/%d/%Y')
    except (ValueError, TypeError):
        return value  # Return the original value if it cannot be parsed

# Load open positions from CSV file
def load_positions(status_filter=None, filter_by=None, filter_value=None, sort_by=None, order='asc'):
    file_path = 'positions.csv'
    
    if not os.path.exists(file_path):
        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['REQ#', 'Date Opened', 'Recruiter', 'Position Title', 'Paygrade', 'Status', 'Priority', 'Product Team', 'Hiring Manager'])
    
    positions = []
    
    with open(file_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if status_filter and row['Status'] != status_filter:
                continue
            if filter_by and filter_value:
                if filter_value.lower() not in row[filter_by].lower():
                    continue
            positions.append(row)
    
    if sort_by:
        reverse = (order == 'desc')
        positions.sort(key=lambda x: x[sort_by], reverse=reverse)
    
    return positions



# Save positions to CSV file
def save_positions(positions):
    if not positions:
        with open('positions.csv', mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=[])
            writer.writeheader()
        return
    
    with open('positions.csv', mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=positions[0].keys())
        writer.writeheader()
        writer.writerows(positions)

# Load applicants for a specific position from CSV file
def load_applicants(req_number):
    applicants = []
    try:
        with open(f'{req_number}_applicants.csv', mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if 'Hired' not in row:
                    row['Hired'] = 'No'
                applicants.append(row)
    except FileNotFoundError:
        pass
    return applicants

def save_applicants(req_number, applicants):
    with open(f'{req_number}_applicants.csv', mode='w', newline='') as file:
        fieldnames = ['Applicant Name', 'Location', 'Shift', 'Salary Expectation', 'Interview 1 Date', 'Interview 1 Feedback', 'Interview 2 Date', 'Interview 2 Feedback', 'Interview 3 Date', 'Interview 3 Feedback', 'Interview 4 Date', 'Interview 4 Feedback', 'Resume', 'Hired']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(applicants)


# Load interview questions from external text files
def load_interview_questions(selected_file):
    questions_with_notes = []
    try:
        with open(f'interview_questions/{selected_file}.txt', 'r') as file:
            for line in file:
                question = line.strip()
                if question:
                    questions_with_notes.append((question, ''))
    except FileNotFoundError:
        pass
    return questions_with_notes

def load_interview_notes(file_name):
    file_path = os.path.join('interview_notes', file_name)
    questions_with_notes = []

    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            question = None
            note = None
            for line in file:
                line = line.strip()
                if line.startswith('Question:'):
                    if question and note:
                        questions_with_notes.append((question, note))
                        note = None
                    question = line[10:].strip()
                elif line.startswith('Note:'):
                    note = line[5:].strip()

            if question and note:
                questions_with_notes.append((question, note))

    return questions_with_notes

@app.route('/interview_questions', methods=['GET', 'POST'])
def interview_questions():
    open_positions = load_positions(status_filter='Open')
    
    req_number = request.args.get('req_number')
    applicant_name = request.args.get('applicant_name')

    if req_number and applicant_name:
        # Load interview questions and notes for the specific applicant and position
        file_name = f"{applicant_name}_{req_number}_interview_notes.txt"
        questions_with_notes = load_interview_notes(file_name)
        return render_template('interview_questions.html', interview_files=get_interview_files(), questions_with_notes=questions_with_notes, open_positions=open_positions)

    if request.method == 'POST':
        selected_files = request.form.getlist('file_checkbox')
        questions_by_file = {}
        for file_name in selected_files:
            file_key = file_name.replace('.txt', '')
            questions_with_notes = load_interview_questions(file_key)
            questions_by_file[file_key] = questions_with_notes
        return render_template('interview_questions.html', interview_files=get_interview_files(), questions_by_file=questions_by_file, open_positions=open_positions)

    return render_template('interview_questions.html', interview_files=get_interview_files(), open_positions=open_positions)


@app.route('/save_interview_notes', methods=['POST'])
def save_interview_notes_route():
    req_number = request.form['req_number']
    applicant_name = request.form['applicant_name']
    other_comments = request.form['other_comments']  # Extract other comments

    notes = request.form.getlist('note')
    questions = request.form.getlist('question')

    print("Notes list:")
    print(notes)
    print("Questions list:")
    print(questions)

    file_name = f"{applicant_name}_{req_number}_interview_notes.txt"
    save_interview_notes(file_name, notes, questions, other_comments)  # Pass other comments to save function

    return redirect(url_for('interview_questions'))

def save_interview_notes(file_name, notes, questions, other_comments):
    if not os.path.exists('interview_notes'):
        os.makedirs('interview_notes')

    file_path = os.path.join('interview_notes', file_name)

    with open(file_path, 'w', encoding='utf-8') as file:
        for i in range(len(questions)):
            question_text = questions[i]
            note = notes[i] if i < len(notes) else ''
            file.write(f'Question: {question_text}\n')
            file.write(f'Note: {note}\n\n')
        # Write other comments at the end
        file.write('Other Comments:\n')
        file.write(f'{other_comments}\n')


def get_interview_files():
    interview_files = []
    for file_name in os.listdir('interview_questions'):
        if file_name.endswith('.txt'):
            interview_files.append(file_name)
    return interview_files

@app.route('/load_interview_notes', methods=['GET'])
def load_interview_notes_route():
    applicant_name = request.args.get('applicant_name')
    req_number = request.args.get('req_number')

    if applicant_name and req_number:
        file_name = f"{applicant_name}_{req_number}_interview_notes.txt"
        file_path = os.path.join('interview_notes', file_name)

        if os.path.exists(file_path):
            questions_with_notes = load_interview_notes(file_name)
            notes_html = ""
            for question, note in questions_with_notes:
                notes_html += f"<h3>{question}</h3>"
                notes_html += f"<p>{note}</p>"
            return notes_html
        else:
            return "Interview notes file not found."
    else:
        return "Invalid request parameters."

@app.route('/')
def home():
    status_filter = request.args.get('status_filter')
    sort_by = request.args.get('sort_by')

    positions = load_positions()

    if status_filter:
        positions = [position for position in positions if position['Status'] == status_filter]

    if sort_by:
        positions.sort(key=lambda x: x[sort_by])

    return render_template('home.html', positions=positions)



@app.route('/position/<req_number>')
def position(req_number):
    positions = load_positions()
    position = next((pos for pos in positions if pos['REQ#'] == req_number), None)
    if position is None:
        return "Position not found", 404
    applicants = load_applicants(req_number)
    return render_template('position.html', req_number=req_number, position=position, applicants=applicants)

@app.route('/add_position', methods=['POST'])
def add_position():
    new_position = {
        'REQ#': request.form['req_number'],
        'Date Opened': request.form['date_opened'],
        'Recruiter': request.form['recruiter'],
        'Position Title': request.form['position_title'],
        'Paygrade': request.form['paygrade'],
        'Status': request.form['status'],
        'Priority': request.form['priority'],
        'Product Team': request.form['product_team'],
        'Hiring Manager': request.form['hiring_manager'],
    }
    positions = load_positions()
    positions.append(new_position)
    save_positions(positions)
    return redirect(url_for('home'))

@app.route('/edit_position/<req_number>', methods=['GET', 'POST'])
def edit_position(req_number):
    if request.method == 'POST':
        positions = load_positions()
        for position in positions:
            if position['REQ#'] == req_number:
                position['Date Opened'] = request.form['date_opened']
                position['Recruiter'] = request.form['recruiter']
                position['Position Title'] = request.form['position_title']
                position['Paygrade'] = request.form['paygrade']
                position['Status'] = request.form['status']
                position['Priority'] = request.form['priority']
                position['Product Team'] = request.form['product_team']
                position['Hiring Manager'] = request.form['hiring_manager']
                break
        save_positions(positions)
        return redirect(url_for('home'))
    else:
        positions = load_positions()
        position = next((pos for pos in positions if pos['REQ#'] == req_number), None)
        if position is None:
            return "Position not found", 404
        return render_template('edit_position.html', position=position)

@app.route('/delete_position/<req_number>', methods=['POST'])
def delete_position(req_number):
    positions = load_positions()
    positions = [pos for pos in positions if pos['REQ#'] != req_number]
    save_positions(positions)
    return redirect(url_for('home'))

def capitalize_name(name):
    return ' '.join(word.capitalize() for word in name.split())

@app.route('/add_applicant/<req_number>', methods=['POST'])
def add_applicant(req_number):
    applicants = load_applicants(req_number)

    applicant_name = capitalize_name(request.form['applicant_name'])
#    first_name, last_name = applicant_name.split(' ')[:2]
    new_applicant = {
        'Applicant Name': applicant_name,
        'Location': request.form['location'],
        'Shift': request.form['shift'],
        'Salary Expectation': request.form['salary_expectation'],
        'Interview 1 Date': request.form['interview_1_date'],
        'Interview 1 Feedback': request.form['interview_1_feedback'],
#        'Interview 2 Date': request.form['interview_2_date'],
#        'Interview 2 Feedback': request.form['interview_2_feedback'],
#        'Interview 3 Date': request.form['interview_3_date'],
#        'Interview 3 Feedback': request.form['interview_3_feedback'],
#        'Interview 4 Date': request.form['interview_4_date'],
#        'Interview 4 Feedback': request.form['interview_4_feedback'],
        'Hired': 'Yes' if 'hired' in request.form else 'No'
    }

    if 'resume' in request.files:
        resume = request.files['resume']
        if resume and allowed_file(resume.filename):
            filename = sanitize_filename(f"{first_name}_{last_name}_{req_number}{os.path.splitext(resume.filename)[1]}")
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            resume.save(file_path)
            new_applicant['Resume'] = filename
        else:
            new_applicant['Resume'] = None
    else:
        new_applicant['Resume'] = None

    # Update REQ status if an applicant is hired
    if new_applicant['Hired'] == 'Yes':
        positions = load_positions()
        for position in positions:
            if position['REQ#'] == req_number:
                position['Status'] = 'Filled'
                break
        save_positions(positions)

    applicants.append(new_applicant)
    save_applicants(req_number, applicants)

    return redirect(url_for('position', req_number=req_number))


@app.route('/resume/<path:filename>')
def get_resume(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/edit_applicant/<req_number>', methods=['GET', 'POST'])
def edit_applicant(req_number):
    if request.method == 'POST':
        applicants = load_applicants(req_number)
        applicant_name = request.form['applicant_name']
        for applicant in applicants:
            if applicant['Applicant Name'] == applicant_name:
                applicant['Location'] = request.form['location']
                applicant['Shift'] = request.form['shift']
                applicant['Salary Expectation'] = request.form['salary_expectation']
                applicant['Interview 1 Date'] = request.form['interview_1_date']
                applicant['Interview 1 Feedback'] = request.form['interview_1_feedback']
                applicant['Interview 2 Date'] = request.form['interview_2_date']
                applicant['Interview 2 Feedback'] = request.form['interview_2_feedback']
                applicant['Interview 3 Date'] = request.form['interview_3_date']
                applicant['Interview 3 Feedback'] = request.form['interview_3_feedback']
                applicant['Interview 4 Date'] = request.form['interview_4_date']
                applicant['Interview 4 Feedback'] = request.form['interview_4_feedback']
                applicant['Hired'] = 'Yes' if 'hired' in request.form else 'No'
                
                if 'resume' in request.files:
                    file = request.files['resume']
                    if file and allowed_file(file.filename):
                        filename = sanitize_filename(f"{applicant_name}_{req_number}{os.path.splitext(file.filename)[1]}")
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(file_path)
                        applicant['Resume'] = filename
                break
        
        # Update REQ status if an applicant is hired
        if any(applicant['Hired'] == 'Yes' for applicant in applicants):
            positions = load_positions()
            for position in positions:
                if position['REQ#'] == req_number:
                    position['Status'] = 'Filled'
                    break
            save_positions(positions)

        save_applicants(req_number, applicants)
        return redirect(url_for('position', req_number=req_number))
    else:
        applicants = load_applicants(req_number)
        applicant_name = request.args.get('applicant_name')
        applicant = next((app for app in applicants if app['Applicant Name'] == applicant_name), None)
        if applicant is None:
            return "Applicant not found", 404
        return render_template('edit_applicant.html', req_number=req_number, applicant=applicant)

@app.route('/delete_applicant/<req_number>/<applicant_name>', methods=['POST'])
def delete_applicant(req_number, applicant_name):
    applicants = load_applicants(req_number)
    applicants = [app for app in applicants if app['Applicant Name'] != applicant_name]
    save_applicants(req_number, applicants)
    return redirect(url_for('position', req_number=req_number))

if __name__ == '__main__':
    app.run(debug=True)
