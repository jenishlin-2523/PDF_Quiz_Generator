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
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

API_KEY = "put your API key here"
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
    print(f"Calling API: {GROQ_API_URL} with payload: {payload}")
    response = requests.post(GROQ_API_URL, json=payload, headers=headers)
    try:
        response_data = response.json()
        print(f"API Response: {response_data}")
        return response_data
    except Exception as e:
        print(f"Error parsing API response: {e}")
        return {}

def extract_text_from_pdf(file_path):
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
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

        # Save the content in the session
        session['pdf_text'] = pdf_text

        # Summarize the content using Groq Cloud API
        summary_response = call_groq_api(pdf_text, system_prompt="Summarize the following content")

        # Extract the summary from the response
        summary = summary_response.get('choices', [{}])[0].get('message', {}).get('content', "Summary could not be generated.")
        session['summary'] = summary

        return render_template('result.html', summary=summary, content=pdf_text, qa_pairs=[])

@app.route('/generate_dynamic_questions', methods=['POST'])
def generate_dynamic_questions():
    quantity = int(request.form['quantity'])
    content = session.get('pdf_text', '')

    if not content:
        return "PDF content not found in session"

    question_prompt = f"Generate {quantity} questions based on the following content."
    questions_response = call_groq_api(content, system_prompt=question_prompt)

    # Extract questions from the response
    questions_raw = questions_response.get('choices', [{}])[0].get('message', {}).get('content', "")
    questions = questions_raw.split('\n')

    return render_template('result.html', dynamic_questions=questions, summary=session.get('summary', ''), content=content)

@app.route('/chat', methods=['POST'])
def chat_with_pdf():
    try:
        # Extract query and content from the form
        query = request.form.get('query', '').strip()
        content = session.get('pdf_text', '').strip()

        if not query:
            return jsonify({'error': 'Query cannot be empty.'})

        if not content:
            return jsonify({'error': 'Content is required to generate a response.'})

        # Generate the prompt for the API
        chat_prompt = f"Answer the question based on the following content: {content}\n\nQuestion: {query}"
        response = call_groq_api(content=chat_prompt, system_prompt="Provide an accurate and concise answer based on the content.")

        # Extract the answer from the API response
        answer = response.get('choices', [{}])[0].get('message', {}).get('content', 'No answer found.')

        return jsonify({'answer': answer})

    except Exception as e:
        print(f"Error in chat_with_pdf: {e}")
        return jsonify({'error': 'An error occurred while processing your request. Please try again.'})

if __name__ == '__main__':
    app.run(debug=True)
