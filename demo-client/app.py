#
# Copyright Â© 2026 ZTUnion LLC. All rights reserved.
#
import json
import threading
import urllib.parse
import requests
import tkinter as tk
from tkinter import ttk, messagebox


DEFAULT_PROXY_URL = "http://34.95.56.239:18080"

PROVIDERS = {
    "OpenAI": {
        "model": "gpt-4o-mini",
        "key_label_direct": "OpenAI API Key",
        "key_label_proxy": "OpenAI Virtual API Key",
    },
    "Anthropic": {
        "model": "claude-3-5-haiku-latest",
        "key_label_direct": "Anthropic API Key",
        "key_label_proxy": "Anthropic Virtual API Key",
    },
    "Gemini": {
        "model": "gemini-1.5-flash",
        "key_label_direct": "Gemini API Key",
        "key_label_proxy": "Gemini Virtual API Key",
    },
    "HuggingFace": {
        "model": "openai/gpt-oss-120b:fastest",
        "key_label_direct": "HuggingFace Token",
        "key_label_proxy": "HuggingFace Virtual API Key",
    },
}


def is_proxy_mode():
    return mode_var.get() == "proxy"


def selected_provider():
    return provider_var.get()


def update_mode_ui(*_):
    provider = selected_provider()
    config = PROVIDERS[provider]

    model_entry.delete(0, tk.END)
    model_entry.insert(0, config["model"])

    if is_proxy_mode():
        banner.config(
            bg="#dcfce7",
            fg="#166534",
            text=f"🟢 Willamette Proxy Mode: Virtual Key → Proxy → CMS → {provider}",
        )
        key_label.config(text=config["key_label_proxy"])
        key_hint.config(text="Use the virtual API key generated from Willamette CMS.")
        proxy_frame.grid()
        status_var.set(f"Mode: Willamette Proxy | Provider: {provider}")
    else:
        banner.config(
            bg="#dbeafe",
            fg="#1e40af",
            text=f"🔵 Direct Provider Mode: Real Key → {provider}",
        )
        key_label.config(text=config["key_label_direct"])
        key_hint.config(text="Use the real provider key/token.")
        proxy_frame.grid_remove()
        status_var.set(f"Mode: Direct Provider | Provider: {provider}")


def append_chat(sender, message):
    chat_text.config(state=tk.NORMAL)
    chat_text.insert(tk.END, f"{sender}\n", "sender")
    chat_text.insert(tk.END, f"{message}\n\n", "message")
    chat_text.config(state=tk.DISABLED)
    chat_text.see(tk.END)


def set_busy(busy):
    send_button.config(state=tk.DISABLED if busy else tk.NORMAL)


def toggle_key_visibility():
    if show_key_var.get():
        key_entry.config(show="")
        show_key_button.config(text="Hide")
    else:
        key_entry.config(show="*")
        show_key_button.config(text="Show")


def build_proxy_kwargs():
    if not is_proxy_mode():
        return {}

    proxy_url = proxy_entry.get().strip()

    return {
        "proxies": {
            "http": proxy_url,
            "https": proxy_url,
        },
        "verify": False,
    }


def send_request():
    key = key_entry.get().strip()
    prompt = prompt_text.get("1.0", tk.END).strip()
    provider = selected_provider()
    model = model_entry.get().strip()

    if not key:
        messagebox.showerror("Missing key", "Please enter a key.")
        return

    if not model:
        messagebox.showerror("Missing model", "Please enter a model.")
        return

    if not prompt:
        messagebox.showerror("Missing message", "Please enter a message.")
        return

    append_chat("You", prompt)
    prompt_text.delete("1.0", tk.END)

    set_busy(True)
    status_var.set("Sending request...")

    thread = threading.Thread(
        target=send_provider_request,
        args=(provider, model, key, prompt),
        daemon=True,
    )
    thread.start()


def send_provider_request(provider, model, key, prompt):
    try:
        if provider == "OpenAI":
            result = call_openai(model, key, prompt)
        elif provider == "Anthropic":
            result = call_anthropic(model, key, prompt)
        elif provider == "Gemini":
            result = call_gemini(model, key, prompt)
        elif provider == "HuggingFace":
            result = call_huggingface(model, key, prompt)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        root.after(0, lambda: append_chat("Assistant", result))
        root.after(0, lambda: status_var.set("Success"))

    except requests.HTTPError as exc:
        response = exc.response

        try:
            body = response.json()
            message = json.dumps(body, indent=2)
        except Exception:
            message = response.text

        root.after(0, lambda: append_chat("Error", message))
        root.after(0, lambda: status_var.set(f"HTTP {response.status_code}"))

    except Exception as exc:
        root.after(0, lambda: append_chat("Error", str(exc)))
        root.after(0, lambda: status_var.set("Request failed"))

    finally:
        root.after(0, lambda: set_busy(False))


def call_openai(model, key, prompt):
    url = "https://api.openai.com/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=90,
        **build_proxy_kwargs(),
    )

    response.raise_for_status()
    data = response.json()

    return data["choices"][0]["message"]["content"]


def call_anthropic(model, key, prompt):
    url = "https://api.anthropic.com/v1/messages"

    headers = {
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "max_tokens": 1024,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=90,
        **build_proxy_kwargs(),
    )

    response.raise_for_status()
    data = response.json()

    parts = []

    for item in data.get("content", []):
        if item.get("type") == "text":
            parts.append(item.get("text", ""))

    return "\n".join(parts).strip() or json.dumps(data, indent=2)


def call_gemini(model, key, prompt):
    encoded_model = urllib.parse.quote(model, safe="")
    encoded_key = urllib.parse.quote(key, safe="")

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{encoded_model}:generateContent?key={encoded_key}"
    )

    headers = {
        "Content-Type": "application/json",
    }

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": prompt,
                    }
                ],
            }
        ],
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=90,
        **build_proxy_kwargs(),
    )

    response.raise_for_status()
    data = response.json()

    candidates = data.get("candidates", [])
    if not candidates:
        return json.dumps(data, indent=2)

    parts = candidates[0].get("content", {}).get("parts", [])
    text_parts = [
        part.get("text", "")
        for part in parts
        if "text" in part
    ]

    return "\n".join(text_parts).strip() or json.dumps(data, indent=2)


def call_huggingface(model, key, prompt):
    url = "https://router.huggingface.co/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "stream": False,
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=90,
        **build_proxy_kwargs(),
    )

    response.raise_for_status()
    data = response.json()

    return data["choices"][0]["message"]["content"]


root = tk.Tk()
root.title("Willamette Demo Client")
root.geometry("980x720")
root.minsize(820, 560)
root.configure(bg="#f8fafc")

style = ttk.Style()
style.theme_use("clam")
style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=8)

root.grid_rowconfigure(2, weight=1)
root.grid_columnconfigure(0, weight=1)

header = tk.Frame(root, bg="#f8fafc", padx=18, pady=14)
header.grid(row=0, column=0, sticky="ew")
header.grid_columnconfigure(0, weight=1)

title = tk.Label(
    header,
    text="Willamette Demo Client",
    bg="#f8fafc",
    fg="#111827",
    font=("Segoe UI", 20, "bold"),
)
title.grid(row=0, column=0, sticky="w")

banner = tk.Label(
    header,
    text="",
    anchor="w",
    justify="left",
    padx=14,
    pady=10,
    font=("Segoe UI", 10, "bold"),
)
banner.grid(row=1, column=0, sticky="ew", pady=(12, 0))

config = tk.Frame(
    root,
    bg="#ffffff",
    padx=16,
    pady=14,
    highlightbackground="#e5e7eb",
    highlightthickness=1,
)
config.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 12))
config.grid_columnconfigure(1, weight=1)
config.grid_columnconfigure(3, weight=1)

mode_var = tk.StringVar(value="direct")

tk.Label(
    config,
    text="Mode",
    bg="#ffffff",
    fg="#111827",
    font=("Segoe UI", 10, "bold"),
).grid(row=0, column=0, sticky="w", padx=(0, 10))

tk.Radiobutton(
    config,
    text="Direct Provider",
    variable=mode_var,
    value="direct",
    command=update_mode_ui,
    bg="#ffffff",
    font=("Segoe UI", 10),
).grid(row=0, column=1, sticky="w")

tk.Radiobutton(
    config,
    text="Willamette Proxy",
    variable=mode_var,
    value="proxy",
    command=update_mode_ui,
    bg="#ffffff",
    font=("Segoe UI", 10),
).grid(row=0, column=2, sticky="w", padx=(16, 8))

proxy_frame = tk.Frame(config, bg="#ffffff")
proxy_frame.grid(row=0, column=3, sticky="ew")
proxy_frame.grid_columnconfigure(1, weight=1)

tk.Label(
    proxy_frame,
    text="Proxy",
    bg="#ffffff",
    fg="#111827",
    font=("Segoe UI", 10, "bold"),
).grid(row=0, column=0, sticky="w", padx=(0, 8))

proxy_entry = tk.Entry(proxy_frame, font=("Segoe UI", 10))
proxy_entry.insert(0, DEFAULT_PROXY_URL)
proxy_entry.grid(row=0, column=1, sticky="ew")

tk.Label(
    config,
    text="Provider",
    bg="#ffffff",
    fg="#111827",
    font=("Segoe UI", 10, "bold"),
).grid(row=1, column=0, sticky="w", pady=(14, 0), padx=(0, 10))

provider_var = tk.StringVar(value="OpenAI")

provider_combo = ttk.Combobox(
    config,
    textvariable=provider_var,
    values=list(PROVIDERS.keys()),
    state="readonly",
)
provider_combo.grid(row=1, column=1, sticky="ew", pady=(14, 0))
provider_combo.bind("<<ComboboxSelected>>", update_mode_ui)

tk.Label(
    config,
    text="Model",
    bg="#ffffff",
    fg="#111827",
    font=("Segoe UI", 10, "bold"),
).grid(row=1, column=2, sticky="w", pady=(14, 0), padx=(16, 10))

model_entry = tk.Entry(config, font=("Segoe UI", 10))
model_entry.grid(row=1, column=3, sticky="ew", pady=(14, 0))

key_label = tk.Label(
    config,
    text="Provider API Key",
    bg="#ffffff",
    fg="#111827",
    font=("Segoe UI", 10, "bold"),
)
key_label.grid(row=2, column=0, sticky="w", pady=(14, 0), padx=(0, 10))

key_input_frame = tk.Frame(config, bg="#ffffff")
key_input_frame.grid(row=2, column=1, columnspan=3, sticky="ew", pady=(14, 0))
key_input_frame.grid_columnconfigure(0, weight=1)

key_entry = tk.Entry(
    key_input_frame,
    show="*",
    font=("Segoe UI", 10),
)
key_entry.grid(row=0, column=0, sticky="ew")

show_key_var = tk.BooleanVar(value=False)

show_key_button = ttk.Checkbutton(
    key_input_frame,
    text="Show",
    variable=show_key_var,
    command=toggle_key_visibility,
)
show_key_button.grid(row=0, column=1, padx=(10, 0))

key_hint = tk.Label(
    config,
    text="",
    bg="#ffffff",
    fg="#6b7280",
    font=("Segoe UI", 9),
)
key_hint.grid(row=3, column=1, columnspan=3, sticky="w", pady=(4, 0))

chat_frame = tk.Frame(
    root,
    bg="#ffffff",
    padx=16,
    pady=14,
    highlightbackground="#e5e7eb",
    highlightthickness=1,
)
chat_frame.grid(row=2, column=0, sticky="nsew", padx=18, pady=(0, 12))
chat_frame.grid_rowconfigure(1, weight=1)
chat_frame.grid_columnconfigure(0, weight=1)

tk.Label(
    chat_frame,
    text="Conversation",
    bg="#ffffff",
    fg="#111827",
    font=("Segoe UI", 11, "bold"),
).grid(row=0, column=0, sticky="w", pady=(0, 8))

chat_text = tk.Text(
    chat_frame,
    state=tk.DISABLED,
    wrap=tk.WORD,
    bg="#f9fafb",
    fg="#111827",
    font=("Segoe UI", 10),
    relief="flat",
    padx=10,
    pady=10,
)
chat_text.grid(row=1, column=0, sticky="nsew")

chat_scroll = ttk.Scrollbar(chat_frame, command=chat_text.yview)
chat_scroll.grid(row=1, column=1, sticky="ns")
chat_text.config(yscrollcommand=chat_scroll.set)

chat_text.tag_configure(
    "sender",
    font=("Segoe UI", 10, "bold"),
    foreground="#2563eb",
)

chat_text.tag_configure(
    "message",
    font=("Segoe UI", 10),
    foreground="#111827",
)

bottom = tk.Frame(
    root,
    bg="#ffffff",
    padx=16,
    pady=12,
    highlightbackground="#e5e7eb",
    highlightthickness=1,
)
bottom.grid(row=3, column=0, sticky="ew", padx=18, pady=(0, 12))
bottom.grid_columnconfigure(0, weight=1)

tk.Label(
    bottom,
    text="Message",
    bg="#ffffff",
    fg="#111827",
    font=("Segoe UI", 10, "bold"),
).grid(row=0, column=0, sticky="w")

prompt_text = tk.Text(
    bottom,
    height=3,
    wrap=tk.WORD,
    font=("Segoe UI", 10),
)
prompt_text.grid(row=1, column=0, sticky="ew", pady=(6, 0))

send_button = ttk.Button(
    bottom,
    text="Send",
    command=send_request,
)
send_button.grid(row=1, column=1, sticky="se", padx=(12, 0), pady=(6, 0))

status_var = tk.StringVar(value="Ready")
status = tk.Label(
    root,
    textvariable=status_var,
    bg="#f8fafc",
    fg="#374151",
    font=("Segoe UI", 9),
)
status.grid(row=4, column=0, sticky="w", padx=18, pady=(0, 10))

update_mode_ui()

root.mainloop()