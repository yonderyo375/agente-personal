# 🧠 Nexus AI — Agente Autónomo

Plataforma completa con agente de IA autónomo basado en Gemini.
Chat con streaming, herramientas MCP, archivos, memoria con Supabase.

---

## 🗂 Estructura del proyecto

```
agente-ia/
├── backend/               ← FastAPI + Python
│   ├── main.py            ← API principal
│   ├── agent.py           ← Lógica del agente
│   ├── memory.py          ← Memoria Supabase
│   ├── requirements.txt
│   ├── render.yaml        ← Config para Render
│   └── tools/
│       ├── registry.py    ← Registro MCP de herramientas
│       ├── web_search.py  ← Búsqueda web
│       ├── code_executor.py ← Ejecutar Python
│       ├── calculator.py  ← Calculadora
│       ├── datetime_tool.py
│       ├── file_reader.py
│       └── file_handler.py
│
├── frontend/              ← Next.js 14
│   ├── app/
│   │   ├── page.tsx       ← Página principal
│   │   ├── layout.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── ChatWindow.tsx ← Ventana de chat
│   │   ├── MessageBubble.tsx ← Burbujas con Markdown
│   │   ├── InputBar.tsx   ← Barra de entrada
│   │   └── Sidebar.tsx    ← Historial de chats
│   ├── lib/
│   │   ├── api.ts         ← Conexión al backend
│   │   └── types.ts
│   └── package.json
│
└── supabase_schema.sql    ← SQL para crear las tablas
```

---

## 🚀 GUÍA DE DEPLOY PASO A PASO

### PASO 1 — Supabase (base de datos)

1. Ve a [supabase.com](https://supabase.com) → tu proyecto
2. Click en **SQL Editor** → **New Query**
3. Pega el contenido de `supabase_schema.sql` y ejecuta (**Run**)
4. Ve a **Settings → API** y copia:
   - `Project URL` → es tu `SUPABASE_URL`
   - `anon public` key → es tu `SUPABASE_KEY`

---

### PASO 2 — GitHub (subir código)

1. Crea un repo en [github.com](https://github.com) llamado `agente-ia`
2. Sube solo la carpeta `backend/` a ese repo:

```bash
# En terminal o Replit
cd agente-ia/backend
git init
git add .
git commit -m "initial commit"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/agente-ia.git
git push -u origin main
```

3. Luego sube la carpeta `frontend/` como otro repo o en la misma carpeta.

---

### PASO 3 — Render (backend)

1. Ve a [render.com](https://render.com) → **New Web Service**
2. Conecta tu repo de GitHub (`agente-ia`)
3. Configuración:
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. En **Environment Variables** agrega:

| Key | Value |
|-----|-------|
| `GEMINI_API_KEY` | tu key de aistudio.google.com |
| `SUPABASE_URL` | del paso 1 |
| `SUPABASE_KEY` | del paso 1 |

5. Click **Create Web Service** — espera 2-3 minutos
6. Copia la URL que te da Render (ej: `https://agente-ia-xxxx.onrender.com`)

---

### PASO 4 — Vercel (frontend)

1. Ve a [vercel.com](https://vercel.com) → **New Project**
2. Importa tu repo de GitHub (la carpeta `frontend/`)
3. En **Environment Variables** agrega:

| Key | Value |
|-----|-------|
| `NEXT_PUBLIC_API_URL` | URL de Render del paso 3 |

4. Click **Deploy** — en 1-2 minutos tienes tu sitio listo
5. Vercel te da una URL gratis: `https://tu-agente.vercel.app`

---

## ✅ RESULTADO FINAL

Tu sitio tendrá:
- 💬 Chat con streaming (texto aparece en tiempo real)
- 📝 Markdown completo (tablas, código con syntax highlighting)
- 🔧 Herramientas MCP (búsqueda web, código Python, calculadora, archivos)
- 📎 Subida de archivos (.txt, .pdf, .py, .json, .csv)
- 🧠 Memoria con Supabase (historial de conversaciones)
- 📱 100% responsive, funciona perfecto en teléfono
- 🔄 Sidebar con historial de chats

---

## ➕ AGREGAR NUEVAS HERRAMIENTAS

Edita `backend/tools/registry.py` y agrega tu herramienta:

```python
Tool(
    name="mi_herramienta",
    description="Descripción de qué hace",
    schema={
        "type": "object",
        "properties": {
            "parametro": {"type": "string", "description": "..."}
        },
        "required": ["parametro"]
    },
    handler=mi_funcion
),
```

---

## 🔑 VARIABLES DE ENTORNO NECESARIAS

| Variable | Dónde obtenerla |
|----------|----------------|
| `GEMINI_API_KEY` | [aistudio.google.com](https://aistudio.google.com) → Get API Key |
| `SUPABASE_URL` | Supabase → Settings → API → Project URL |
| `SUPABASE_KEY` | Supabase → Settings → API → anon public |
| `NEXT_PUBLIC_API_URL` | URL de tu backend en Render |
