"""
mock_interview.py
=================
Servicio de simulación de entrevistas técnicas para ingenieros junior y trainees.
Utiliza Google GenAI SDK con el modelo Gemini 2.5 Flash para generar preguntas
personalizadas basadas en el perfil del candidato y la oferta laboral, y evalúa
las respuestas del usuario con retroalimentación estructurada.
"""

import os
import sys
from typing import Optional
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field

load_dotenv()

# ---------------------------------------------------------------------------
# Modelos Pydantic para salidas estructuradas
# ---------------------------------------------------------------------------

class InterviewQuestion(BaseModel):
    """Representa una pregunta de entrevista generada por la IA."""
    category: str = Field(description="Categoría: 'técnica', 'conductual' o 'situacional'")
    question: str = Field(description="Texto completo de la pregunta")
    difficulty: str = Field(description="Nivel de dificultad: 'básico', 'intermedio' o 'avanzado'")
    tip: str = Field(description="Consejo breve sobre cómo abordar esta pregunta")


class InterviewSession(BaseModel):
    """Conjunto de preguntas generadas para una sesión de entrevista."""
    job_title: str = Field(description="Título del cargo al que se aplica")
    questions: list[InterviewQuestion] = Field(description="Lista de preguntas generadas")
    focus_areas: list[str] = Field(description="Áreas clave detectadas en la oferta laboral")


class AnswerFeedback(BaseModel):
    """Retroalimentación estructurada sobre la respuesta del candidato."""
    score: int = Field(description="Puntuación de 1 a 10", ge=1, le=10)
    strengths: list[str] = Field(description="Aspectos positivos de la respuesta")
    improvements: list[str] = Field(description="Áreas de mejora identificadas")
    ideal_answer_hint: str = Field(description="Pista sobre los elementos clave de una respuesta ideal")
    encouragement: str = Field(description="Mensaje motivador personalizado para el candidato junior")


# ---------------------------------------------------------------------------
# Cliente Gemini
# ---------------------------------------------------------------------------

def _get_client() -> genai.Client:
    """Inicializa y retorna el cliente de Google GenAI."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[ERROR] No se encontró GEMINI_API_KEY en las variables de entorno.")
        print("        Asegúrate de tener un archivo .env con tu clave de API.")
        sys.exit(1)
    return genai.Client(api_key=api_key)


# ---------------------------------------------------------------------------
# Generación de preguntas
# ---------------------------------------------------------------------------

def generate_interview_questions(
    profile: dict,
    job_description: str,
    num_questions: int = 8,
    lang: str = "es"
) -> InterviewSession:
    """
    Genera una sesión de preguntas de entrevista personalizadas.

    Args:
        profile (dict): Perfil del ingeniero junior desde student_profile.yaml.
        job_description (str): Descripción completa de la oferta laboral.
        num_questions (int): Número de preguntas a generar (por defecto 8).
        lang (str): Idioma de salida, 'es' para español o 'en' para inglés.

    Returns:
        InterviewSession: Objeto con las preguntas y áreas de enfoque.
    """
    client = _get_client()

    language_instruction = (
        "Responde completamente en español." if lang == "es"
        else "Respond entirely in English."
    )

    prompt = f"""
{language_instruction}

Eres un experto en procesos de selección para empresas de tecnología.
Tu tarea es preparar a un ingeniero junior para una entrevista real.

PERFIL DEL CANDIDATO:
{profile}

DESCRIPCIÓN DE LA OFERTA LABORAL:
{job_description}

Genera exactamente {num_questions} preguntas de entrevista personalizadas para este candidato
y esta oferta laboral específica. Incluye una mezcla de preguntas:
- Técnicas: relacionadas con las tecnologías y habilidades requeridas.
- Conductuales: sobre experiencias pasadas (usa el método STAR).
- Situacionales: escenarios hipotéticos relevantes al rol.

Para cada pregunta, incluye la categoría, dificultad, y un consejo breve.
También identifica las 3-5 áreas clave que el candidato debe dominar para este rol.

Responde ÚNICAMENTE con un objeto JSON válido con esta estructura:
{{
  "job_title": "<título del cargo>",
  "questions": [
    {{
      "category": "<técnica|conductual|situacional>",
      "question": "<pregunta completa>",
      "difficulty": "<básico|intermedio|avanzado>",
      "tip": "<consejo breve>"
    }}
  ],
  "focus_areas": ["<área 1>", "<área 2>", ...]
}}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    raw = response.text.strip().replace("```json", "").replace("```", "").strip()

    import json
    data = json.loads(raw)
    return InterviewSession(**data)


# ---------------------------------------------------------------------------
# Evaluación de respuestas
# ---------------------------------------------------------------------------

def evaluate_answer(
    question: str,
    answer: str,
    profile: dict,
    lang: str = "es"
) -> AnswerFeedback:
    """
    Evalúa la respuesta del candidato a una pregunta de entrevista.

    Args:
        question (str): La pregunta de entrevista formulada.
        answer (str): La respuesta proporcionada por el candidato.
        profile (dict): Perfil del ingeniero junior.
        lang (str): Idioma de la retroalimentación.

    Returns:
        AnswerFeedback: Retroalimentación estructurada con puntuación y consejos.
    """
    client = _get_client()

    language_instruction = (
        "Responde completamente en español." if lang == "es"
        else "Respond entirely in English."
    )

    prompt = f"""
{language_instruction}

Eres un entrevistador senior compasivo en una empresa de tecnología.
Estás evaluando la respuesta de un ingeniero junior o trainee.

PERFIL DEL CANDIDATO:
{profile}

PREGUNTA DE ENTREVISTA:
{question}

RESPUESTA DEL CANDIDATO:
{answer}

Evalúa la respuesta de forma constructiva y motivadora. Ten en cuenta que es un perfil junior,
por lo que tus expectativas deben ser acordes a ese nivel. Sé específico y útil.

Responde ÚNICAMENTE con un objeto JSON válido con esta estructura:
{{
  "score": <número del 1 al 10>,
  "strengths": ["<fortaleza 1>", "<fortaleza 2>"],
  "improvements": ["<área de mejora 1>", "<área de mejora 2>"],
  "ideal_answer_hint": "<pista sobre elementos clave de una respuesta ideal>",
  "encouragement": "<mensaje motivador personalizado>"
}}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    raw = response.text.strip().replace("```json", "").replace("```", "").strip()

    import json
    data = json.loads(raw)
    return AnswerFeedback(**data)


# ---------------------------------------------------------------------------
# Sesión interactiva de entrevista
# ---------------------------------------------------------------------------

def run_interactive_session(
    profile: dict,
    job_description: str,
    num_questions: int = 5,
    lang: str = "es"
) -> None:
    """
    Ejecuta una sesión interactiva de entrevista en la terminal.

    Args:
        profile (dict): Perfil del candidato.
        job_description (str): Descripción de la oferta laboral.
        num_questions (int): Número de preguntas en la sesión.
        lang (str): Idioma de la sesión ('es' o 'en').
    """
    print("\n" + "=" * 60)
    print("   SIMULADOR DE ENTREVISTA TÉCNICA - JR CAREER COPILOT")
    print("=" * 60)
    print("[INFO] Generando preguntas personalizadas con Gemini 2.5 Flash...")

    session = generate_interview_questions(profile, job_description, num_questions, lang)

    print(f"\n✅ Cargo objetivo: {session.job_title}")
    print(f"📌 Áreas clave a dominar: {', '.join(session.focus_areas)}")
    print(f"\nSe generaron {len(session.questions)} preguntas. ¡Comencemos!\n")

    total_score = 0

    for i, q in enumerate(session.questions, 1):
        print("-" * 60)
        print(f"Pregunta {i}/{len(session.questions)} [{q.category.upper()} - {q.difficulty}]")
        print(f"\n❓ {q.question}")
        print(f"💡 Consejo: {q.tip}\n")

        answer = input("Tu respuesta (presiona Enter dos veces para terminar):\n> ").strip()
        if not answer:
            print("[INFO] Respuesta omitida. Pasando a la siguiente pregunta.\n")
            continue

        print("\n[INFO] Evaluando tu respuesta...\n")
        feedback = evaluate_answer(q.question, answer, profile, lang)

        total_score += feedback.score

        print(f"⭐ Puntuación: {feedback.score}/10")
        print(f"\n✅ Fortalezas:")
        for s in feedback.strengths:
            print(f"   • {s}")
        print(f"\n🔧 Áreas de mejora:")
        for imp in feedback.improvements:
            print(f"   • {imp}")
        print(f"\n🎯 Pista para una respuesta ideal:\n   {feedback.ideal_answer_hint}")
        print(f"\n💪 {feedback.encouragement}\n")

    avg = total_score / len(session.questions) if session.questions else 0
    print("=" * 60)
    print(f"   SESIÓN COMPLETADA — Puntuación promedio: {avg:.1f}/10")
    print("=" * 60)
    if avg >= 8:
        print("🏆 ¡Excelente desempeño! Estás listo para la entrevista real.")
    elif avg >= 6:
        print("📈 Buen desempeño. Repasa las áreas de mejora y practica más.")
    else:
        print("📚 Sigue practicando. Cada entrevista es una oportunidad de aprender.")
    print()


# ---------------------------------------------------------------------------
# Punto de entrada independiente
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import yaml

    profile_path = "config/student_profile.yaml"
    job_path = "job_description.txt"

    try:
        with open(profile_path, "r", encoding="utf-8") as f:
            profile = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"[ERROR] No se encontró el archivo de perfil: {profile_path}")
        sys.exit(1)

    try:
        with open(job_path, "r", encoding="utf-8") as f:
            job_description = f.read().strip()
        if not job_description:
            print(f"[ERROR] El archivo '{job_path}' está vacío.")
            sys.exit(1)
    except FileNotFoundError:
        print(f"[ERROR] No se encontró el archivo de vacante: {job_path}")
        sys.exit(1)

    run_interactive_session(profile, job_description, num_questions=5, lang="es")