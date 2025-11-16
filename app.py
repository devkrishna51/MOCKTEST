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

# Helper Functionsimport chardet


        
def load_questions(subject, set_id, topic=None):
    questions = []
    try:
        if topic:
            topic = topic.lower().replace(" ", "_").replace("-", "").replace("–", "").replace("&", "and")
            file_path = os.path.join(DATA_DIR, 'olevel', subject, topic, f'set{set_id}.txt')
        else:
            file_path = os.path.join(DATA_DIR, subject, f'set{set_id}.txt')

        print("📂 Loading questions from:", file_path)

        with open(file_path, 'r', encoding='utf-8-sig') as f:
            for line in f:
                parts = line.strip().split('|')
                if len(parts) == 6:
                    q, a, b, c, d, correct = parts
                    questions.append({
                        'q': q,
                        'options': [a, b, c, d],
                        'correct': correct.strip().upper()
                    })

    except Exception as e:
        print("❌ Error reading file:", e)

    return questions

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

@app.route("/olevel")
def olevel_home():
    return render_template("olevel.html")
@app.route("/olevel/<subject>")
def olevel_subject(subject):
    topics = {
        'm1': ['Introduction to computer', 'Introduction to Operating System' , 'Libre Office Writer' ,'Libre Office Calc' ,'Libre Office Impress', 'Introduction to Internet & WWW', 'Internet, Email & Networking'],
        'm2': ['Introduction to Web Design', 'Editors' ,'HTML Basics' ,'Cascading Style Sheets (CSS)', 'CSS Framework' ,'JavaScript and Angular JS','Photo Editor'],
        'm3': ['Introduction to Programming', 'Algorithm and Flowcharts to solve problems' , 'Introduction to Python' ,'Operators, Expressions and Python Statements' ,'Sequence data types' ,'Functions','File Processing','Modules' ,'NumPy Basics'],
        'm4': ['Introduction to IoT – Applications/Devices, Protocols and Communication Model', 'Things and Connections' , 'Sensors, Actuators and Microcontrollers', 'Building IoT Applications' , 'Security and Future of IoT Ecosystem' ,'Soft skills-Personality Development']
    }
    return render_template("olevel_topics.html", subject=subject.upper(), topics=topics.get(subject, []))

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

@app.route('/olevel/quiz/<subject>/<topic>/<int:set_id>', methods=['GET', 'POST'])
def olevel_quiz(subject, topic, set_id):
    file_path = os.path.join(DATA_DIR, 'olevel', subject, topic, f'set{set_id}.txt')
    questions = []

    # Simple question loading (without flash)
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('|')
            if len(parts) == 6:
                q, a, b, c, d, correct = parts
                questions.append({
                    'q': q,
                    'options': [a, b, c, d],
                    'correct': correct.strip().upper()
                })

    # Step 1: Name & Age Form
    if request.method == 'POST':
        if 'student_name' in request.form and 'student_age' in request.form:
            student_name = request.form['student_name']
            student_age = request.form['student_age']

            return render_template('quiz_form.html',
                                   subject=subject,
                                   topic=topic,
                                   set_id=set_id,
                                   student_name=student_name,
                                   student_age=student_age,
                                   questions=questions)

        # Step 2: Quiz Submission
        elif 'student_name_hidden' in request.form:
            student_name = request.form.get('student_name_hidden', 'Unknown')
            student_age = request.form.get('student_age_hidden', 'N/A')

            student_answers = []
            score = 0
            incorrect = []

            for i, q in enumerate(questions):
                ans = request.form.get(f'q{i}', '').strip().upper()
                student_answers.append(ans)
                if ans == q['correct']:
                    score += 1
                else:
                    incorrect.append({
                        'question': q['q'],
                        'your_answer': ans if ans else "Not Answered",
                        'correct_answer': q['correct'],
                        'options': q['options']
                    })

            return render_template('quiz_result.html',
                                   student_name=student_name,
                                   student_age=student_age,
                                   score=score,
                                   total=len(questions),
                                   incorrect_answers=incorrect)

    # GET request: first load of form
    return render_template('quiz_form.html',
                           subject=subject,
                           topic=topic,
                           set_id=set_id)





@app.route('/projects')
def projects():
    return render_template('main_2.html')

DEVELOPER_ID = "KRISHNADEV"
DEVELOPER_PASS = "Seth@#$1709"

@app.route('/dev_authen' , methods =['GET' , 'POST'])
def dev_authen():
    user = request.form.get('username')
    passw = request.form.get('password')
    if(user == DEVELOPER_ID and passw == DEVELOPER_PASS):
         return render_template('dev_panel.html')
    else :
        return render_template('main_2.html')
    
@app.route('/dev_auth', methods=['POST'])
def dev_auth():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        teachers = read_accounts(TEACHERS_FILE)
        if username in teachers:
            return "Teacher username already exists! <a href='/'>Go Home</a>"
        add_account(TEACHERS_FILE, username, password)
        return "Teacher account created successfully! <a href='/'>Go Home</a>"
    return render_template('main_2.html')


@app.route('/developer', methods=['GET', 'POST'])
def developer_panel():
    return render_template('dev_authentication.html')
    

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
        return "⚠︝ You have been blocked from submitting the test. <a href='/student/logout'>Logout</a>"

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


@app.route('/quiz/<subject>/<int:set_id>', methods=['GET', 'POST'])
def quiz(subject, set_id):
    if request.method == 'POST':
        # Step 1: Check if student is submitting name & age (initial form)
        if 'student_name' in request.form and 'student_age' in request.form:
            student_name = request.form['student_name']
            student_age = request.form['student_age']
            questions = load_questions(subject, set_id)  # ✅ Reload questions here

            return render_template('quiz_form.html',
                                   subject=subject,
                                   set_id=set_id,
                                   student_name=student_name,
                                   student_age=student_age,
                                   questions=questions)

        else:
            # Step 2: Answers are being submitted
            student_name = request.form.get('student_name_hidden', 'Unknown')
            student_age = request.form.get('student_age_hidden', 'N/A')
            questions = load_questions(subject, set_id)  # ✅ Reload questions again

            student_answers = []
            score = 0
            incorrect = []

            for i, q in enumerate(questions):
                ans = request.form.get(f'q{i}', '')
                student_answers.append(ans)
                if ans == q['correct']:
                    score += 1
                else:
                    incorrect.append({
                        'question': q['q'],
                        'your_answer': ans if ans else "Not Answered",
                        'correct_answer': q['correct'],
                        'options': q['options']
                    })

            return render_template('quiz_result.html',
                                   student_name=student_name,
                                   student_age=student_age,
                                   score=score,
                                   total=len(questions),
                                   incorrect_answers=incorrect)

    # Step 3: First GET request, show name/age form
    questions = load_questions(subject, set_id)
    return render_template('quiz_form.html',
                           subject=subject,
                           set_id=set_id,
                           student_name=None,
                           student_age=None,
                           questions=questions)


@app.route('/student/logout')
def student_logout():
    session.pop('student', None)
    return redirect(url_for('projects'))

@app.route('/subject/<subject_name>')
def subject_page(subject_name):
    template_name = f'subject_{subject_name}.html'
    print(f"Trying to render: {template_name}")
    try:
        return render_template(template_name)
    except Exception as e:
        print(f"Error: {e}")
        return f"Subject page not found for: {template_name}", 404


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
