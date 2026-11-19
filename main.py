import subprocess
import threading
import time
import pyautogui
import pygetwindow as gw
from google.genai import types


def enviar_whatsapp(contacto: str, mensaje: str) -> str:
    """Busca un contacto en WhatsApp Desktop y le envía un mensaje de texto."""
    print(f"💬 [WHATSAPP] Enviando a '{contacto}': {mensaje}")

    def proceso_whatsapp():
        subprocess.Popen('start "" "whatsapp:"', shell=True)
        time.sleep(2.0)

        ventanas = [w for w in gw.getAllWindows() if "WhatsApp" in w.title]
        if ventanas:
            try:
                if ventanas[0].isMinimized:
                    ventanas[0].restore()
                ventanas[0].activate()
                time.sleep(0.3)
            except Exception:
                pass

        pyautogui.hotkey("ctrl", "f")
        time.sleep(0.3)
        pyautogui.hotkey("ctrl", "a")
        pyautogui.press("backspace")

        subprocess.run("clip", input=contacto.strip().encode("utf-16le"), check=True)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(1.0)

        pyautogui.press("down")
        time.sleep(0.15)
        pyautogui.press("enter")
        time.sleep(0.4)

        subprocess.run("clip", input=mensaje.strip().encode("utf-16le"), check=True)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.2)
        pyautogui.press("enter")

    threading.Thread(target=proceso_whatsapp, daemon=True).start()
    return f"Mensaje enviado a {contacto} por WhatsApp."


SKILL_INFO = {
    "funciones": {
        "enviar_whatsapp": enviar_whatsapp,
    },
    "declaraciones": [
        types.FunctionDeclaration(
            name="enviar_whatsapp",
            description="Busca un contacto en WhatsApp Desktop y le envía un mensaje de texto.",
            behavior="NON_BLOCKING",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "contacto": types.Schema(
                        type="STRING",
                        description="Nombre del contacto o grupo tal como aparece en WhatsApp.",
                    ),
                    "mensaje": types.Schema(
                        type="STRING",
                        description="Texto exacto del mensaje a enviar.",
                    ),
                },
                required=["contacto", "mensaje"],
            ),
        )
    ],
}