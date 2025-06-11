from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    word_count = Column(Integer, nullable=False)
    sentiment_score = Column(Integer, nullable=True)
    topics = Column(String, nullable=True)  # Stored as JSON string
    analysis = Column(Text, nullable=True)  # Stored analysis from LLM 