#
# Copyright © 2026 ZTUnion LLC. All rights reserved.
#

import os
import sys
 
from huggingface_hub import InferenceClient
 
TOKEN = os.environ.get("HF_TOKEN")
if not TOKEN:
    sys.exit("HF_TOKEN is empty. export HF_TOKEN=....")
 
MODEL = "Qwen/Qwen2.5-7B-Instruct"
 
client = InferenceClient(token=TOKEN)
 
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
        stream = client.chat_completion(
            model=MODEL,
            messages=messages,
            max_tokens=500,
            temperature=0.7,
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
