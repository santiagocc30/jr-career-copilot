import os
import sys
import yaml
from google import genai
from google.genai import types
from models import OptimizedCV

def optimize_cv(profile: dict, job_description: str, lang: str = "es") -> OptimizedCV:
    """
    Se conecta con la API de Gemini 2.5 Flash para optimizar el CV del ingeniero junior
    basándose en la descripción del empleo utilizando la SDK oficial de google-genai.
    
    Args:
        profile (dict): Datos del perfil del ingeniero junior cargados del YAML.
        job_description (str): Descripción del empleo objetivo.
        lang (str): Idioma de salida para los campos del currículum ('es' o 'en').
        
    Returns:
        OptimizedCV: Objeto Pydantic estructurado y validado con el currículum optimizado.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("\n[ERROR] La variable de entorno GEMINI_API_KEY no está configurada.")
        print("Para solucionar esto:")
        print("  1. Consigue una clave de API gratuita en Google AI Studio (https://aistudio.google.com/).")
        print("  2. Crea un archivo llamado '.env' en la raíz del proyecto.")
        print("  3. Agrega la siguiente línea al archivo '.env':")
        print("     GEMINI_API_KEY=tu_clave_de_api_secreta_aqui")
        print("  4. Alternativamente, puedes exportarla en tu terminal:")
        print("     export GEMINI_API_KEY=\"tu_clave_de_api_secreta_aqui\"")
        sys.exit(1)

    print("\n[INFO] Inicializando cliente de Google GenAI...")
    try:
        client = genai.Client()
    except Exception as exc:
        print("\n[ERROR] Falló la inicialización del cliente de Google GenAI:")
        print(exc)
        sys.exit(1)

    # Mapeo descriptivo del idioma de destino para el prompt
    language_name = "Spanish" if lang == "es" else "English"

    # Crear el prompt optimizado aplicando el Efecto Pygmalion
    prompt = (
        "You are an expert technical recruiter, engineering career coach, and master of resume building. "
        "Your mission is to tailor an engineering junior/trainee's CV to match the target job description. "
        "You must apply the Pygmalion Effect: frame their achievements, projects, and academic background in "
        "an empowering, high-potential light, emphasizing technical excellence, problem-solving abilities, and dedication. "
        "Improve word choice by using strong technical action verbs and industry keywords (e.g., 'Optimized query latency', "
        "'Designed robust microservices', 'Spearheaded testing coverage'). "
        "\n\n"
        "--- CRITICAL LANGUAGE RULE ---\n"
        f"The user has selected the output language: '{language_name}' (code: {lang}).\n"
        f"YOU MUST OUTPUT ALL TEXT FIELDS (names, role titles, achievements, institution degrees, summaries, skills) "
        f"EXCLUSIVELY IN '{language_name}'. Even if the original profile or job description is in another language, "
        f"ensure the final JSON output fields are fully and naturally translated and optimized in '{language_name}'.\n"
        "\n"
        "--- CRITICAL SAFETY RULES (TRUTHFULNESS) ---\n"
        "1. NEVER INVENT OR HALLUCINATE any achievements, jobs, degrees, certifications, dates, or grades that are not "
        "present in the junior engineer's original profile. Doing so would violate professional ethics.\n"
        "2. You may reframe, expand, and structure existing bullet points to showcase engineering rigor, impact, "
        "and relevancy, but the underlying core data must remain 100% truthful to the junior engineer's YAML profile.\n"
        "3. Emphasize keywords from the job description that correspond to the junior engineer's real skills, rearrange the "
        "skills in order of relevance, and highlight tools they actually used.\n"
        "\n"
        f"JUNIOR ENGINEER PROFILE (YAML):\n{yaml.dump(profile, allow_unicode=True)}\n\n"
        f"TARGET JOB DESCRIPTION:\n{job_description}\n"
    )

    print(f"[INFO] Comunicándose con Gemini 2.5 Flash para optimizar el CV (Idioma de salida: {language_name})...")
    
    try:
        # Configurar la llamada estructurada con el esquema Pydantic
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=OptimizedCV,
            temperature=0.2,  # Mayor consistencia y apego a los hechos reales
            system_instruction=(
                "You are an elite career strategist for engineers. You translate junior engineer / trainee profiles into highly "
                "targeted, recruiters-attracting resumes based on specific job descriptions, strictly without fabricating data."
            )
        )
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=config
        )
        
        # Validar la respuesta con el esquema Pydantic
        if not response.text:
            raise ValueError("Gemini devolvió una respuesta vacía.")
            
        optimized_cv = OptimizedCV.model_validate_json(response.text)
        print("[INFO] Optimización completada con éxito por la Inteligencia Artificial.")
        return optimized_cv

    except Exception as exc:
        print("\n[ERROR] Ocurrió un fallo en la llamada o validación con la API de Gemini:")
        print(exc)
        print("\nConsejo: Verifica tu conexión a internet, comprueba que tu API Key sea correcta y que no ")
        print("hayas excedido los límites de cuota (Rate Limits) del modelo gemini-2.5-flash.")
        sys.exit(1)
