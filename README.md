PDF Quiz Generator
PDF Quiz Generator is a Flask-based web application that allows users to upload PDF files, analyze their content, and perform several actions such as summarizing content, generating multiple-choice questions, and interacting with the content via a chat interface.
Features
1. **Upload PDF**: Users can upload a PDF file to extract its content.
2. **Summarization**: Generates a concise summary of the PDF content using the Groq Cloud API.
3. **Question Generation**: Allows users to specify the number of questions to generate based on the PDF content.
4. **Chat with PDF**: Provides a chat interface for querying the uploaded PDF content.
Technologies Used
- **Backend**: Flask, PyPDF2, Flask-Session
- **Frontend**: HTML, Bootstrap 4, JavaScript
- **API Integration**: Groq Cloud API for summarization, question generation, and answering queries
File Structure
```
Project/
├── .venv/                  # Virtual environment
├── flask_session/          # Flask session files
├── static/                 # Static assets (if any)
├── templates/              # HTML templates
│   ├── index.html          # Upload page
│   ├── result.html         # Result page
├── uploads/                # Directory for uploaded PDF files
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
```
Installation and Setup
Follow these steps to set up the project on your local machine:
Prerequisites
- Python 3.8+
- Flask
- Virtual Environment (optional but recommended)
Steps
1. Clone the repository:
```bash
git clone https://github.com/yourusername/pdf-quiz-generator.git
cd pdf-quiz-generator
```
2. Set up a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
```
3. Install the required dependencies:
```bash
pip install -r requirements.txt
```
4. Create the `uploads/` directory:
```bash
mkdir uploads
```
5. Update the API key:
- Replace `your_secret_key_here` and `API_KEY` in `app.py` with your Groq Cloud API key.
6. Run the application:
```bash
python app.py
```
7. Open your browser and navigate to:
```
http://127.0.0.1:5000
```
Usage
1. **Upload a PDF**: Start by uploading a PDF file using the provided form.
2. **View the Summary**: After processing, view the summary of the PDF on the results page.
3. **Generate Questions**: Specify the number of questions you want to generate, and they will appear on the results page.
4. **Chat with PDF**: Use the chat interface to ask questions about the uploaded content and get answers.
API Key


Future Enhancements
- Support for OCR to handle image-based PDFs.
- Improved error handling for invalid or corrupted PDFs.
- Enhanced UI for a better user experience.
License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
Author
MORSHED MD MONOARUL
