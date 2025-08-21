from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, DateTime, func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class LearnerProfile(Base):
    __tablename__ = "learners"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50))
    skill_level = Column(String(20))
    prior_knowledge = Column(Text)
    learning_style = Column(String(20))
    pace = Column(String(20))
    language = Column(String(20))
    time_availability = Column(String(50))

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String(100))
    outline = Column(JSON)
    content = Column(Text)

class Quiz(Base):
    __tablename__ = "quizzes"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    questions = Column(JSON)
