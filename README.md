# 🧠 Automated Interview Preparation Coach  
An AI-powered, cross-platform interview practice system that evaluates your responses using **speech analysis**, **semantic understanding**, and **domain-based question generation**.
## Getting Started

1. Clone the repository:

   git clone https://github.com/Arushi06k/Interview-Preparation-Coach.git
2. Browse the folders and open the relevant language or topic you want to practice.

## Usage

- Use the practice plans to structure daily study.
- Attempt problems in a dedicated editor or coding platform, then review the provided solutions.
- Add your own notes, solutions, and resources as you learn.

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a branch for your change (e.g., feature/add-python-solutions).
3. Commit your changes with clear messages.
4. Open a pull request describing your additions.

Please include tests or examples where appropriate and ensure content is well-formatted and explained.

---

## 🚀 Features

### 🎤 Voice-Based Interview
- Real-time microphone recording
- Speech-to-text conversion using STT engines
- Text-to-speech (TTS) for delivering questions

### 🧠 Smart AI Evaluation
- **Semantic Scoring** using SBERT MiniLM embeddings  
- **Keyword Matching** with SpaCy PhraseMatcher  
- **Delivery Evaluation**: fluency, readability, fillers, clarity  
- **Final Hybrid Score** (Content + Communication)

### 📚 Domain-Based Questioning
- Curated dataset of **1650 interview questions**
- 11 domains, 3 difficulty levels  
- Follow-up question support  
- Resume-based domain suggestion (optional)

### 📊 Detailed Feedback Dashboard
- Question-wise score breakdown  
- Strengths & weaknesses  
- Improvement suggestions  
- Data visualizations

### 📱 Cross-Platform Frontend (Flutter)
- Login & onboarding  
- Resume upload  
- Domain selection  
- Interview screen with recording  
- Results page  

### ⚙️ Backend with FastAPI
- REST APIs for interview flow  
- Audio processing  
- NLP scoring  
- Database persistence (SQLite)

### Modules:
- **Frontend (Flutter)** — UI, audio capture, API communication  
- **Backend (FastAPI)** — question logic, scoring engine  
- **ML Models** — SBERT MiniLM, SpaCy, readability metrics  
- **Database** — SQLite for session storage  

---
## 🏗️ System Architecture

Flutter App → FastAPI Backend → STT Engine → NLP Scoring Engine → SQLite DB → Feedback Dashboard

## 🧩 Tech Stack

### Frontend
- Flutter  
- Dart  
- Provider / Bloc (state management)  
- file_picker, dio, flutter_sound  

### Backend
- Python  
- FastAPI  
- Uvicorn  
- SQLite  

### ML/NLP
- Sentence-BERT (MiniLM-L6-v2)  
- SpaCy PhraseMatcher  
- Textstat  
- Google Speech-to-Text / Whisper  
- gTTS  

## 📁 Project Structure

root/
│
├── frontend/
│ ├── lib/
│ ├── assets/
│ ├── pubspec.yaml
│
├── backend/
│ ├── main.py
│ ├── api/
│ ├── models/
│ ├── scoring/
│ ├── resume_parser/
│ ├── database/
│
├── dataset/
│ ├── interview_questions.csv
│
└── README.md
