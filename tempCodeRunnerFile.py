
@app.route('/report_cheating', methods=['POST'])
def report_cheating():
    if 'student' in session:
        student_name = session['student']
        add_blocked_student(student_name)
        return jsonify({'status': 'blocked'})
    return jsonify({'status': 'error', 'message': 'Student not logged in'}), 403