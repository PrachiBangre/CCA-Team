import os
import tempfile
import logging
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st
import time
import groq
from groq import Groq
from langchain.prompts import PromptTemplate

# ------------------- CONFIGURATION -------------------
load_dotenv()
logging.basicConfig(filename="app.log", level=logging.ERROR)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("No API key found for Groq in .env")

groq_client = Groq(api_key=GROQ_API_KEY)

# ------------------- FILE & WEB EXTRACTION -------------------
def _extract_text_from_file(file, chunk_size=3000):
    import fitz

    text = ""
    file_ext = Path(file.name).suffix.lower()
    if file_ext == ".pdf":
        pdf_doc = fitz.open(stream=file.read(), filetype="pdf")
        for page in pdf_doc:
            text += page.get_text()
    else:
        text = file.read().decode("utf-8", errors="ignore")

    # Split text into chunks of chunk_size
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    return chunks

def _extract_text_from_url(url):
    """Extract up to 3000 chars of visible text from a webpage."""
    import requests
    from bs4 import BeautifulSoup

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        text = " ".join(p.get_text() for p in soup.find_all("p"))
    except Exception as e:
        logging.error(f"Error fetching URL: {url} — {e}", exc_info=True)
        st.error(f"❌ Failed to fetch URL: {e}")
        text = ""

    return text[:3000]

# ------------------- MODEL GENERATION -------------------
def generate_with_groq_with_retries(prompt, placeholder=None, retries=3):
    """
    Generate text using Groq's LLaMA3 model with streaming output and automatic retry on timeout.
    """
    delay = 2  # Initial waiting period in seconds before retrying
    for attempt in range(retries):
        try:
            course_text = ""
            with st.spinner("⏳ Generating course (Groq)…"):
                stream = groq_client.chat.completions.create(
                    model="llama3-70b-8192",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    stream=True
                )
                for chunk in stream:
                    content_piece = getattr(chunk.choices[0].delta, "content", None)
                    if content_piece:
                        course_text += content_piece
                        if placeholder:
                            placeholder.markdown(course_text)
            return course_text

        except groq.APITimeoutError:
            if attempt < retries - 1:
                time.sleep(delay)
                delay *= 2  # exponential backoff
            else:
                raise

# ------------------- PROMPT TEMPLATE -------------------
def get_prompt(topic, context, learner_profile):
    name = learner_profile.get("name", "Learner")
    skill_level = learner_profile.get("skill_level", "Beginner")
    prior_knowledge = learner_profile.get("prior_knowledge", "None")
    learning_style = learner_profile.get("learning_style", "Textual")
    pace = learner_profile.get("pace", "Normal")
    language = learner_profile.get("language", "English")
    time_availability = learner_profile.get("time_availability", "Flexible")

    template = f"""
You are designing a comprehensive and tailored course on the topic: **\"{topic}\"**.

### Learner Profile & Background
- **Name:** {name}
- **Current Skill Level:** {skill_level}
- **Prior Knowledge:** {prior_knowledge}
- **Preferred Learning Style:** {learning_style}
- **Preferred Pace:** {pace}
- **Language:** {language}
- **Time Available:** {time_availability}

---

### Learning Goals & Objectives

Please consider that the learner expects a course structured to:
- Meet their specific skill level and learning preferences,
- Fit within their pace and available time,
- Use language accessible and clear to them,
- And help them achieve mastery of the "{topic}" exact knowledge as per the policy document.

---

### Content Source & Quality

- Use **only** the official policy document text provided below.
- Do **not** add external information, general HR knowledge, or personal interpretations.
- Quote or paraphrase **exactly** from the document, preserving terminology, formal titles, clauses, and wordings.
- Include official lists, tables, and numbered points as they appear.

---

### Important Formatting Instructions

- Do NOT include any internal chunk markers like `<!-- Section 1 -->` in the final course output.
- Instead, replace such internal markers with clear, descriptive module headings or breaks so the course is visually appealing and easy to follow.
- Expand module and subtopic explanations with details from the document for clarity and learner engagement, while sticking strictly to the source text.
- Use consistent formatting with headings, bullet points, and numbered lists as per the document style.
- Make the course user-friendly and descriptive without adding any content not present in the provided document.

---

### Structure & Instructional Design

Organize the course as follows:

- **2 to 3 Main Modules**, clearly numbered and titled.
- Each module should have:
  - A **Module Overview**: 4–6 sentences summarizing the focus and relevance.
  - **1 to 2 Subtopics**, each explained with:
    - The concept or rule described in the document,
    - Its significance in context,
    - Relevant procedures or examples if present.
  - A bulleted list of **Learning Outcomes**: 2–3 clear, actionable points derived from the content.

Ensure the content is chunked into manageable lessons with a formal, professional tone aligned with the policy document style.

---

### Example Format

**Module 1: Appointment Authorities**

**Module Overview:**  
This module explains the appointment authorities as defined in the policy document.

**Subtopics:**

1.1 Pay Level Groups and Authorities  
- Administrative Staff in Pay Level 11 and above: appointed by Director  
- Administrative Staff in Pay Level 6 to 10: appointed by Chief Administrative Officer (delegated authority)  
- Administrative Staff in Pay Level 5 and below: appointed by Associate Vice President – HR (sub-delegated authority)

1.2 Contract Types and Terms  
- Initial appointments are on Tenure Based Scaled Contract.  
- Salary and allowances follow the scale fixed for these appointments.  
- Leave eligibility for contract employees matches that of permanent employees.

---

### Official Policy Document Reference

\"\"\"  
{context}  
\"\"\"

Please create the complete, well-structured course now.
"""
    return PromptTemplate.from_template(template).format(topic=topic, context=context)

# ------------------- MAIN FUNCTION -------------------
def generate_course_from_topic(topic, learner_profile, source_type="file", file=None, url=None, placeholder=None):
    # Initialize session state flag to avoid regenerating multiple times
    if 'course_generated' not in st.session_state:
        st.session_state['course_generated'] = False
        st.session_state['course_content'] = None
        st.session_state['course_file_path'] = None

    # Only generate if not done yet
    if st.session_state['course_generated']:
        return st.session_state['course_content'], st.session_state['course_file_path']

    # Extract full text in chunks based on input
    if source_type.lower() == "file" and file:
        text_chunks = _extract_text_from_file(file)
    elif source_type.lower() == "web url" and url:
        text = _extract_text_from_url(url)
        text_chunks = [text]
    else:
        text_chunks = [""]

    full_course_text = ""
    chunk_index = 1
    for chunk in text_chunks:
        prompt = get_prompt(topic, chunk, learner_profile)
        partial_text = generate_with_groq_with_retries(prompt, placeholder)
        full_course_text += f"\n\n<!-- Section {chunk_index} -->\n\n{partial_text}"
        chunk_index += 1

    # Save the combined text to a temp file
    file_path = Path(tempfile.gettempdir()) / f"{topic.replace(' ', '_')}.txt"
    try:
        with file_path.open("w", encoding="utf-8") as f:
            f.write(full_course_text)
    except Exception as e:
        logging.error(f"Error saving course file: {e}", exc_info=True)
        st.error(f"❌ Failed to save course file: {e}")

    # Store in session state to avoid regeneration
    st.session_state['course_generated'] = True
    st.session_state['course_content'] = full_course_text
    st.session_state['course_file_path'] = str(file_path)

    return full_course_text, str(file_path)

# ------------------- RUN TEST IF STANDALONE -------------------
if __name__ == "__main__":
    import io

    learner_profile = {
        "name": "Prachi Naresh Bangre",
        "skill_level": "Intermediate",
        "prior_knowledge": "Familiar with basic HR policies",
        "learning_style": "Textual",
        "pace": "Normal",
        "language": "English",
        "time_availability": "2 hours/day",
    }

    document_text = (
        "This document contains detailed information about leave policies, "
        "including types of leaves, application procedures, entitlements, approvals, and dispute resolution."
    )

    topic = "Leave Policy"
    course, path = generate_course_from_topic(topic, learner_profile, source_type="none", placeholder=None)
    print("=== Generated Course ===")
    print(course)
    print(f"\nCourse saved to: {path}")
