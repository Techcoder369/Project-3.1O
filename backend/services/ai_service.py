"""
AI Service - Smart Content Generator (FINAL STABLE VERSION)
✔ Unique MCQs per quiz
✔ Safe JSON parsing
✔ Retry protection
✔ RAG-based generation
"""

import os
import json
import re
from typing import Dict, List, Set

from dotenv import load_dotenv
load_dotenv()

# ======================================================
# GROQ SETUP
# ======================================================

GROQ_AVAILABLE = False
client = None

try:
    from groq import Groq

    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if api_key and api_key.startswith("gsk_"):
        client = Groq(api_key=api_key)
        GROQ_AVAILABLE = True
        print("✅ Groq AI connected")
    else:
        print("❌ GROQ_API_KEY missing or invalid")

except Exception as e:
    print(f"❌ Groq init failed: {e}")
    GROQ_AVAILABLE = False


# ======================================================
# RAG SERVICE
# ======================================================

try:
    from backend.services.rag_service import rag_service
    RAG_AVAILABLE = True
except Exception as e:
    print(f"⚠ RAG service import failed: {e}")
    RAG_AVAILABLE = False


# ======================================================
# CONFIG
# ======================================================

DIFFICULTY_QUESTION_COUNT = {
    "easy": 5,
    "medium": 8,
    "hard": 10
}

FLASHCARD_COUNT = DIFFICULTY_QUESTION_COUNT


# ======================================================
# INTERNAL: SAFE MCQ GENERATION
# ======================================================

def _generate_mcq_from_context(context: str, asked: Set[str]) -> Dict:
    if not GROQ_AVAILABLE or not client:
        return {}

    previous = "\n".join(f"- {q}" for q in asked) or "None"

    prompt = f"""
Generate ONE UNIQUE exam-oriented MCQ.

STRICT RULES:
- Must NOT repeat or paraphrase previous questions
- Focus on a NEW concept
- DCET / Diploma level
- Exactly 4 options
- One correct answer
- Short explanation
- Return ONLY ONE JSON object

PREVIOUS QUESTIONS:
{previous}

STUDY MATERIAL:
{context[:3000]}

JSON FORMAT ONLY:
{{
  "question": "",
  "options": ["", "", "", ""],
  "correct_index": 0,
  "explanation": ""
}}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are an exam MCQ generator."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=500
        )

        raw = response.choices[0].message.content.strip()

        match = re.search(r"\{[\s\S]*?\}", raw)
        if not match:
            return {}

        data = json.loads(match.group())

        if (
            isinstance(data.get("question"), str)
            and isinstance(data.get("options"), list)
            and len(data["options"]) == 4
            and isinstance(data.get("correct_index"), int)
            and isinstance(data.get("explanation"), str)
        ):
            return data

        return {}

    except Exception as e:
        print("⚠ MCQ generation error:", e)
        return {}


# ======================================================
# FLASHCARD GENERATION
# ======================================================

def _generate_flashcards_from_context(context: str, count: int) -> List[Dict]:
    if not GROQ_AVAILABLE or not client:
        return []

    prompt = f"""
Generate EXACTLY {count} exam-oriented flashcards.

RULES:
- Front: Question only
- Back: Explanation only
- Simple language

STUDY MATERIAL:
{context[:4000]}

Return JSON ARRAY ONLY:
[
  {{
    "front": "",
    "back": ""
  }}
]
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1200
        )

        text = response.choices[0].message.content.strip()

        match = re.search(r"\[\s*\{[\s\S]*?\}\s*\]", text)
        if not match:
            return []

        data = json.loads(match.group())

        flashcards = []
        for card in data:
            front = str(card.get("front", "")).strip()
            back = str(card.get("back", "")).strip()
            if front and back:
                flashcards.append({
                    "question": front,
                    "answer": back,
                    "front": front,
                    "back": back
                })

        return flashcards

    except Exception as e:
        print("⚠ Flashcard error:", e)
        return []


# ======================================================
# PUBLIC API: QUIZ
# ======================================================

def generate_quiz(subject_id: int, unit_id: int, difficulty: str = "medium") -> Dict:
    if not RAG_AVAILABLE:
        return _empty_quiz("Document service not available")

    count = DIFFICULTY_QUESTION_COUNT.get(difficulty, 8)
    chunks = _get_chunks(subject_id, unit_id, top_k=40)

    context = " ".join(c.get("text", "") for c in chunks if c.get("text"))
    if len(context) < 200:
        return _empty_quiz("Insufficient content")

    questions = []
    asked_questions: Set[str] = set()

    attempts = 0
    max_attempts = count * 4

    while len(questions) < count and attempts < max_attempts:
        mcq = _generate_mcq_from_context(context, asked_questions)
        attempts += 1

        if not mcq:
            continue

        q_text = mcq["question"].strip().lower()
        if q_text in asked_questions:
            continue

        asked_questions.add(q_text)
        questions.append(mcq)

    if not questions:
        return _empty_quiz("MCQ generation failed")

    return {
        "success": True,
        "difficulty": difficulty,
        "questions": questions
    }


# ======================================================
# PUBLIC API: FLASHCARDS
# ======================================================

def generate_flashcards(subject_id: int, unit_id: int, difficulty: str = "medium") -> Dict:
    if not RAG_AVAILABLE:
        return {"success": False, "flashcards": []}

    count = FLASHCARD_COUNT.get(difficulty, 8)
    chunks = _get_chunks(subject_id, unit_id, top_k=30)

    context = " ".join(c.get("text", "") for c in chunks if c.get("text"))
    if len(context) < 200:
        return {"success": False, "flashcards": []}

    flashcards = _generate_flashcards_from_context(context, count)

    return {
        "success": True,
        "difficulty": difficulty,
        "flashcards": flashcards
    }


# ======================================================
# HELPERS
# ======================================================

def _get_chunks(subject_id: int, unit_id: int, top_k: int = 20):
    try:
        return rag_service.retrieve_context(
            subject_id=subject_id,
            unit_id=unit_id,
            top_k=top_k
        )
    except Exception:
        return []


def _empty_quiz(message: str) -> Dict:
    return {
        "success": False,
        "message": message,
        "questions": []
    }


__all__ = ["generate_quiz", "generate_flashcards"]
