#
# Copyright © 2026 ZTUnion LLC. All rights reserved.
#

import os
import sys
 
from google import genai
from google.genai import types
 
if not os.environ.get("GEMINI_API_KEY"):
    sys.exit("GEMINI_API_KEY is empty. export GEMINI_API_KEY=....")
 
MODEL = "gemini-3.5-flash"
SYSTEM = "Reply in short."
 
client = genai.Client()
 
chat = client.chats.create(
    model=MODEL,
    config=types.GenerateContentConfig(system_instruction=SYSTEM),
)
 
print(f"Model: {MODEL}  (End: exit or Ctrl+C)\n")
 
while True:
    try:
        question = input("Query> ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nEnding Session.")
        break
 
    if not question:
        continue
    if question.lower() in ("exit", "quit"):
        print("Ending Session.")
        break
 
    print("Answer> ", end="", flush=True)
    try:
        for chunk in chat.send_message_stream(question):
            if chunk.text:
                print(chunk.text, end="", flush=True)
        print("\n")
    except Exception as e:
        print(f"\n[Error] {e}\n")
        history = chat.get_history()
        if history and history[-1].role == "user":
            chat = client.chats.create(
                model=MODEL,
                config=types.GenerateContentConfig(system_instruction=SYSTEM),
                history=history[:-1],
            )
        continue
