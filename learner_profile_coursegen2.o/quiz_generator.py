import os
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def call_groq_with_retry(messages, model="llama3-8b-8192", max_retries=5, wait_time=1):
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                messages=messages,
                model=model,
            )
            return response
        except Exception as e:
            print(f"Groq API error: {e}. Retrying in {wait_time} seconds... (Attempt {attempt+1}/{max_retries})")
            time.sleep(wait_time)
            wait_time *= 2
    raise Exception("Groq API request failed after retries")

def generate_quiz(course_content, difficulty="Medium"):
    messages = [
        {
            "role": "system",
            "content": "Generate quizzes consisting of multiple-choice questions (MCQs) in valid JSON format only."
        },
        {
            "role": "user",
            "content": (
                f"Generate 5 MCQs based on the following course content.\n"
                f"Each MCQ must have exactly 4 options and one correct answer.\n"
                f"Difficulty level: {difficulty}.\n"
                f"Output ONLY valid JSON exactly as:\n"
                f"[\n"
                f"  {{\n"
                f"    \"question\": \"...\",\n"
                f"    \"options\": [\"...\", \"...\", \"...\", \"...\"],\n"
                f"    \"answer\": \"...\"\n"
                f"  }},\n"
                f"  ... 4 more questions ...\n"
                f"]\n\n"
                f"Course Content:\n{course_content[:1000]}"
            ),
        },
    ]
    response = call_groq_with_retry(messages)
    quiz_text = response.choices[0].message.content.strip()

    print("DEBUG: Raw quiz JSON text from AI:", quiz_text)  # For debugging

    return quiz_text
