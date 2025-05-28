from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey123'

# PostgreSQL connection details (tumhare hisaab se update karna)
DB_HOST = 'dpg-d0rcppndiees73bth020-a.oregon-postgres.render.com'
DB_NAME = 'krishnabd'
DB_USER = 'krishna_web'
DB_PASS = 'Qg2ftttZMH7KrUtwReA9QYa2zkbf19zw'

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    return conn

# Helper functions - ab file ke bajaye DB me kaam karenge

def read_accounts(table):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT username, password FROM {table};")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {username: password for username, password in rows}

def add_account(table, username, password):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"INSERT INTO {table} (username, password) VALUES (%s, %s);", (username, password))
    conn.commit()
    cur.close()
    conn.close()

def read_questions():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT question_text FROM questions ORDER BY id;")
    questions = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return questions

def add_question(question):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO questions (question_text) VALUES (%s);", (question,))
    conn.commit()
    cur.close()
    conn.close()

def clear_questions():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM questions;")
    conn.commit()
    cur.close()
    conn.close()

def read_answers():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT student_username, answers FROM answers;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {student: ans for student, ans in rows}

def add_answer(student_username, answers_list):
    answers_str = ', '.join(answers_list)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO answers (student_username, answers) VALUES (%s, %s);", (student_username, answers_str))
    conn.commit()
    cur.close()
    conn.close()

# ---- Flask routes same as before, but now database backed ----

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/developer', methods=['GET', 'POST'])
def developer_panel():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        teachers = read_accounts('teachers')
        if username in teachers:
            return "Teacher username already exists!"
        add_account('teachers', username, password)
        return "Teacher account created successfully! <a href='/'>Go Home</a>"
    return render_template('dev_panel.html')

@app.route('/teacher/login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        teachers = read_accounts('teachers')
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
            # Clear students and answers tables
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM students;")
            cur.execute("DELETE FROM answers;")
            conn.commit()
            cur.close()
            conn.close()

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
        students = read_accounts('students')
        if username in students:
            return "Student username already exists!"
        add_account('students', username, password)
        return "Student registered! <a href='/student/login'>Login here</a>"
    return render_template('student_register.html')

@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        students = read_accounts('students')
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
