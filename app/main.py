from fastapi import FastAPI, HTTPException, Depends, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
import os
from groq import Groq
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from . import models, database

load_dotenv()

app = FastAPI(title="Daily Journal API")

# Mount static directory for serving images
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/assets", StaticFiles(directory="."), name="assets")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
models.Base.metadata.create_all(bind=database.engine)

# Initialize Groq client
client = Groq(api_key="your_api_key_here")

class JournalEntry(BaseModel):
    content: str
    date: datetime
    word_count: int

class AnalysisRequest(BaseModel):
    entries: List[JournalEntry]

class JournalEntryIn(BaseModel):
    content: str
    date: Optional[datetime] = None

chat_history = []

@app.get("/", response_class=HTMLResponse)
async def get_journal_form():
    return """
    <html>
        <head>
            <title>Daily Journal</title>
            <link href="https://fonts.googleapis.com/css2?family=Sawarabi+Mincho&display=swap" rel="stylesheet">
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    min-height: 100vh;
                    font-family: 'Sawarabi Mincho', serif;
                    background: url('https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1500&q=80') no-repeat center center fixed;
                    background-size: cover;
                    position: relative;
                    overflow-x: hidden;
                }
                .overlay {
                    position: fixed;
                    top: 0; left: 0; right: 0; bottom: 0;
                    background: rgba(255,255,255,0.6);
                    z-index: 0;
                }
                .container {
                    position: relative;
                    z-index: 1;
                    max-width: 700px;
                    margin: 60px auto 0 auto;
                    background: rgba(255,255,255,0.85);
                    border-radius: 18px;
                    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.18);
                    padding: 40px 32px 32px 32px;
                    backdrop-filter: blur(2px);
                }
                h1 {
                    font-size: 2.5em;
                    color: #d81b60;
                    text-align: center;
                    margin-bottom: 24px;
                    letter-spacing: 2px;
                }
                form, .entries-list {
                    margin-top: 24px;
                }
                textarea {
                    width: 100%;
                    min-height: 200px;
                    border-radius: 10px;
                    border: 1px solid #e0b7c1;
                    padding: 16px;
                    font-size: 1.1em;
                    background: #fff8fa;
                    margin-bottom: 18px;
                    resize: vertical;
                }
                button {
                    background: linear-gradient(90deg, #ffb7c5 0%, #d81b60 100%);
                    color: white;
                    border: none;
                    padding: 12px 32px;
                    border-radius: 8px;
                    font-size: 1.1em;
                    cursor: pointer;
                    box-shadow: 0 2px 8px rgba(216,27,96,0.08);
                    transition: background 0.2s;
                }
                button:hover {
                    background: linear-gradient(90deg, #d81b60 0%, #ffb7c5 100%);
                }
                a {
                    color: #d81b60;
                    text-decoration: none;
                    font-weight: bold;
                    margin-right: 18px;
                }
                a:hover {
                    text-decoration: underline;
                }
                /* Falling petals animation */
                .petal {
                    position: fixed;
                    top: -50px;
                    width: 40px;
                    height: 40px;
                    pointer-events: none;
                    z-index: 2;
                    opacity: 0.8;
                    animation: fall 8s linear infinite;
                }
                @keyframes fall {
                    0% { transform: translateY(-50px) rotate(0deg);}
                    100% { transform: translateY(110vh) rotate(360deg);}
                }
            </style>
        </head>
        <body>
            <div class="overlay"></div>
            <div class="container">
                <h1>Write Your Daily Journal</h1>
                <form action="/submit" method="post">
                    <textarea name="content" placeholder="Write at least 1000 words..."></textarea><br>
                    <button type="submit">Submit</button>
                </form>
                <br>
                <a href="/entries">View All Entries</a> | <a href="/chat">Chat with Blossom</a>
            </div>
            <!-- Cherry blossom petals (animated) -->
            <img src="/assets/cherry-blossom.png" class="petal" style="left:10vw; animation-delay:0s;">
            <img src="/assets/cherry-blossom.png" class="petal" style="left:30vw; animation-delay:2s;">
            <img src="/assets/cherry-blossom.png" class="petal" style="left:50vw; animation-delay:1s;">
            <img src="/assets/cherry-blossom.png" class="petal" style="left:70vw; animation-delay:3s;">
            <img src="/assets/cherry-blossom.png" class="petal" style="left:90vw; animation-delay:1.5s;">
        </body>
    </html>
    """

@app.post("/submit", response_class=HTMLResponse)
async def submit_journal(content: str = Form(...), db: Session = Depends(database.get_db)):
    word_count = len(content.split())
    if word_count < 1000:
        return f"<p style='color:red;'>You wrote {word_count} words. Please write at least 1000 words.</p><a href='/'>Back</a>"
    entry = models.JournalEntry(content=content, word_count=word_count, date=datetime.utcnow())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return RedirectResponse(url="/entries", status_code=303)

@app.get("/entries", response_class=HTMLResponse)
async def list_entries(db: Session = Depends(database.get_db)):
    entries = db.query(models.JournalEntry).order_by(models.JournalEntry.date.desc()).all()
    html = """
    <html>
        <head>
            <title>All Journal Entries</title>
            <link href="https://fonts.googleapis.com/css2?family=Sawarabi+Mincho&display=swap" rel="stylesheet">
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    min-height: 100vh;
                    font-family: 'Sawarabi Mincho', serif;
                    background: url('https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1500&q=80') no-repeat center center fixed;
                    background-size: cover;
                    position: relative;
                    overflow-x: hidden;
                }
                .overlay {
                    position: fixed;
                    top: 0; left: 0; right: 0; bottom: 0;
                    background: rgba(255,255,255,0.6);
                    z-index: 0;
                }
                .container {
                    position: relative;
                    z-index: 1;
                    max-width: 700px;
                    margin: 60px auto 0 auto;
                    background: rgba(255,255,255,0.85);
                    border-radius: 18px;
                    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.18);
                    padding: 40px 32px 32px 32px;
                    backdrop-filter: blur(2px);
                }
                h1 {
                    font-size: 2.5em;
                    color: #d81b60;
                    text-align: center;
                    margin-bottom: 24px;
                    letter-spacing: 2px;
                }
                ul {
                    list-style-type: none;
                    padding: 0;
                }
                li {
                    background-color: rgba(255, 255, 255, 0.9);
                    margin: 10px 0;
                    padding: 10px;
                    border-radius: 5px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                }
                a {
                    color: #d81b60;
                    text-decoration: none;
                }
                a:hover {
                    text-decoration: underline;
                }
                button {
                    background-color: #d81b60;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 16px;
                }
                button:hover {
                    background-color: #ad1457;
                }
            </style>
        </head>
        <body>
            <div class="overlay"></div>
            <div class="container">
                <h1>All Journal Entries</h1>
                <ul>
    """
    for entry in entries:
        html += f"<li><b>{entry.date.strftime('%Y-%m-%d')}</b>: {entry.word_count} words <a href='/entry/{entry.id}'>View</a></li>"
    html += """
                </ul>
                <a href='/'>Back to Journal</a>
                <br>
                <a href='/analyze'><button>View Analysis</button></a>
            </div>
            <!-- Cherry blossom petals (animated) -->
            <img src="/assets/cherry-blossom.png" class="petal" style="left:10vw; animation-delay:0s;">
            <img src="/assets/cherry-blossom.png" class="petal" style="left:30vw; animation-delay:2s;">
            <img src="/assets/cherry-blossom.png" class="petal" style="left:50vw; animation-delay:1s;">
            <img src="/assets/cherry-blossom.png" class="petal" style="left:70vw; animation-delay:3s;">
            <img src="/assets/cherry-blossom.png" class="petal" style="left:90vw; animation-delay:1.5s;">
        </body>
    </html>
    """
    return html

@app.get("/entry/{entry_id}", response_class=HTMLResponse)
async def view_entry(entry_id: int, db: Session = Depends(database.get_db)):
    entry = db.query(models.JournalEntry).filter(models.JournalEntry.id == entry_id).first()
    if not entry:
        return "<p>Entry not found.</p><a href='/entries'>Back</a>"
    html = f"""
    <html>
        <head>
            <title>Journal Entry {entry.date.strftime('%Y-%m-%d')}</title>
            <link href="https://fonts.googleapis.com/css2?family=Sawarabi+Mincho&display=swap" rel="stylesheet">
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    min-height: 100vh;
                    font-family: 'Sawarabi Mincho', serif;
                    background: url('https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1500&q=80') no-repeat center center fixed;
                    background-size: cover;
                    position: relative;
                    overflow-x: hidden;
                }
                .overlay {
                    position: fixed;
                    top: 0; left: 0; right: 0; bottom: 0;
                    background: rgba(255,255,255,0.6);
                    z-index: 0;
                }
                .container {
                    position: relative;
                    z-index: 1;
                    max-width: 700px;
                    margin: 60px auto 0 auto;
                    background: rgba(255,255,255,0.85);
                    border-radius: 18px;
                    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.18);
                    padding: 40px 32px 32px 32px;
                    backdrop-filter: blur(2px);
                }
                h1 {
                    font-size: 2.5em;
                    color: #d81b60;
                    text-align: center;
                    margin-bottom: 24px;
                    letter-spacing: 2px;
                }
                pre {
                    background-color: rgba(255, 255, 255, 0.9);
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                }
                a {
                    color: #d81b60;
                    text-decoration: none;
                }
                a:hover {
                    text-decoration: underline;
                }
            </style>
        </head>
        <body>
            <div class="overlay"></div>
            <div class="container">
                <h1>Journal Entry {entry.date.strftime('%Y-%m-%d')}</h1>
                <pre>{entry.content}</pre>
                <p>Word count: {entry.word_count}</p>
                <a href='/entries'>Back to Entries</a>
            </div>
            <!-- Cherry blossom petals (animated) -->
            <img src="/assets/cherry-blossom.png" class="petal" style="left:10vw; animation-delay:0s;">
            <img src="/assets/cherry-blossom.png" class="petal" style="left:30vw; animation-delay:2s;">
            <img src="/assets/cherry-blossom.png" class="petal" style="left:50vw; animation-delay:1s;">
            <img src="/assets/cherry-blossom.png" class="petal" style="left:70vw; animation-delay:3s;">
            <img src="/assets/cherry-blossom.png" class="petal" style="left:90vw; animation-delay:1.5s;">
        </body>
    </html>
    """
    return html

@app.get("/")
async def root():
    return {"message": "Welcome to Daily Journal API"}

@app.post("/analyze")
async def analyze_entries(request: AnalysisRequest):
    try:
        # Combine all entries for analysis
        combined_text = "\n".join([entry.content for entry in request.entries])
        
        # Prepare prompt for analysis
        prompt = f"""Analyze the following journal entries and provide insights about:
        1. Main topics and themes
        2. Emotional patterns
        3. Areas of focus (work, health, relationships, etc.)
        4. Recommendations for improvement
        
        Journal entries:
        {combined_text}
        """
        
        # Get analysis from Groq
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.3-70b-versatile",
            stream=False,
        )
        
        return {
            "analysis": chat_completion.choices[0].message.content,
            "word_count": sum(entry.word_count for entry in request.entries)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/validate-word-count")
async def validate_word_count(entry: JournalEntry):
    if entry.word_count < 1000:
        return {
            "valid": False,
            "message": f"Entry needs {1000 - entry.word_count} more words to meet the daily requirement."
        }
    return {
        "valid": True,
        "message": "Entry meets the daily word count requirement."
    }

@app.get("/analyze", response_class=HTMLResponse)
async def analyze_entries(db: Session = Depends(database.get_db)):
    entries = db.query(models.JournalEntry).order_by(models.JournalEntry.date.desc()).all()
    combined_text = "\n".join([entry.content for entry in entries])
    prompt = f"""Analyze the following journal entries and provide insights about:
    1. Main topics and themes
    2. Emotional patterns
    3. Areas of focus (work, health, relationships, etc.)
    4. Recommendations for improvement
    
    Journal entries:
    {combined_text}
    """
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        stream=False,
    )
    analysis = chat_completion.choices[0].message.content
    return f"""
    <html>
        <head>
            <title>Analysis</title>
            <link href="https://fonts.googleapis.com/css2?family=Sawarabi+Mincho&display=swap" rel="stylesheet">
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    min-height: 100vh;
                    font-family: 'Sawarabi Mincho', serif;
                    background: url('https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1500&q=80') no-repeat center center fixed;
                    background-size: cover;
                    position: relative;
                    overflow-x: hidden;
                }
                .overlay {
                    position: fixed;
                    top: 0; left: 0; right: 0; bottom: 0;
                    background: rgba(255,255,255,0.6);
                    z-index: 0;
                }
                .container {
                    position: relative;
                    z-index: 1;
                    max-width: 700px;
                    margin: 60px auto 0 auto;
                    background: rgba(255,255,255,0.85);
                    border-radius: 18px;
                    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.18);
                    padding: 40px 32px 32px 32px;
                    backdrop-filter: blur(2px);
                }
                h1 {
                    font-size: 2.5em;
                    color: #d81b60;
                    text-align: center;
                    margin-bottom: 24px;
                    letter-spacing: 2px;
                }
                pre {
                    background-color: rgba(255, 255, 255, 0.9);
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                }
                a {
                    color: #d81b60;
                    text-decoration: none;
                }
                a:hover {
                    text-decoration: underline;
                }
            </style>
        </head>
        <body>
            <div class="overlay"></div>
            <div class="container">
                <h1>Analysis</h1>
                <pre>{analysis}</pre>
                <a href='/entries'>Back to Entries</a>
            </div>
            <!-- Cherry blossom petals (animated) -->
            <img src="/assets/cherry-blossom.png" class="petal" style="left:10vw; animation-delay:0s;">
            <img src="/assets/cherry-blossom.png" class="petal" style="left:30vw; animation-delay:2s;">
            <img src="/assets/cherry-blossom.png" class="petal" style="left:50vw; animation-delay:1s;">
            <img src="/assets/cherry-blossom.png" class="petal" style="left:70vw; animation-delay:3s;">
            <img src="/assets/cherry-blossom.png" class="petal" style="left:90vw; animation-delay:1.5s;">
        </body>
    </html>
    """

@app.get("/chat", response_class=HTMLResponse)
async def chat_page():
    chat_html = """
    <html>
      <head>
        <title>Cherry Blossom Chat</title>
        <link href='https://fonts.googleapis.com/css2?family=Sawarabi+Mincho&display=swap' rel='stylesheet'>
        <style>
          body { background: #fff0f6; font-family: 'Sawarabi Mincho', serif; margin: 0; padding: 0; }
          .chat-container { max-width: 600px; height: 80vh; margin: 40px auto; background: rgba(255,255,255,0.95); border-radius: 18px; box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.18); display: flex; flex-direction: column; }
          h1 { color: #d81b60; text-align: center; margin: 24px 0 0 0; }
          .messages { flex: 1; overflow-y: auto; padding: 24px 24px 0 24px; display: flex; flex-direction: column; gap: 12px; }
          .bubble { max-width: 80%; padding: 12px 18px; border-radius: 18px; font-size: 1.1em; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
          .user { align-self: flex-end; background: linear-gradient(90deg, #ffb7c5 0%, #d81b60 100%); color: white; border-bottom-right-radius: 4px; }
          .bot { align-self: flex-start; background: #f3e5f5; color: #d81b60; border-bottom-left-radius: 4px; border: 1px solid #f8bbd0; }
          form { display: flex; gap: 8px; padding: 18px 24px; background: rgba(255,255,255,0.95); border-top: 1px solid #f8bbd0; }
          input[type=text] { flex: 1; padding: 12px; border-radius: 8px; border: 1px solid #e0b7c1; font-size: 1.1em; }
          button { background: linear-gradient(90deg, #ffb7c5 0%, #d81b60 100%); color: white; border: none; padding: 10px 24px; border-radius: 8px; font-size: 1.1em; cursor: pointer; }
          button:hover { background: linear-gradient(90deg, #d81b60 0%, #ffb7c5 100%); }
          .nav { text-align: center; margin: 18px 0 0 0; }
          .nav a { color: #d81b60; text-decoration: none; font-weight: bold; margin: 0 12px; }
          .nav a:hover { text-decoration: underline; }
        </style>
      </head>
      <body>
        <div class="chat-container">
          <h1>Cherry Blossom Chat</h1>
          <div class="messages" id="messages">
    """
    for msg in chat_history:
        if msg['role'] == 'user':
            chat_html += f"<div class='bubble user'>You: {msg['content']}</div>"
        else:
            chat_html += f"<div class='bubble bot'>Blossom: {msg['content']}</div>"
    chat_html += """
          </div>
          <form action="/chat" method="post" autocomplete="off">
            <input type="text" name="message" placeholder="Type your message..." autocomplete="off" required />
            <button type="submit">Send</button>
          </form>
        </div>
        <div class="nav">
          <a href="/">Journal</a> | <a href="/entries">Entries</a>
        </div>
        <script>
          // Auto-scroll to bottom
          var messagesDiv = document.getElementById('messages');
          messagesDiv.scrollTop = messagesDiv.scrollHeight;
        </script>
      </body>
    </html>
    """
    return chat_html

@app.post("/chat", response_class=HTMLResponse)
async def chat_post(request: Request):
    form = await request.form()
    user_message = form.get("message")
    chat_history.append({"role": "user", "content": user_message})
    # Generate response from LLM
    prompt = "You are Blossom, a friendly and supportive companion. Respond like a caring friend.\n" + "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history])
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        stream=False,
    )
    bot_reply = chat_completion.choices[0].message.content
    chat_history.append({"role": "bot", "content": bot_reply})
    return await chat_page() 