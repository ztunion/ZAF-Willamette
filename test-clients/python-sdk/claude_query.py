#
# Copyright © 2026 ZTUnion LLC. All rights reserved.
#

import os
import sys
 
from anthropic import Anthropic
 
if not os.environ.get("ANTHROPIC_API_KEY"):
    sys.exit("ANTHROPIC_API_KEY is empty. export ANTHROPIC_API_KEY=....")
 
MODEL = "claude-sonnet-4-6"
SYSTEM = "ê°„ê²°í•˜ê²Œ í•œêµ­ì–´ë¡œ ë‹µí•˜ë¼."
MAX_TOKENS = 1024
 
client = Anthropic()
 
messages = []
 
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
        with client.messages.stream(
            model=MODEL,
            system=SYSTEM,
            messages=messages,
            max_tokens=MAX_TOKENS,
        ) as stream:
            for text in stream.text_stream:
                answer_parts.append(text)
                print(text, end="", flush=True)
        print("\n")
    except Exception as e:
        messages.pop()
        print(f"\n[Error] {e}\n")
        continue
 
    messages.append({"role": "assistant", "content": "".join(answer_parts)})
