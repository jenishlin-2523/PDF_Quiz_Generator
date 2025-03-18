from flask import Flask, request, render_template, jsonify, session, redirect, url_for
import os
import requests
import json
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
from flask_session import Session

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configure session settings
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Dummy user data for login
users = {
    "student1": {"password": "pass123", "role": "student"},
    "staff1": {"password": "staff123", "role": "staff"}
}

API_KEY = "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"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def call_groq_api(content, system_prompt="Summarize the following content"):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ]
    }
    response = requests.post(GROQ_API_URL, json=payload, headers=headers)
    try:
        response_data = response.json()
        return response_data
    except Exception as e:
        print(f"Error parsing API response: {e}")
        return {}

def extract_text_from_pdf(file_path):
    reader = PdfReader(file_path)
    text = "".join([page.extract_text() or "" for page in reader.pages])
    return text

@app.route('/')
def home():
    return redirect(url_for('login'))  # Redirect to login page initially

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Dummy credentials for testing
        valid_users = {
            "staff": {"password": "staff123", "role": "staff"},
            "student": {"password": "student123", "role": "student"}
        }

        user_data = valid_users.get(username)
        
        if user_data and user_data["password"] == password:
            session['user'] = username  # Store username in session
            session['role'] = user_data["role"]  # Store role in session
            # Redirect to corresponding dashboard based on user role
            if user_data["role"] == "staff":
                return redirect(url_for('staff_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            return "Invalid Credentials. Try again!"  # If login fails
    return render_template('login.html')  # Render the login form on GET request

@app.route('/student_dashboard')
def student_dashboard():
    if 'user' not in session or session['role'] != 'student':
        return redirect(url_for('login'))  # Redirect to login page if not logged in
    return render_template('student_dashboard.html', user=session['user'])  # Render student dashboard

@app.route('/staff_dashboard', methods=['GET', 'POST'])
def staff_dashboard():
    if request.method == 'POST':
        # Check if the quiz is uploaded as a JSON file
        file = request.files['quiz_file']
        if file:
            try:
                # Load the uploaded quiz data from the JSON file
                quiz_data = json.load(file)
                session['uploaded_quiz'] = quiz_data  # Store the quiz in session or database
                
                # You can also store it in the database for persistence
                # db.save_quiz_data(quiz_data)  # If you're using a database

                # Redirect back to the staff dashboard to confirm the upload
                return redirect(url_for('staff_dashboard'))
            except Exception as e:
                # Handle any exceptions while loading the file
                return f"Error uploading quiz: {e}"

    # Render the staff dashboard page
    return render_template('staff_dashboard.html')


@app.route('/logout')
def logout():
    session.pop('user', None)  # Remove user from session
    session.pop('role', None)  # Remove role from session
    return redirect(url_for('login'))  # Redirect to login page after logout

@app.route('/upload', methods=['POST'])
def upload_pdf():
    if 'pdf' not in request.files:
        return "No file part"

    file = request.files['pdf']

    if file.filename == '':
        return "No selected file"

    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        pdf_text = extract_text_from_pdf(file_path)
        session['pdf_text'] = pdf_text  

        summary_response = call_groq_api(pdf_text, system_prompt="Summarize the following content")
        summary = summary_response.get('choices', [{}])[0].get('message', {}).get('content', "Summary could not be generated.")
        session['summary'] = summary

        return render_template('result.html', summary=summary, content=pdf_text)

@app.route('/generate_dynamic_questions', methods=['POST'])
def generate_dynamic_questions():
    quantity = int(request.form['quantity'])
    content = session.get('pdf_text', '')

    if not content:
        return "PDF content not found in session"

    question_prompt = f"""
    Generate {quantity} multiple-choice questions from the given text.
    Each question should have 4 options (A, B, C, D) and a correct answer.
    Return the result in a structured JSON format like this:
    {{
        "questions": [
            {{
                "question": "What is AI?",
                "options": {{"A": "Artificial Intelligence", "B": "Animal Intelligence", "C": "Automatic Input", "D": "Analog Interface"}},
                "answer": "A"
            }},
            ...
        ]
    }}
    Only return JSON. No extra text.
    """

    questions_response = call_groq_api(content, system_prompt=question_prompt)

    questions_raw = questions_response.get('choices', [{}])[0].get('message', {}).get('content', "")

    try:
        questions_data = json.loads(questions_raw)
        questions_list = questions_data.get("questions", [])  

        questions = [{ "question": q["question"], "options": q["options"] } for q in questions_list]
        correct_answers = { q["question"]: q["answer"] for q in questions_list }

        session['quiz_questions'] = questions
        session['correct_answers'] = correct_answers  

        return render_template('quiz.html', questions=questions)

    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        return "Error in generating questions. The API response was not valid JSON."


@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    user_answers = request.form
    correct_answers = session.get('correct_answers', {})

    score = sum(1 for question, user_answer in user_answers.items() if correct_answers.get(question) == user_answer)
    total = len(correct_answers)

    return render_template('quiz_result.html', score=score, total=total)

@app.route('/chat', methods=['POST'])
def chat_with_pdf():
    try:
        query = request.form.get('query', '').strip()
        content = session.get('pdf_text', '').strip()

        if not query:
            return jsonify({'error': 'Query cannot be empty.'})
        if not content:
            return jsonify({'error': 'Content is required to generate a response.'})

        chat_prompt = f"Answer the question based on the following content: {content}\n\nQuestion: {query}"
        response = call_groq_api(content=chat_prompt, system_prompt="Provide an accurate and concise answer.")

        answer = response.get('choices', [{}])[0].get('message', {}).get('content', 'No answer found.')
        return jsonify({'answer': answer})

    except Exception as e:
        return jsonify({'error': 'An error occurred while processing your request. Please try again.'})

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    # If accessed from dashboard, use the questions stored in session
    questions = session.get('quiz_questions', [])
    if not questions:
        return redirect(url_for('student_dashboard'))  # Redirect if no quiz questions exist in session

    return render_template('quiz.html', questions=questions, from_dashboard=False)


if __name__ == '__main__':
    app.run(debug=True)
