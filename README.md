# 📄 AI Resume Architect (Agentic Resume Tailor)

An AI-powered application that acts as your personal technical recruiter and resume writer. It automatically tailors your master resume data to specific Job Descriptions (JDs), generating highly relevant, targeted resumes, cover letters, and outreach emails.

## ✨ Features

- **JD Analysis:** Extracts core requirements, domains, and must-have skills from any job description.
- **Smart Skill Filtering:** Selects and categorizes your skills that strictly match or complement the JD.
- **Experience Tailoring:** Rewrites and selects your most relevant professional experience bullets using the XYZ format (Accomplished [X] as measured by [Y], by doing [Z]).
- **Project Selection:** Highlights the best personal or academic projects based on the job requirements.
- **Multi-Model Support:** Choose between various AI models (e.g., Llama 3.3 70B, Llama 3.1 8B) for fast or high-quality generations.
- **PDF Generation:** Automatically generates a beautifully formatted LaTeX/PDF resume tailored to the job.

## 🏗️ Architecture

This project is split into two main components:
1. **FastAPI Backend:** Handles all the prompt engineering, data processing, and LLM communication.
2. **Streamlit Frontend:** A clean, user-friendly web interface to paste JDs, select models, and download generated assets.

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- API Keys (e.g., Groq API for Llama models)

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/resume-creator-agent.git
cd resume-creator-agent
```

### 2. Set up a virtual environment and install dependencies
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
pip install -r requirements.txt
```
*(Note: If you don't have a `requirements.txt` yet, you can create one using `pip freeze > requirements.txt`)*

### 3. Configure your Environment Variables
Create a `.env` file in the root directory and add your API keys. 
```env
GROQ_API_KEY=your_groq_api_key_here
```
> ⚠️ **Important:** Never commit your `.env` file to version control. It is already included in the `.gitignore`.

### 4. Set up your Master Data
Create a `my_data.json` file in the `data/` folder (e.g., `data/my_data.json`). This file acts as your "Master Resume" containing all your skills, experiences, and projects. 

The AI will selectively extract and rewrite content from this file. 

Example structure:
```json
{
  "personal": {
    "name": "Your Name",
    "email": "you@email.com",
    "github": "https://github.com/yourusername"
  },
  "skills": ["Python", "Java", "Docker"],
  "experience": [ ... ],
  "education": [ ... ],
  "projects": [ ... ]
}
```
> ⚠️ **Important:** `my_data.json` is ignored by git to protect your personal information.

## 💻 Usage

You need to run both the backend and frontend simultaneously.

### Start the Backend
Open a terminal and run the backend startup script:
```bash
sh run.sh
```
*(Alternatively, you can run the FastAPI server directly via `uvicorn app.main:app --reload`)*

### Start the Frontend
Open a second terminal, activate your virtual environment, and start Streamlit:
```bash
streamlit run frontend/app.py
```

1. Open the provided Local URL (usually `http://localhost:8501`) in your browser.
2. Paste the Job Description into the text area.
3. Select your preferred AI model from the sidebar.
4. Click **Generate Resume** and wait for the AI to process your application.
5. View and download your tailored PDF resume!

## 📝 License
This project is open-source and available under the MIT License.
