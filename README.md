# Daily Journal App

A modern journaling application that helps you maintain a daily writing habit and provides insights into your life patterns.

## Features

- Daily journaling with 1000-word minimum requirement
- Sentiment analysis and topic extraction
- Weekly reports and insights
- Life focus analysis
- Personalized feedback and recommendations

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your GROQ API key:
   ```
   GROQ_API_KEY=your_api_key_here
   ```
5. Run the backend:
   ```bash
   uvicorn app.main:app --reload
   ```
6. Run the frontend:
   ```bash
   cd frontend
   npm install
   npm start
   ```

## Tech Stack

- Backend: FastAPI, SQLAlchemy, Groq LLM
- Frontend: React, TypeScript, TailwindCSS
- Database: SQLite (development) / PostgreSQL (production) 