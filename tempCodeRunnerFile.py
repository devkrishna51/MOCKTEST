@app.route("/olevel/<subject>/<topic>/set<int:set_id>")
def quiz_topic(subject, topic, set_id):
    folder = safe_folder_name(topic)
    file_path = f"data/{subject}/{folder}/set{set_id}.txt"
    
    if not os.path.exists(file_path):
        return f"Set file not found for {topic} - Set {set_id}", 404

    # ✅ Read questions from file (example logic)
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    questions = []
    for line in lines:
        parts = line.strip().split('|')
        if len(parts) == 5:
            questions.append({
                'question': parts[0],
                'options': parts[1:5]
            })

    return render_template("quiz_form.html", subject=subject, topic=topic, set_id=set_id, questions=questions)