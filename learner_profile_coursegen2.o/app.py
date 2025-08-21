#app.py

import streamlit as st
from database import SessionLocal
from models import Course, Quiz, LearnerProfile
from parser import parse_file
from course_generator import generate_course_from_topic
from quiz_generator import generate_quiz
from utils import save_course_to_disk, save_quiz_to_disk
import json
from gtts import gTTS
import pyttsx3
import os

# Set page title and layout
st.set_page_config(page_title="AI Course Generator", layout="wide")

# Initialize DB session
db = SessionLocal()

st.title("📘 AI Course Generator with Quiz System")

# -------------------
# SESSION STATE INIT
# Initialize session state keys to store app status and data across reruns
if "course_obj" not in st.session_state:
    st.session_state.course_obj = None         # Stores DB object for generated course
if "course_content" not in st.session_state:
    st.session_state.course_content = None     # Stores generated course text content
if "course_file_path" not in st.session_state:
    st.session_state.course_file_path = None   # Path to saved course file
if "mark_read" not in st.session_state:
    st.session_state.mark_read = False         # Tracks if user marked course as read
if "quiz_created" not in st.session_state:
    st.session_state.quiz_created = False      # Tracks if quiz is generated
if "quiz_json" not in st.session_state:
    st.session_state.quiz_json = None          # Raw quiz JSON string returned by AI
if "quiz_mcqs" not in st.session_state:
    st.session_state.quiz_mcqs = None          # Parsed list of quiz questions (dicts)
if "understanding_level" not in st.session_state:
    st.session_state.understanding_level = None # User’s understanding level
if "quiz_level" not in st.session_state:
    st.session_state.quiz_level = None         # User-selected difficulty for quiz

# -------------------
# TEXT-TO-SPEECH FUNCTION
def tts_play(text, lang="en"):
    """
    Try gTTS (online) first, fallback to pyttsx3 (offline) if gTTS fails.
    """
    temp_mp3 = "temp_tts.mp3"
    temp_wav = "temp_tts.wav"
    
    try:
        tts = gTTS(text, lang=lang)
        tts.save(temp_mp3)
        with open(temp_mp3, "rb") as audio_file:
            st.audio(audio_file.read(), format="audio/mp3")
        os.remove(temp_mp3)
        return
    except Exception as e:
        st.warning(f"gTTS failed: {e}. Using offline fallback.")

    # Offline fallback
    try:
        engine = pyttsx3.init()
        engine.save_to_file(text, temp_wav)
        engine.runAndWait()
        with open(temp_wav, "rb") as audio_file:
            st.audio(audio_file.read(), format="audio/wav")
        os.remove(temp_wav)
    except Exception as e:
        st.error(f"Offline TTS (pyttsx3) failed: {e}")
# -------------------
# UI INPUTS FOR COURSE GENERATION
topic = st.text_input("Enter topic name")
file = st.file_uploader("Upload file (PDF/DOCX)", type=["pdf", "docx"])
url = st.text_input("Or enter URL (optional -- not implemented)")

st.subheader("Learner Profile")
name = st.text_input("Name")
skill_level = st.selectbox("Skill Level", ["Beginner", "Intermediate", "Advanced"])
prior_knowledge = st.text_area("Prior Knowledge")
learning_style = st.selectbox("Learning Style", ["Visual", "Textual", "Practical"])
pace = st.selectbox("Preferred Pace", ["Slow", "Normal", "Fast"])
language = st.selectbox("Preferred Language", ["English", "Other"])
time_availability = st.text_input("Time availability (e.g., 2h/day)")

generate_course_btn = st.button("Generate Course")

# -------------------
# COURSE GENERATION LOGIC
if generate_course_btn:
    # Basic validation of inputs
    if not topic:
        st.error("Please enter a topic name.")
        st.stop()
    if file:
        content = parse_file(file)  # Extract text from uploaded file
    elif url:
        st.error("URL parsing not implemented.")
        st.stop()
    else:
        st.error("Please upload a file or enter a URL")
        st.stop()

    # Build learner profile object
    learner_profile = LearnerProfile(
        name=name,
        skill_level=skill_level.lower(),
        prior_knowledge=prior_knowledge,
        learning_style=learning_style.lower(),
        pace=pace.lower(),
        language=language,
        time_availability=time_availability,
    )

    # Call course generation function, unpack text output only
    course_content, _ = generate_course_from_topic(topic, learner_profile.to_dict(), content)

    # Save new course in DB
    new_course = Course(topic=topic, outline={}, content=str(course_content))
    db.add(new_course)
    db.commit()
    db.refresh(new_course)

    # Save course text to disk and show path
    file_path = save_course_to_disk(course_content, topic)
    st.success(f"✅ Course Generation is Done Successfully on '{topic}'")
    st.info(f"Course saved locally at: {file_path}")

    # Update session state for course and reset quiz-related states
    st.session_state.course_obj = new_course
    st.session_state.course_content = course_content
    st.session_state.course_file_path = file_path
    st.session_state.mark_read = False
    st.session_state.quiz_created = False
    st.session_state.quiz_json = None
    st.session_state.quiz_mcqs = None

# -------------------
# SHOW GENERATED COURSE
if st.session_state.course_obj:
    st.subheader(f"Course: {st.session_state.course_obj.topic}")

    # Display course text content in scrollable text area
    st.text_area("Course Content", st.session_state.course_content, height=350)

    # Add button to play course content using Text-to-Speech
    if st.button("🔊 Listen to Course Content"):
        tts_play(st.session_state.course_content)

    # Button to download course as .txt file
    st.download_button(
        label="Download Course (.txt)",
        data=st.session_state.course_content,
        file_name=f"{st.session_state.course_obj.topic}_course.txt",
        mime="text/plain",
        key="download_course_btn"
    )

    # Button to mark content as read which unlocks quiz generation
    if not st.session_state.mark_read:
        if st.button("Mark as Read"):
            st.session_state.mark_read = True

# -------------------
# QUIZ PREPARATION
if st.session_state.mark_read and not st.session_state.quiz_created:
    st.header("Quiz Preparation")

    # Get user input for quiz personalization
    understanding_level = st.selectbox("Your Understanding Level", ["Low", "Medium", "High"])
    quiz_level = st.selectbox("Quiz Difficulty Level", ["Easy", "Moderate", "Difficult"])

    if st.button("Generate Quiz"):
        st.info("Generating quiz, please wait...")

        # Generate quiz JSON string from AI based on course content and difficulty
        quiz_json_text = generate_quiz(st.session_state.course_content, difficulty=quiz_level)
        st.session_state.quiz_json = quiz_json_text

        # Attempt to parse JSON response; show raw output on failure for debugging
        try:
            quiz_mcqs = json.loads(quiz_json_text)
            st.session_state.quiz_mcqs = quiz_mcqs
            st.session_state.quiz_created = True
            st.success("Quiz generated successfully!")
        except json.JSONDecodeError:
            st.error("Failed to parse the quiz JSON. Please check the raw quiz output below.")
            st.text_area("Raw Quiz Output", quiz_json_text, height=300)
            st.session_state.quiz_created = False

# -------------------
# QUIZ DISPLAY AND USER INTERACTION
if st.session_state.quiz_created and st.session_state.quiz_mcqs:
    st.header("Take the Quiz")

    user_answers = {}

    # Display first 5 quiz questions with options as radio buttons
    for idx, q in enumerate(st.session_state.quiz_mcqs[:5], start=1):
        st.markdown(f"*Q{idx}. {q['question']}*")
        user_choice = st.radio(f"Your answer for Q{idx}", q['options'], key=f"quiz_q_{idx}")
        user_answers[idx] = user_choice

    # Submit button to score quiz
    if st.button("Submit Quiz"):
        # Count correct answers by comparing user answers to correct ones
        correct_count = sum(
            1 for idx, q in enumerate(st.session_state.quiz_mcqs[:5], start=1)
            if user_answers.get(idx) == q.get("answer")
        )
        st.success(f"Your Score: {correct_count} / 5")

        # Show an expander with correct answers and user result status
        with st.expander("See Correct Answers"):
            for idx, q in enumerate(st.session_state.quiz_mcqs[:5], start=1):
                status = "✅ Correct" if user_answers.get(idx) == q.get("answer") else "❌ Incorrect"
                st.write(f"Q{idx}: {status} | Correct answer: {q.get('answer')}")

        # Option to reset the quiz
        if st.button("Reset Quiz"):
            st.session_state.quiz_created = False
            st.session_state.quiz_mcqs = []
            st.experimental_rerun()