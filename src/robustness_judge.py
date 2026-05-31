"""
robustness_judge.py
===================
Servicio de evaluación de robustez del CV optimizado.
Actúa como un "juez crítico" que analiza el CV final desde múltiples perspectivas:
reclutador, ATS (Applicant Tracking System) y entrevistador técnico senior.
Utiliza Google GenAI SDK con Gemini 2.5 Flash para producir un reporte detallado
con puntuaciones, alertas y recomendaciones accionables.
"""

import os
import sys
import json
from typing import Optional
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field

load_dotenv()


# ---------------------------------------------------------------------------
# Modelos Pydantic para salidas estructuradas
# ---------------------------------------------------------------------------

class ATSAnalysis(BaseModel):
    """Análisis de compatibilidad con sistemas ATS."""
    score: int = Field(description="Puntuación ATS del 1 al 100", ge=1, le=100)
    matched_keywords: list[str] = Field(description="Palabras clave de la oferta presentes en el CV")
    missing_keywords: list[str] = Field(description="Palabras clave importantes ausentes en el CV")
    format_warnings: list[str] = Field(description="Advertencias sobre formato que pueden afectar el ATS")


class RecruiterAnalysis(BaseModel):
    """Evaluación desde la perspectiva del reclutador de RRHH."""
    first_impression_score: int = Field(description="Puntuación de primera impresión del 1 al 10", ge=1, le=10)
    clarity_score: int = Field(description="Claridad y legibilidad del 1 al 10", ge=1, le=10)
    strengths: list[str] = Field(description="Aspectos que destacan positivamente para el reclutador")
    red_flags: list[str] = Field(description="Elementos que podrían generar dudas o rechazo")
    summary_quality: str = Field(description="Evaluación del resumen/objetivo profesional")


class TechnicalAnalysis(BaseModel):
    """Evaluación desde la perspectiva del entrevistador técnico."""
    technical_credibility_score: int = Field(
        description="Credibilidad técnica del perfil del 1 al 10", ge=1, le=10
    )
    skill_alignment: list[str] = Field(description="Habilidades técnicas bien alineadas con la oferta")
    skill_gaps: list[str] = Field(description="Brechas técnicas detectadas respecto a la oferta")
    project_quality: str = Field(description="Evaluación de los proyectos o experiencias mencionadas")
    recommendations: list[str] = Field(description="Recomendaciones técnicas específicas para mejorar el CV")


class PygmalionAnalysis(BaseModel):
    """Evaluación del efecto Pygmalion aplicado al CV."""
    pygmalion_score: int = Field(
        description="Nivel de potenciación del perfil del 1 al 10 (sin falsificar datos)", ge=1, le=10
    )
    well_amplified: list[str] = Field(description="Logros académicos o laborales bien potenciados")
    under_amplified: list[str] = Field(description="Logros que podrían expresarse con mayor impacto")
    ethical_alerts: list[str] = Field(description="Alertas si algún contenido parece exagerado o irreal")


class RobustnessReport(BaseModel):
    """Reporte completo de robustez del CV optimizado."""
    overall_score: int = Field(description="Puntuación global de robustez del 1 al 100", ge=1, le=100)
    verdict: str = Field(description="Veredicto final: 'Listo para enviar', 'Necesita ajustes', o 'Requiere revisión mayor'")
    ats: ATSAnalysis
    recruiter: RecruiterAnalysis
    technical: TechnicalAnalysis
    pygmalion: PygmalionAnalysis
    top_3_actions: list[str] = Field(description="Las 3 acciones más importantes a tomar antes de enviar el CV")
    motivational_closing: str = Field(description="Cierre motivador personalizado para el candidato junior")


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
# Evaluación de robustez principal
# ---------------------------------------------------------------------------

def evaluate_cv_robustness(
    optimized_cv_text: str,
    job_description: str,
    profile: dict,
    lang: str = "es"
) -> RobustnessReport:
    """
    Evalúa la robustez del CV optimizado desde múltiples perspectivas.

    Args:
        optimized_cv_text (str): Contenido del CV optimizado (texto Markdown o plano).
        job_description (str): Descripción completa de la oferta laboral.
        profile (dict): Perfil original del candidato desde student_profile.yaml.
        lang (str): Idioma del reporte ('es' para español, 'en' para inglés).

    Returns:
        RobustnessReport: Reporte completo con puntuaciones y recomendaciones.
    """
    client = _get_client()

    language_instruction = (
        "Responde completamente en español." if lang == "es"
        else "Respond entirely in English."
    )

    prompt = f"""
{language_instruction}

Eres un panel de expertos en selección de talento tecnológico compuesto por:
1. Un especialista en ATS (Applicant Tracking Systems)
2. Un reclutador senior de recursos humanos
3. Un entrevistador técnico senior en ingeniería de software
4. Un coach de marca personal para ingenieros junior

Tu tarea es evaluar la calidad y robustez de este CV optimizado por IA para un ingeniero junior.
Sé crítico pero constructivo. Ten en cuenta que el candidato es junior/trainee.

PERFIL ORIGINAL DEL CANDIDATO:
{json.dumps(profile, ensure_ascii=False, indent=2)}

DESCRIPCIÓN DE LA OFERTA LABORAL:
{job_description}

CV OPTIMIZADO A EVALUAR:
{optimized_cv_text}

Evalúa el CV desde las 4 perspectivas del panel y genera un reporte estructurado completo.
Asegúrate de que las alertas éticas detecten contenido que parezca exagerado o inventado
respecto al perfil original. El Efecto Pygmalion debe potenciar, no falsificar.

Responde ÚNICAMENTE con un objeto JSON válido con esta estructura exacta:
{{
  "overall_score": <1-100>,
  "verdict": "<Listo para enviar|Necesita ajustes|Requiere revisión mayor>",
  "ats": {{
    "score": <1-100>,
    "matched_keywords": ["<kw1>", ...],
    "missing_keywords": ["<kw1>", ...],
    "format_warnings": ["<aviso1>", ...]
  }},
  "recruiter": {{
    "first_impression_score": <1-10>,
    "clarity_score": <1-10>,
    "strengths": ["<fortaleza1>", ...],
    "red_flags": ["<bandera roja1>", ...],
    "summary_quality": "<evaluación>"
  }},
  "technical": {{
    "technical_credibility_score": <1-10>,
    "skill_alignment": ["<habilidad1>", ...],
    "skill_gaps": ["<brecha1>", ...],
    "project_quality": "<evaluación>",
    "recommendations": ["<recomendación1>", ...]
  }},
  "pygmalion": {{
    "pygmalion_score": <1-10>,
    "well_amplified": ["<logro1>", ...],
    "under_amplified": ["<logro1>", ...],
    "ethical_alerts": ["<alerta1>", ...]
  }},
  "top_3_actions": ["<acción1>", "<acción2>", "<acción3>"],
  "motivational_closing": "<mensaje motivador>"
}}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    raw = response.text.strip().replace("```json", "").replace("```", "").strip()
    data = json.loads(raw)
    return RobustnessReport(**data)


# ---------------------------------------------------------------------------
# Renderizado del reporte en consola
# ---------------------------------------------------------------------------

def print_robustness_report(report: RobustnessReport) -> None:
    """
    Imprime el reporte de robustez de forma legible en la terminal.

    Args:
        report (RobustnessReport): El reporte generado por evaluate_cv_robustness.
    """
    print("\n" + "=" * 65)
    print("        REPORTE DE ROBUSTEZ DEL CV — JR CAREER COPILOT")
    print("=" * 65)

    verdict_emoji = {
        "Listo para enviar": "🟢",
        "Necesita ajustes": "🟡",
        "Requiere revisión mayor": "🔴"
    }.get(report.verdict, "⚪")

    print(f"\n{verdict_emoji} VEREDICTO: {report.verdict}")
    print(f"📊 Puntuación Global de Robustez: {report.overall_score}/100\n")

    # ATS
    print("-" * 65)
    print(f"🤖 ANÁLISIS ATS — Puntuación: {report.ats.score}/100")
    print(f"   ✅ Keywords presentes: {', '.join(report.ats.matched_keywords) or 'Ninguna detectada'}")
    print(f"   ❌ Keywords faltantes: {', '.join(report.ats.missing_keywords) or 'Ninguna'}")
    if report.ats.format_warnings:
        print("   ⚠️  Advertencias de formato:")
        for w in report.ats.format_warnings:
            print(f"      • {w}")

    # Reclutador
    print(f"\n👔 PERSPECTIVA RECLUTADOR")
    print(f"   Primera impresión: {report.recruiter.first_impression_score}/10  |  Claridad: {report.recruiter.clarity_score}/10")
    print(f"   📝 Resumen profesional: {report.recruiter.summary_quality}")
    print("   ✅ Fortalezas:")
    for s in report.recruiter.strengths:
        print(f"      • {s}")
    if report.recruiter.red_flags:
        print("   🚩 Banderas rojas:")
        for r in report.recruiter.red_flags:
            print(f"      • {r}")

    # Técnico
    print(f"\n💻 PERSPECTIVA TÉCNICA — Credibilidad: {report.technical.technical_credibility_score}/10")
    print(f"   📋 Proyectos: {report.technical.project_quality}")
    print("   ✅ Habilidades alineadas:")
    for s in report.technical.skill_alignment:
        print(f"      • {s}")
    if report.technical.skill_gaps:
        print("   🔧 Brechas detectadas:")
        for g in report.technical.skill_gaps:
            print(f"      • {g}")
    print("   💡 Recomendaciones técnicas:")
    for rec in report.technical.recommendations:
        print(f"      • {rec}")

    # Pygmalion
    print(f"\n✨ EFECTO PYGMALION — Puntuación: {report.pygmalion.pygmalion_score}/10")
    print("   🚀 Bien potenciado:")
    for w in report.pygmalion.well_amplified:
        print(f"      • {w}")
    if report.pygmalion.under_amplified:
        print("   📈 Podría potenciarse más:")
        for u in report.pygmalion.under_amplified:
            print(f"      • {u}")
    if report.pygmalion.ethical_alerts:
        print("   ⚠️  Alertas éticas:")
        for a in report.pygmalion.ethical_alerts:
            print(f"      • {a}")

    # Top 3 acciones
    print("\n" + "-" * 65)
    print("🎯 TOP 3 ACCIONES PRIORITARIAS ANTES DE ENVIAR:")
    for i, action in enumerate(report.top_3_actions, 1):
        print(f"   {i}. {action}")

    print(f"\n💪 {report.motivational_closing}")
    print("=" * 65 + "\n")


# ---------------------------------------------------------------------------
# Exportar reporte a Markdown
# ---------------------------------------------------------------------------

def export_report_to_markdown(report: RobustnessReport, output_path: str = "output/robustness_report.md") -> None:
    """
    Exporta el reporte de robustez a un archivo Markdown.

    Args:
        report (RobustnessReport): El reporte de robustez generado.
        output_path (str): Ruta del archivo de salida.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    verdict_emoji = {
        "Listo para enviar": "🟢",
        "Necesita ajustes": "🟡",
        "Requiere revisión mayor": "🔴"
    }.get(report.verdict, "⚪")

    lines = [
        "# Reporte de Robustez del CV — JR Career Copilot\n",
        f"## {verdict_emoji} Veredicto: {report.verdict}",
        f"**Puntuación Global:** {report.overall_score}/100\n",
        "---\n",
        f"## 🤖 Análisis ATS — {report.ats.score}/100",
        f"- **Keywords presentes:** {', '.join(report.ats.matched_keywords) or 'Ninguna'}",
        f"- **Keywords faltantes:** {', '.join(report.ats.missing_keywords) or 'Ninguna'}",
    ]
    if report.ats.format_warnings:
        lines.append("- **Advertencias de formato:**")
        for w in report.ats.format_warnings:
            lines.append(f"  - {w}")

    lines += [
        "\n---\n",
        f"## 👔 Perspectiva Reclutador",
        f"- Primera impresión: **{report.recruiter.first_impression_score}/10** | Claridad: **{report.recruiter.clarity_score}/10**",
        f"- Resumen profesional: {report.recruiter.summary_quality}",
        "- **Fortalezas:**",
    ]
    for s in report.recruiter.strengths:
        lines.append(f"  - {s}")
    if report.recruiter.red_flags:
        lines.append("- **Banderas rojas:**")
        for r in report.recruiter.red_flags:
            lines.append(f"  - {r}")

    lines += [
        "\n---\n",
        f"## 💻 Perspectiva Técnica — Credibilidad: {report.technical.technical_credibility_score}/10",
        f"- Proyectos: {report.technical.project_quality}",
        "- **Habilidades alineadas:**",
    ]
    for s in report.technical.skill_alignment:
        lines.append(f"  - {s}")
    if report.technical.skill_gaps:
        lines.append("- **Brechas:**")
        for g in report.technical.skill_gaps:
            lines.append(f"  - {g}")
    lines.append("- **Recomendaciones:**")
    for rec in report.technical.recommendations:
        lines.append(f"  - {rec}")

    lines += [
        "\n---\n",
        f"## ✨ Efecto Pygmalion — {report.pygmalion.pygmalion_score}/10",
        "- **Bien potenciado:**",
    ]
    for w in report.pygmalion.well_amplified:
        lines.append(f"  - {w}")
    if report.pygmalion.under_amplified:
        lines.append("- **Podría potenciarse más:**")
        for u in report.pygmalion.under_amplified:
            lines.append(f"  - {u}")
    if report.pygmalion.ethical_alerts:
        lines.append("- **⚠️ Alertas éticas:**")
        for a in report.pygmalion.ethical_alerts:
            lines.append(f"  - {a}")

    lines += [
        "\n---\n",
        "## 🎯 Top 3 Acciones Prioritarias",
    ]
    for i, action in enumerate(report.top_3_actions, 1):
        lines.append(f"{i}. {action}")

    lines += [
        "\n---\n",
        f"## 💪 Mensaje Final\n",
        report.motivational_closing,
    ]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"[INFO] Reporte exportado a: {output_path}")


# ---------------------------------------------------------------------------
# Punto de entrada independiente
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import yaml

    profile_path = "config/student_profile.yaml"
    job_path = "job_description.txt"
    cv_path = "output/optimized_cv.md"

    try:
        with open(profile_path, "r", encoding="utf-8") as f:
            profile = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"[ERROR] No se encontró el perfil: {profile_path}")
        sys.exit(1)

    try:
        with open(job_path, "r", encoding="utf-8") as f:
            job_description = f.read().strip()
        if not job_description:
            print(f"[ERROR] El archivo '{job_path}' está vacío.")
            sys.exit(1)
    except FileNotFoundError:
        print(f"[ERROR] No se encontró la vacante: {job_path}")
        sys.exit(1)

    try:
        with open(cv_path, "r", encoding="utf-8") as f:
            optimized_cv = f.read().strip()
        if not optimized_cv:
            print(f"[ERROR] El CV optimizado '{cv_path}' está vacío. Ejecuta primero cv_optimizer.py.")
            sys.exit(1)
    except FileNotFoundError:
        print(f"[ERROR] No se encontró el CV optimizado: {cv_path}")
        print("        Ejecuta primero: py src/cv_optimizer.py --job job_description.txt")
        sys.exit(1)

    print("[INFO] Evaluando robustez del CV con el panel de expertos IA...")
    report = evaluate_cv_robustness(optimized_cv, job_description, profile, lang="es")
    print_robustness_report(report)
    export_report_to_markdown(report)