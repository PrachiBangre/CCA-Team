# Learner-Profile Course Generator (Streamlit)

A Streamlit app that:
- Collects a learner profile (skill level, prior knowledge, learning style, pace, language, available time)
- Generates a personalized course outline from a topic + optional file or URL
- Saves courses (text + profile) to DB and local disk (.txt)
- After "Mark as Read", generates a quiz whose difficulty adapts to the learner's skill level
- Sidebar shows history of courses and quizzes

## Quickstart

```bash
# 1) (Optional) create venv
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2) Install deps
pip install -r requirements.txt

# 3) Configure LLM provider (choose one)
# OpenAI:
export MODEL_PROVIDER=openai
export OPENAI_API_KEY=sk-...

# Groq:
export MODEL_PROVIDER=groq
export GROQ_API_KEY=gsk_...

# Or use a dummy local generator (no API keys needed):
export MODEL_PROVIDER=dummy

# 4) Run
streamlit run app.py
```

## Files
- `app.py` – Streamlit UI and flow
- `course_generator.py` – builds course prompt & calls LLM
- `quiz_generator.py` – builds quiz prompt & calls LLM
- `database.py` – SQLAlchemy session/engine
- `models.py` – SQLAlchemy models
- `utils.py` – helpers for context extraction and saving files

## Notes
- SQLite DB created at `app.db` by default.
- Files saved under `data/courses/` and `data/quizzes/`.
- For URL context, we fetch raw text from the page. Provide accessible URLs.
