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