#
# Copyright © 2026 ZTUnion LLC. All rights reserved.
#

import os
import sys
 
from openai import OpenAI
 
if not os.environ.get("OPENAI_API_KEY"):
    sys.exit("OPENAI_API_KEY is empty. export OPENAI_API_KEY=....")
 
MODEL = "gpt-5.5"
 
client = OpenAI()
 
messages = [
    {"role": "system", "content": "Reply in short."},
]
 
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
 
    messages.append({"role": "user", "content": question})
 
    print("Answer> ", end="", flush=True)
    answer_parts = []
    try:
        stream = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                answer_parts.append(delta)
                print(delta, end="", flush=True)
        print("\n")
    except Exception as e:
        messages.pop()
        print(f"\n[Error] {e}\n")
        continue
 
    messages.append({"role": "assistant", "content": "".join(answer_parts)})
