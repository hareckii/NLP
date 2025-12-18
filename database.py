from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class LanguageProfile(Base):
    """Профиль языка для N-грамм метода"""
    __tablename__ = 'language_profiles'
    
    id = Column(Integer, primary_key=True)
    language = Column(String(50), nullable=False)
    ngram = Column(String(10), nullable=False)
    frequency = Column(Float, nullable=False)
    rank = Column(Integer, nullable=False)
    method = Column(String(20), default='n-gram')
    created_at = Column(DateTime, default=datetime.now)

class AlphabetProfile(Base):
    """Профиль языка для алфавитного метода"""
    __tablename__ = 'alphabet_profiles'
    
    id = Column(Integer, primary_key=True)
    language = Column(String(50), nullable=False)
    character = Column(String(5), nullable=False)
    frequency = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

class Document(Base):
    """Документы для анализа"""
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True)
    filename = Column(String(255))
    content = Column(Text)
    language_n_gram = Column(String(50))
    language_alphabet = Column(String(50))
    language_neural = Column(String(50))
    confidence_n_gram = Column(Float)
    confidence_alphabet = Column(Float)
    confidence_neural = Column(Float)
    processing_time = Column(Float)
    created_at = Column(DateTime, default=datetime.now)

class DetectionResult(Base):
    """Результаты распознавания"""
    __tablename__ = 'detection_results'
    
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer)
    method = Column(String(20))
    detected_language = Column(String(50))
    confidence = Column(Float)
    processing_time = Column(Float)
    created_at = Column(DateTime, default=datetime.now)

# Создание базы данных
def init_db():
    engine = create_engine('sqlite:///language_detection.db')
    Base.metadata.create_all(engine)
    return engine

# Создание сессии
def get_session():
    engine = init_db()
    Session = sessionmaker(bind=engine)
    return Session()