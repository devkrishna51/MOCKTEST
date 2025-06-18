from flask import Flask, render_template, request, redirect, url_for, session
import os
from flask import jsonify

app = Flask(__name__)
app.secret_key = 'supersecretkey123'

# File paths
DATA_DIR = 'data'
TEACHERS_FILE = os.path.join(DATA_DIR, 'teacher_accounts.txt')
STUDENTS_FILE = os.path.join(DATA_DIR, 'student_accounts.txt')
QUESTIONS_FILE = os.path.join(DATA_DIR, 'questions.txt')
ANSWERS_FILE = os.path.join(DATA_DIR, 'answers.txt')

# Helper Functions

def add_blocked_student(student_name):
    with open(ANSWERS_FILE, 'a') as f:
        f.write(f"{student_name}|BLOCKED\n")

def read_accounts(filename):
    accounts = {}
    try:
        with open(filename, 'r') as f:
            for line in f:
                parts = line.strip().split(maxsplit=1)
                if len(parts) == 2:
                    username, password = parts
                    accounts[username] = password
    except FileNotFoundError:
        pass
    return accounts

def add_account(filename, username, password):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'a') as f:
        f.write(f"{username} {password}\n")

def read_structured_questions():
    questions = []
    try:
        with open(QUESTIONS_FILE, 'r') as f:
            for line in f:
                parts = line.strip().split('|')
                if len(parts) == 6:
                    q, a, b, c, d, correct = parts
                    questions.append({
                        'q': q,
                        'options': [a, b, c, d],
                        'correct': correct.upper()
                    })
    except FileNotFoundError:
        pass
    return questions

def add_question_line(line):
    os.makedirs(os.path.dirname(QUESTIONS_FILE), exist_ok=True)
    with open(QUESTIONS_FILE, 'a') as f:
        f.write(line + "\n")

def clear_questions():
    open(QUESTIONS_FILE, 'w').close()

def read_answers():
    answers = {}
    try:
        with open(ANSWERS_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                if ':' in line:
                    student, ans = line.split(':', 1)
                    student = student.strip()
                    ans = ans.strip()

                    
                    if ans == 'BLOCKED':
                        answers[student] = 'BLOCKED'
                        continue

                    
                    ans_list = []
                    for pair in ans.split(','):
                        pair = pair.strip()
                        if '|' in pair:
                            answer_text, score = pair.split('|', 1)
                            ans_list.append((answer_text.strip(), score.strip()))
                        else:
                            ans_list.append((pair.strip(), '0'))
                    answers[student] = ans_list
    except FileNotFoundError:
        pass
    return answers


def add_answer(student, ans_list, score_list):
    os.makedirs(os.path.dirname(ANSWERS_FILE), exist_ok=True)
    with open(ANSWERS_FILE, 'a') as f:
        f.write(f"{student}: " + ', '.join([f"{a}|{s}" for a, s in zip(ans_list, score_list)]) + "\n")

# Routes


@app.route('/report_cheating', methods=['POST'])
def report_cheating():
    if 'student' in session:
        student_name = session['student']
        add_blocked_student(student_name)
        return jsonify({'status': 'blocked'})
    return jsonify({'status': 'error', 'message': 'Student not logged in'}), 403
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

    questions = read_structured_questions()
    answers = read_answers()

    if request.method == 'POST':
        # Add new question
        if 'add_question' in request.form:
            q = request.form['question'].strip()
            optA = request.form['option_a'].strip()
            optB = request.form['option_b'].strip()
            optC = request.form['option_c'].strip()
            optD = request.form['option_d'].strip()
            correct = request.form['correct_option'].strip().upper()

            if q and optA and optB and optC and optD and correct in ['A', 'B', 'C', 'D']:
                add_question_line(f"{q}|{optA}|{optB}|{optC}|{optD}|{correct}")
                questions = read_structured_questions()  # refresh after adding

        # Delete all questions
        elif 'clear_questions' in request.form:
            clear_questions()
            questions = []  

        # Delete all students and their answers
        elif 'clear_students' in request.form:
            open(STUDENTS_FILE, 'w').close()
            open(ANSWERS_FILE, 'w').close()
            answers = {}

        # Delete selected questions using checkbox
        elif 'delete_selected' in request.form:
            indices_to_delete = request.form.getlist('delete_questions')
            indices_to_delete = list(map(int, indices_to_delete))

            questions = [q for i, q in enumerate(questions) if i not in indices_to_delete]

            # Overwrite updated questions
            with open(QUESTIONS_FILE, 'w') as f:
                for q in questions:
                    f.write(f"{q['q']}|{q['options'][0]}|{q['options'][1]}|{q['options'][2]}|{q['options'][3]}|{q['correct']}\n")

    return render_template('teacher_panel.html', questions=questions, answers=answers, enumerate=enumerate)


@app.route('/teacher/logout')
def teacher_logout():
    session.pop('teacher', None)
    return redirect(url_for('projects'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('projects'))

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

    student_name = session['student']
    questions = read_structured_questions()
    answers = read_answers()
    student_answers = answers.get(student_name)

    # ✅ Blocked student check
    if student_answers == 'BLOCKED':
        return "⚠️ You have been blocked from submitting the test. <a href='/student/logout'>Logout</a>"

    # ✅ Student trying to submit answers
    if request.method == 'POST':
        if student_answers is not None:
            return "❗You have already submitted your answers. <a href='/student/logout'>Logout</a>"

        submitted_answers = []
        score_list = []
        incorrect_list = []

        for i, q in enumerate(questions):
            selected = request.form.get(f'answer_{i}', '').strip().upper()
            submitted_answers.append(selected)

            if selected == q['correct']:
                score_list.append('1')
            else:
                score_list.append('0')
                incorrect_list.append({
                    'question': q['q'],
                    'your_answer': selected if selected else "Not Answered",
                    'correct_answer': q['correct'],
                    'options': q['options']
                })

        add_answer(student_name, submitted_answers, score_list)
        session['show_incorrect'] = incorrect_list  # temp store
        return redirect(url_for('student_panel'))

    #  Already submitted, show score & incorrect
    if student_answers is not None:
        total_score = sum(int(score) for _, score in student_answers)
        incorrect_list = session.pop('show_incorrect', [])
        return render_template('student_panel.html', 
                                  score=total_score,
    questions=questions,
    student_answers=student_answers,
    incorrect_list=incorrect_list,
    block_message=None
)

    # First time, no submission
    return render_template('student_panel.html',
                           score=None,
                           questions=questions,
                           student_answers=None,
                           incorrect_list=[])




@app.route('/student/logout')
def student_logout():
    session.pop('student', None)
    return redirect(url_for('projects'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
