from flask import Flask, render_template, request, redirect, url_for, session
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey123'

# File paths
DATA_DIR = 'data'
TEACHERS_FILE = os.path.join(DATA_DIR, 'teacher_accounts.txt')
STUDENTS_FILE = os.path.join(DATA_DIR, 'student_accounts.txt')
QUESTIONS_FILE = os.path.join(DATA_DIR, 'questions.txt')
ANSWERS_FILE = os.path.join(DATA_DIR, 'answers.txt')

# Helper Functions
def read_accounts(filename):
    accounts = {}
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(maxsplit=1)
                if len(parts) == 2:
                    username, password = parts
                    accounts[username] = password
    except FileNotFoundError:
        print(f"File {filename} not found, returning empty dict.")
    return accounts

def add_account(filename, username, password):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'a') as f:
        f.write(f"{username} {password}\n")
    print(f"Added account '{username}' to {filename}")

def read_questions():
    questions = []
    try:
        with open(QUESTIONS_FILE, 'r') as f:
            questions = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Questions file {QUESTIONS_FILE} not found.")
    print(f"Loaded questions: {questions}")
    return questions

def add_question(q):
    os.makedirs(os.path.dirname(QUESTIONS_FILE), exist_ok=True)
    with open(QUESTIONS_FILE, 'a') as f:
        f.write(q + "\n")
    print(f"Added question: {q}")

def clear_questions():
    open(QUESTIONS_FILE, 'w').close()
    print("Cleared all questions")

def read_answers():
    answers = {}
    try:
        with open(ANSWERS_FILE, 'r') as f:
            for line in f:
                if ':' in line:
                    student, ans = line.strip().split(':', 1)
                    ans_list = []
                    for pair in ans.split(','):
                        pair = pair.strip()
                        if '|' in pair:
                            answer_text, score = pair.split('|', 1)
                            ans_list.append( (answer_text.strip(), score.strip()) )
                        else:
                            ans_list.append( (pair.strip(), '0') )
                    answers[student.strip()] = ans_list
    except FileNotFoundError:
        print(f"Answers file {ANSWERS_FILE} not found.")
    return answers

def add_answer(student, ans_list):
    os.makedirs(os.path.dirname(ANSWERS_FILE), exist_ok=True)
    with open(ANSWERS_FILE, 'a') as f:
        f.write(f"{student}: " + ', '.join([f"{a}|0" for a in ans_list]) + "\n")

# ---- Routes ----

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/projects')
def projects():
    return render_template('main_2.html')

@app.route('/developer', methods=['GET', 'POST'])
def developer_panel():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        teachers = read_accounts(TEACHERS_FILE)
        if username in teachers:
            return "Teacher username already exists! <a href='/'>Go Home</a>"
        add_account(TEACHERS_FILE, username, password)
        return "Teacher account created successfully! <a href='/'>Go Home</a>"
    return render_template('dev_panel.html')

@app.route('/teacher/login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        teachers = read_accounts(TEACHERS_FILE)
        if username in teachers and teachers[username] == password:
            session['teacher'] = username
            return redirect(url_for('teacher_panel'))
        return "Invalid teacher credentials! <a href='/teacher/login'>Try Again</a>"
    return render_template('teacher_login.html')

@app.route('/teacher/panel', methods=['GET', 'POST'])
def teacher_panel():
    if 'teacher' not in session:
        return redirect(url_for('teacher_login'))

    if request.method == 'POST':
        if 'add_question' in request.form:
            question = request.form['question'].strip()
            if question:
                add_question(question)

        elif 'clear_questions' in request.form:
            clear_questions()

        elif 'clear_students' in request.form:
            open(STUDENTS_FILE, 'w').close()
            open(ANSWERS_FILE, 'w').close()
            print("Cleared all students and answers")

        elif 'submit_score' in request.form:
            student_name = request.form['student_name']
            answer_index = int(request.form['answer_index'])
            score = request.form['score']

            answers = read_answers()
            if student_name in answers:
                ans_score_list = answers[student_name]
                answer_text, _ = ans_score_list[answer_index]
                ans_score_list[answer_index] = (answer_text, score)

                with open(ANSWERS_FILE, 'w') as f:
                    for student, ans_list in answers.items():
                        line_parts = [f"{a}|{s}" for a, s in ans_list]
                        f.write(f"{student}: {', '.join(line_parts)}\n")
            return redirect(url_for('teacher_panel'))

    questions = read_questions()
    answers = read_answers()
    return render_template('teacher_panel.html', questions=questions, answers=answers, enumerate=enumerate)
@app.before_request
def log_ip_address():
    if "X-Forwarded-For" in request.headers:
        ip = request.headers.getlist("X-Forwarded-For")[0].split(',')[0].strip()
    else:
        ip = request.remote_addr
    print(f"[{request.method}] {request.path} - IP: {ip}")
@app.before_request
def log_ip_address():
    ip = request.remote_addr
    print(f"[{request.method}] {request.path} - IP: {ip}")
    
@app.route('/teacher/logout')
def teacher_logout():
    session.pop('teacher', None)
    return redirect(url_for('projects'))  # Redirect to main_2.html

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('projects'))  # Redirect to main_2.html

@app.route('/student/register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        students = read_accounts(STUDENTS_FILE)
        if username in students:
            return "Student username already exists! <a href='/student/register'>Try Again</a>"
        add_account(STUDENTS_FILE, username, password)
        return "Student registered! <a href='/student/login'>Login here</a>"
    return render_template('student_register.html')

@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        students = read_accounts(STUDENTS_FILE)
        if username in students and students[username] == password:
            session['student'] = username
            return redirect(url_for('student_panel'))
        return "Invalid student credentials! <a href='/student/login'>Try Again</a>"
    return render_template('student_login.html')

@app.route('/student/panel', methods=['GET', 'POST'])
def student_panel():
    if 'student' not in session:
        return redirect(url_for('student_login'))

    questions = read_questions()
    answers = read_answers()

    student_name = session['student']
    student_answers = answers.get(student_name)

    if request.method == 'POST':
        if student_answers is not None:
            return "You have already submitted your answers. <a href='/student/logout'>Logout</a>"

        answers_list = []
        for i in range(len(questions)):
            ans = request.form.get(f'answer_{i}', '').strip()
            answers_list.append(ans)
        add_answer(student_name, answers_list)
        return "Answers submitted! <a href='/student/logout'>Logout</a>"

    if student_answers is not None:
        total_score = sum(int(score) for _, score in student_answers)
        return render_template('student_panel.html', score=total_score, questions=questions, student_answers=student_answers)
    else:
        return render_template('student_panel.html', score=None, questions=questions, student_answers=None)

@app.route('/student/logout')
def student_logout():
    session.pop('student', None)
    return redirect(url_for('projects'))  # Redirect to main_2.html

if __name__ == '__main__':
    app.run(debug=True)
