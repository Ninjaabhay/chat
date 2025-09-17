import os
import re
from typing import List

import chainlit as cl
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("Set GEMINI_API_KEY in .env or environment!")

client = genai.Client()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

CRISIS_KEYWORDS = [
    r"\bkill myself\b", r"\bkill me\b", r"\bsuicid", r"\bwant to die\b",
    r"\bharm myself\b", r"\bno reason to live\b", r"\boverdose\b"
]

CRISIS_RESP = (
    "I'm really sorry you're feeling this way. I'm just a chatbot and not a replacement "
    "for professional help, but I want you to be safe. If you are in immediate danger, "
    "please call your local emergency number right now.\n\n"
    "You can also reach:\n"
    "- India: Call 14416 (Manas -Mental health Support )\n\n"
    "Would you like me to help you find local resources?"
)

SYSTEM_PROMPT = (
    "You are a compassionate mental health support assistant. "
    "Be empathetic, non-judgmental, and encourage seeking professional help. "
    "Do not give medical diagnoses."
)

# Use Chainlit's session state for history


def append_history(role: str, content: str):
    hist = cl.user_session.get("history", [])
    hist.append({"role": role, "content": content})
    cl.user_session.set("history", hist[-10:])  # keep last 10


def get_history() -> List[dict]:
    return cl.user_session.get("history", [])


def looks_like_crisis(text: str) -> bool:
    return any(re.search(p, text.lower()) for p in CRISIS_KEYWORDS)


@cl.on_chat_start
async def start():
    """Called at start of chat."""
    cl.user_session.set("history", [])
    append_history("system", SYSTEM_PROMPT)
    welcome = "Hi — I'm here to listen. What's on your mind?"
    append_history("assistant", welcome)
    await cl.Message(
        content="🌸 Hi, I’m **SoulSync** — your mental health companion.\n\n"
                "I’m here to listen, support, and guide you towards positivity. 💙",
        author="SoulSync"  # This sets the displayed author name
    ).send()


@cl.on_message
async def main(message: cl.Message):
    """Handle each incoming user message."""
    user_text = message.content.strip()
    append_history("user", user_text)

    # Crisis check
    if looks_like_crisis(user_text):
        append_history("assistant", CRISIS_RESP)
        await cl.Message(content=CRISIS_RESP).send()
        return

    # Prepare content for Gemini
    hist = get_history()
    content_parts = [f"{h['role'].capitalize()}: {h['content']}" for h in hist]
    content_parts.append(f"User: {user_text}")

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=content_parts,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0)
            ),
        )
        bot_text = response.text or "Sorry, I couldn’t generate a reply."
    except Exception as e:
        print("Gemini error:", e)
        bot_text = "I'm having trouble responding right now. Please try again later."

    append_history("assistant", bot_text)
    await cl.Message(content=bot_text).send()
