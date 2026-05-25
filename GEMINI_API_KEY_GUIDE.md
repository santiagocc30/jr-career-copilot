# Guía Paso a Paso: Obtención y Configuración de la Clave de API de Gemini 🔑

Esta guía está diseñada para que estudiantes de ingeniería configuren de forma rápida y segura su acceso a los modelos de lenguaje de Google (particularmente **Gemini 2.5 Flash**) utilizando la plataforma **Google AI Studio**.

---

## 🌟 ¿Qué es Google AI Studio?

**Google AI Studio** es una herramienta de prototipado rápido basada en la web que permite a desarrolladores y estudiantes experimentar con los modelos Gemini de Google. A través de esta plataforma, puedes generar **Claves de API (API Keys)** para conectar tus aplicaciones locales a la infraestructura de inteligencia artificial de Google.

> [!NOTE]
> **Cuota Gratuita:** Google AI Studio ofrece un nivel gratuito muy generoso para el desarrollo y pruebas académicas de tus aplicaciones, el cual es ideal para este proyecto de optimización de CV. No necesitas ingresar tarjetas de crédito para este nivel básico.

---

## 📋 Paso 1: Obtener la Clave de API

Sigue detalladamente estos pasos en tu navegador:

1. **Accede al portal:**
   Dirígete a [Google AI Studio](https://aistudio.google.com/) e inicia sesión con tu cuenta de Google (personal o institucional).

2. **Ir al menú de Claves de API:**
   En la esquina superior izquierda de la pantalla, haz clic en el botón azul que dice **"Get API key"** (Obtener clave de API).

3. **Crear una nueva clave:**
   - Haz clic en el botón **"Create API key"** (Crear clave de API).
   - Se te presentarán dos opciones principales:
     - **Crear clave de API en un proyecto nuevo de Google Cloud:** Recomendado si es tu primera vez y quieres mantener las cosas simples.
     - **Crear clave de API en un proyecto existente:** Útil si ya estás administrando otros recursos en Google Cloud Console.
   - Elige **"Create API key in new project"** (Crear clave de API en un nuevo proyecto).

4. **Copiar la clave generada:**
   Una vez que el sistema termine de crear el recurso, se abrirá un cuadro de diálogo con una cadena de texto larga (por ejemplo, `AIzaSy...`).
   - Haz clic en **"Copy"** (Copiar).
   - Guárdala temporalmente en un lugar seguro (por ejemplo, un bloc de notas local). **No compartas esta clave con nadie.**

---

## ⚙️ Paso 2: Configurar la Clave de API en el Proyecto

El script `cv_optimizer.py` busca la variable de entorno `GEMINI_API_KEY` para autenticar las peticiones. Tienes dos métodos principales para configurarla localmente:

### Método A: Archivo `.env` (Recomendado y más persistente)

Este método es ideal porque evita que tengas que configurar la variable cada vez que abres una terminal nueva.

1. Ve a la raíz de tu proyecto `cvgen/`.
2. Duplica el archivo `.env.example` y renómbralo a `.env` (o crea un archivo nuevo de texto llamado `.env`).
3. Abre el archivo `.env` con tu editor de texto favorito y agrega la clave que copiaste anteriormente:
   ```env
   GEMINI_API_KEY=tu_clave_de_api_secreta_aqui
   ```
4. Guarda el archivo. El script utiliza `python-dotenv` para cargar este archivo automáticamente al ejecutarse.
