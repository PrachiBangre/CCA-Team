import os
import re
import requests
import pathlib
import datetime
from typing import Optional, Union

DATA_DIR = pathlib.Path("data")
COURSES_DIR = DATA_DIR / "courses"
QUIZZES_DIR = DATA_DIR / "quizzes"

for d in (DATA_DIR, COURSES_DIR, QUIZZES_DIR):
    d.mkdir(parents=True, exist_ok=True)


def extract_context(source_type: str, file: Optional[Union[bytes, object]] = None, url: Optional[str] = None) -> str:
    if source_type.lower() == "file" and file is not None:
        try:
            content = file.read()
            if isinstance(content, bytes):
                return content.decode("utf-8", errors="ignore")
            return str(content)
        except Exception as e:
            return f"[Could not read file: {e}]"

    elif source_type.lower() == "url" and url:
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            text = response.text
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text)
            return text.strip()
        except Exception as e:
            return f"[Could not fetch URL: {e}]"

    return ""


def timestamp_slug() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def save_course_to_disk(course_text: str, topic: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_\-]+", "_", topic)[:50]
    fname = COURSES_DIR / f"{timestamp_slug()}_{slug}.txt"
    with open(fname, "w", encoding="utf-8") as f:
        f.write(course_text)
    return str(fname)


def save_quiz_to_disk(quiz_text: str, topic: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_\-]+", "_", topic)[:50]
    fname = QUIZZES_DIR / f"{timestamp_slug()}_{slug}_quiz.txt"
    with open(fname, "w", encoding="utf-8") as f:
        f.write(quiz_text)
    return str(fname)


# Example usage showing correct tuple unpacking:
def example_usage():
    # Simulated course generation function returning (course_text, file_path)
    def generate_course_from_topic(topic, learner_profile, **kwargs):
        dummy_text = f"This is a generated course for topic: {topic}"
        dummy_path = "/path/to/generated_course.txt"
        return dummy_text, dummy_path

    topic = "Leave Policy"
    learner_profile = {
        "name": "Alice",
        "skill_level": "Intermediate",
        "prior_knowledge": "Basic HR",
        "learning_style": "Textual",
        "pace": "Normal",
        "language": "English",
        "time_availability": "2 hours/day",
    }

    # Proper unpacking of tuple to variables
    course_text, generated_path = generate_course_from_topic(topic, learner_profile)

    # Pass only the course_text string to saving function to avoid TypeError
    saved_path = save_course_to_disk(course_text, topic)
    print(f"Course saved to: {saved_path}")


if __name__ == "__main__":
    example_usage()
