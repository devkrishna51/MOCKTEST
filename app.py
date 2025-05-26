from flask import Flask, render_template, request, redirect, url_for, session
import os
app = Flask(__name__)
app.secret_key = 'supersecretkey123'

# File paths
TEACHERS_FILE = 'data/teacher_accounts.txt'
STUDENTS_FILE = 'data/student_accounts.txt'
QUESTIONS_FILE = 'data/questions.txt'
ANSWERS_FILE = 'data/answers.txt'

# Helper Functions
def read_accounts(filename):
    accounts = {}
    try:
        with open(filename, 'r') as f:
            for line in f:
                username, password = line.strip().split()
                accounts[username] = password
    except FileNotFoundError:
        pass
    return accounts

def add_account(filename, username, password):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'a') as f:
        f.write(f"{username} {password}\n")

def read_questions():
    questions = []
    try:
        with open(QUESTIONS_FILE, 'r') as f:
            questions = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        pass
    return questions

def add_question(q):
    with open(QUESTIONS_FILE, 'a') as f:
        f.write(q + "\n")

def clear_questions():
    open(QUESTIONS_FILE, 'w').close()

def read_answers():
    answers = {}
    try:
        with open(ANSWERS_FILE, 'r') as f:
            for line in f:
                if ':' in line:
                    student, ans = line.strip().split(':', 1)
                    answers[student] = ans.strip()
    except FileNotFoundError:
        pass
    return answers

def add_answer(student, ans_list):
    with open(ANSWERS_FILE, 'a') as f:
        f.write(f"{student}: {', '.join(ans_list)}\n")

# ---- Routes ----

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/developer', methods=['GET', 'POST'])
def developer_panel():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        teachers = read_accounts(TEACHERS_FILE)
        if username in teachers:
            return "Teacher username already exists!"
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
        return "Invalid teacher credentials!"
    return render_template('teacher_login.html')

@app.route('/teacher/panel', methods=['GET', 'POST'])
def teacher_panel():
    if 'teacher' not in session:
        return redirect(url_for('teacher_login'))

    if request.method == 'POST':
        if 'add_question' in request.form:
            question = request.form['question']
            add_question(question)

        elif 'clear_questions' in request.form:
            clear_questions()

        elif 'clear_students' in request.form:
            # Clear student accounts file
            open(STUDENTS_FILE, 'w').close()  # truncate file to zero size (delete all content)
            # Optionally, also clear answers if you want:
            open(ANSWERS_FILE, 'w').close()

    questions = read_questions()
    answers = read_answers()
    return render_template('teacher_panel.html', questions=questions, answers=answers)


@app.route('/teacher/logout')
def teacher_logout():
    session.pop('teacher', None)
    return redirect(url_for('index'))

@app.route('/student/register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        students = read_accounts(STUDENTS_FILE)
        if username in students:
            return "Student username already exists!"
        add_account(STUDENTS_FILE, username, password)
        return "Student registered! <a href='/student/login'>Login here</a>"
    return render_template('student_register.html')

@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        students = read_accounts(STUDENTS_FILE)
        if username in students and students[username] == password:
            session['student'] = username
            return redirect(url_for('student_panel'))
        return "Invalid student credentials!"
    return render_template('student_login.html')

@app.route('/student/panel', methods=['GET', 'POST'])
def student_panel():
    if 'student' not in session:
        return redirect(url_for('student_login'))

    questions = read_questions()
    if request.method == 'POST':
        answers = []
        for i in range(len(questions)):
            ans = request.form.get(f'answer_{i}', '')
            answers.append(ans)
        add_answer(session['student'], answers)
        return "Answers submitted! <a href='/student/logout'>Logout</a>"

    return render_template('student_panel.html', questions=questions)

@app.route('/student/logout')
def student_logout():
    session.pop('student', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
