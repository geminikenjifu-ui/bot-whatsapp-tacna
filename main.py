import os
import sqlite3
import httpx
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse

app = FastAPI()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "tacna_secreto_2026")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "1425322544000697")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
MODELO_IA = os.getenv("MODELO_IA", "google/gemini-2.5-flash")

PROMPT_NEGOCIO = """
Eres el asesor comercial de una tienda de celulares de gama alta en Tacna, Perú.
Responde de forma amable, directa y persuasiva (máximo 3 a 4 líneas por mensaje).

CATÁLOGO Y PRECIOS:
- Samsung Galaxy S24 Ultra 256GB (Nuevo sellado): S/ 3,850 | Seminuevo impecable (10/10): S/ 3,200.
- Samsung Galaxy S23 Ultra 256GB (Seminuevo 9.5/10): S/ 2,450.
- iPhone 15 Pro Max 256GB (Batería 95%+): S/ 3,950.
- iPhone 14 Pro 128GB (Batería 90%+): S/ 2,650.

ENTREGAS EN TACNA:
- Lunes a sábado de 9:30 a.m. a 8:00 p.m.
- Puntos seguros: Plaza Zela, Paseo Cívico, Plaza Vea (Av. Bolognesi) o Galería Coronel Mendoza.
- Pagos: Yape, Plin, transferencia BCP/Interbank o efectivo al revisar el equipo.
- Rebaja máxima autorizada: S/ 50 solo si concreta hoy.
"""


def iniciar_db():
    conn = sqlite3.connect("clientes.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS historial (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telefono TEXT NOT NULL,
            rol TEXT NOT NULL,
            contenido TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


iniciar_db()


def guardar_mensaje(telefono: str, rol: str, contenido: str):
    conn = sqlite3.connect("clientes.db")
    conn.execute(
        "INSERT INTO historial (telefono, rol, contenido) VALUES (?, ?, ?)",
        (telefono, rol, contenido),
    )
    conn.commit()
    conn.close()


def obtener_historial(telefono: str, limite: int = 10) -> list[dict]:
    conn = sqlite3.connect("clientes.db")
    cursor = conn.execute(
        "SELECT rol, contenido FROM historial WHERE telefono = ? ORDER BY id DESC LIMIT ?",
        (telefono, limite),
    )
    filas = cursor.fetchall()[::-1]
    conn.close()
    return [{"role": r, "content": c} for r, c in filas]


async def responder_con_ia(telefono: str, texto: str) -> str:
    guardar_mensaje(telefono, "user", texto)
    mensajes = [{"role": "system", "content": PROMPT_NEGOCIO}] + obtener_historial(telefono)

    async with httpx.AsyncClient(timeout=25.0) as client:
        resp = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODELO_IA,
                "messages": mensajes,
                "temperature": 0.4,
                "max_tokens": 500,
            },
        )
        if resp.status_code >= 400:
            print("OPENROUTER ERROR:", resp.status_code, resp.text)
        resp.raise_for_status()

        data_ia = resp.json()
        contenido = data_ia.get("choices", [{}])[0].get("message", {}).get("content")
        respuesta = (
            contenido.strip()
            if contenido
            else "Hola, gracias por escribirnos. ¿Qué modelo de celular de nuestro catálogo en Tacna te interesa?"
        )

    guardar_mensaje(telefono, "assistant", respuesta)
    return respuesta


async def enviar_whatsapp(destino: str, texto: str):
    url = f"https://graph.facebook.com/v25.0/{PHONE_NUMBER_ID}/messages"
    async with httpx.AsyncClient(timeout=15.
