from flask import Flask, request, render_template, jsonify, session
import os
import requests
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
from flask_session import Session

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configure session settings
app.config['SECRET_KEY'] = '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'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

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
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

@app.route('/')
def index():
    return render_template('index.html')

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

        # Extract text from PDF
        pdf_text = extract_text_from_pdf(file_path)
        session['pdf_text'] = pdf_text  # Store in session

        # Summarize content using Groq Cloud API
        summary_response = call_groq_api(pdf_text, system_prompt="Summarize the following content")
        summary = summary_response.get('choices', [{}])[0].get('message', {}).get('content', "Summary could not be generated.")
        session['summary'] = summary

        return render_template('result.html', summary=summary, content=pdf_text)

import json

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

    # Call Groq API
    questions_response = call_groq_api(content, system_prompt=question_prompt)

    # Extract response text
    questions_raw = questions_response.get('choices', [{}])[0].get('message', {}).get('content', "")

    # Try to parse the response as JSON
    try:
        questions_data = json.loads(questions_raw)  # Convert text to JSON
        questions_list = questions_data.get("questions", [])  # Extract question list
        
        # Store questions & answers separately in the session
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
    user_answers = request.form  # {question: selected_answer}
    correct_answers = session.get('correct_answers', {})  # Retrieve stored answers

    score = 0
    total = len(correct_answers)

    for question, user_answer in user_answers.items():
        if correct_answers.get(question) == user_answer:
            score += 1

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

if __name__ == '__main__':
    app.run(debug=True)
