# database.py

from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()

class Category(Base):
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    
    # تعریف رابطه با جدول‌های دیگر
    questions = relationship("Question", back_populates="category")
    exams = relationship("Exam", back_populates="category")

class Question(Base):
    __tablename__ = 'questions'
    
    id = Column(Integer, primary_key=True)
    title = Column(Text, nullable=False)
    image_url = Column(String(500))
    option_a = Column(String(200), nullable=False)
    option_b = Column(String(200), nullable=False)
    option_c = Column(String(200), nullable=False)
    option_d = Column(String(200), nullable=False)
    correct_answer = Column(String(1), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    
    # تعریف رابطه‌ها
    category = relationship("Category", back_populates="questions")
    exam_questions = relationship("ExamQuestion", back_populates="question")

class Exam(Base):
    __tablename__ = 'exams'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    price = Column(Integer, default=0)
    question_count = Column(Integer, nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)  # اضافه کردن این ستون
    
    # تعریف رابطه‌ها
    category = relationship("Category", back_populates="exams")
    exam_questions = relationship("ExamQuestion", back_populates="exam")
    user_exams = relationship("UserExam", back_populates="exam")

class ExamQuestion(Base):
    __tablename__ = 'exam_questions'
    
    id = Column(Integer, primary_key=True)
    exam_id = Column(Integer, ForeignKey('exams.id'), nullable=False)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False)
    
    # تعریف رابطه‌ها
    exam = relationship("Exam", back_populates="exam_questions")
    question = relationship("Question", back_populates="exam_questions")

class UserExam(Base):
    __tablename__ = 'user_exams'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    exam_id = Column(Integer, ForeignKey('exams.id'), nullable=False)
    answers = Column(String, nullable=False)
    current_question = Column(Integer, default=0)
    score = Column(Float, default=0)
    is_finished = Column(Boolean, default=False)
    is_paid = Column(Boolean, default=False)
    
    # تعریف رابطه‌ها
    exam = relationship("Exam", back_populates="user_exams")

# ایجاد موتور دیتابیس و جلسه
engine = create_engine('sqlite:///bot.db')
Session = sessionmaker(bind=engine)

# ایجاد جداول در صورت عدم وجود
def create_tables():
    Base.metadata.create_all(engine)

if __name__ == '__main__':
    create_tables()