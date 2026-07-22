#
# Copyright Â© 2026 ZTUnion LLC. All rights reserved.
#
import secrets
import string

from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth import (
    verify_login,
    create_session_token,
    verify_session_token,
)

from app.secret_store import create_or_update_secret

from app.storage import (
    save_api_key_record,
    get_api_key_record,
    list_api_key_records,
    delete_api_key_record,
)


app = FastAPI(title="Willamette CMS Console")

templates = Jinja2Templates(directory="app/templates")


def extract_key_prefix(real_api_key: str) -> str:
    key = real_api_key.strip()

    if not key:
        return "vk-"

    # First preference:
    # preserve everything up to the last '_' or '-'
    last_separator = max(
        key.rfind("_"),
        key.rfind("-"),
    )

    if last_separator != -1:
        return key[: last_separator + 1]

    # Otherwise preserve:
    # leading letters + immediately following digits

    index = 0

    while index < len(key) and key[index].isalpha():
        index += 1

    while index < len(key) and key[index].isdigit():
        index += 1

    if index == 0:
        index = min(8, len(key))

    return key[:index]


def generate_virtual_key(real_api_key: str) -> str:
    prefix = extract_key_prefix(real_api_key)

    chars = string.ascii_letters + string.digits

    return prefix + "".join(
        secrets.choice(chars)
        for _ in range(48)
    )

def build_secret_id(
    virtual_api_key: str,
) -> str:
    safe_secret_id = ""

    for char in virtual_api_key:
        if char.isalnum():
            safe_secret_id += char
        else:
            safe_secret_id += "-"

    safe_secret_id = safe_secret_id.strip("-")

    return f"api-key-{safe_secret_id}"


def parse_csv(value: str) -> list[str]:
    if not value:
        return []

    return [
        item.strip()
        for item in value.split(",")
        if item.strip()
    ]


def checkbox_enabled(value: str | None) -> bool:
    return value == "on"


def require_login(request: Request) -> bool:
    token = request.cookies.get("cms_session")
    return verify_session_token(token)


def normalize_record(record: dict) -> dict:
    policy = record.get("policy", {})

    return {
        "virtual_api_key": record.get("virtual_api_key", ""),
        "provider": record.get("provider", "unknown"),
        "status": record.get("status", "active"),
        "owner": record.get("owner", "unknown"),
        "policy": {
            "ip_validation_enabled": policy.get("ip_validation_enabled", False),
            "allowed_ip_ranges": policy.get("allowed_ip_ranges", []),
            "ja3_validation_enabled": policy.get("ja3_validation_enabled", False),
            "allowed_ja3": policy.get("allowed_ja3", []),
            "ja4_validation_enabled": policy.get("ja4_validation_enabled", False),
            "allowed_ja4": policy.get("allowed_ja4", []),
            "country_validation_enabled": policy.get("country_validation_enabled", False),
            "allowed_countries": policy.get("allowed_countries", []),
        },
    }


def list_api_keys_for_dashboard() -> dict:
    records = list_api_key_records()
    result = {}

    for record in records:
        normalized = normalize_record(record)
        virtual_key = normalized["virtual_api_key"]
        result[virtual_key] = normalized

    return result


def build_policy(
    ip_validation_enabled: str | None,
    allowed_ip_ranges: str,
    ja3_validation_enabled: str | None,
    allowed_ja3: str,
    ja4_validation_enabled: str | None,
    allowed_ja4: str,
    country_validation_enabled: str | None,
    allowed_countries: list[str],
) -> dict:
    return {
        "ip_validation_enabled": checkbox_enabled(ip_validation_enabled),
        "allowed_ip_ranges": parse_csv(allowed_ip_ranges),
        "ja3_validation_enabled": checkbox_enabled(ja3_validation_enabled),
        "allowed_ja3": parse_csv(allowed_ja3),
        "ja4_validation_enabled": checkbox_enabled(ja4_validation_enabled),
        "allowed_ja4": parse_csv(allowed_ja4),
        "country_validation_enabled": checkbox_enabled(country_validation_enabled),
        "allowed_countries": allowed_countries,
    }


@app.get("/")
def root():
    return RedirectResponse(
        url="/login",
        status_code=302,
    )


@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        request,
        "login.html",
        {
            "error": None,
        },
    )


@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    if not verify_login(username, password):
        return templates.TemplateResponse(
            request,
            "login.html",
            {
                "error": "Invalid credentials",
            },
            status_code=401,
        )

    token = create_session_token(username)

    response = RedirectResponse(
        url="/dashboard",
        status_code=302,
    )

    response.set_cookie(
        key="cms_session",
        value=token,
        httponly=True,
        samesite="lax",
    )

    return response


@app.get("/dashboard")
def dashboard(request: Request):
    if not require_login(request):
        return RedirectResponse(
            url="/login",
            status_code=302,
        )

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "api_keys": list_api_keys_for_dashboard(),
            "created_key": None,
            "edit_item": None,
            "message": None,
        },
    )


@app.post("/api-keys")
def add_api_key(
    request: Request,
    provider: str = Form(...),
    real_api_key: str = Form(...),
    ip_validation_enabled: str | None = Form(None),
    allowed_ip_ranges: str = Form(""),
    ja3_validation_enabled: str | None = Form(None),
    allowed_ja3: str = Form(""),
    ja4_validation_enabled: str | None = Form(None),
    allowed_ja4: str = Form(""),
    country_validation_enabled: str | None = Form(None),
    allowed_countries: list[str] = Form([]),
):
    if not require_login(request):
        return RedirectResponse(
            url="/login",
            status_code=302,
        )

    normalized_provider = provider.lower()
    virtual_api_key = generate_virtual_key(real_api_key)
    secret_id = build_secret_id(virtual_api_key)

    secret_version = create_or_update_secret(
        secret_id=secret_id,
        secret_value=real_api_key,
    )

    policy = build_policy(
        ip_validation_enabled,
        allowed_ip_ranges,
        ja3_validation_enabled,
        allowed_ja3,
        ja4_validation_enabled,
        allowed_ja4,
        country_validation_enabled,
        allowed_countries,
    )

    record = {
        "virtual_api_key": virtual_api_key,
        "provider": normalized_provider,
        "secret_version": secret_version,
        "status": "active",
        "owner": "web-console-user",
        "policy": policy,
    }

    save_api_key_record(
        virtual_api_key,
        record,
    )

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "api_keys": list_api_keys_for_dashboard(),
            "created_key": virtual_api_key,
            "edit_item": None,
            "message": "API key created successfully.",
        },
    )


@app.get("/api-keys/{virtual_api_key}/edit")
def edit_api_key_page(
    request: Request,
    virtual_api_key: str,
):
    if not require_login(request):
        return RedirectResponse(
            url="/login",
            status_code=302,
        )

    record = get_api_key_record(virtual_api_key)

    if not record:
        return templates.TemplateResponse(
            request,
            "dashboard.html",
            {
                "api_keys": list_api_keys_for_dashboard(),
                "created_key": None,
                "edit_item": None,
                "message": "API key not found.",
            },
        )

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "api_keys": list_api_keys_for_dashboard(),
            "created_key": None,
            "edit_item": normalize_record(record),
            "message": None,
        },
    )


@app.post("/api-keys/{virtual_api_key}/edit")
def update_api_key(
    request: Request,
    virtual_api_key: str,
    provider: str = Form(...),
    real_api_key: str = Form(""),
    status: str = Form("active"),
    ip_validation_enabled: str | None = Form(None),
    allowed_ip_ranges: str = Form(""),
    ja3_validation_enabled: str | None = Form(None),
    allowed_ja3: str = Form(""),
    ja4_validation_enabled: str | None = Form(None),
    allowed_ja4: str = Form(""),
    country_validation_enabled: str | None = Form(None),
    allowed_countries: list[str] = Form([]),
):
    if not require_login(request):
        return RedirectResponse(
            url="/login",
            status_code=302,
        )

    existing_record = get_api_key_record(virtual_api_key)

    if not existing_record:
        return templates.TemplateResponse(
            request,
            "dashboard.html",
            {
                "api_keys": list_api_keys_for_dashboard(),
                "created_key": None,
                "edit_item": None,
                "message": "API key not found.",
            },
        )

    secret_version = existing_record.get("secret_version")

    if real_api_key.strip():
        secret_id = build_secret_id(virtual_api_key)
        secret_version = create_or_update_secret(
            secret_id=secret_id,
            secret_value=real_api_key.strip(),
        )

    policy = build_policy(
        ip_validation_enabled,
        allowed_ip_ranges,
        ja3_validation_enabled,
        allowed_ja3,
        ja4_validation_enabled,
        allowed_ja4,
        country_validation_enabled,
        allowed_countries,
    )

    updated_record = {
        "virtual_api_key": virtual_api_key,
        "provider": provider.lower(),
        "secret_version": secret_version,
        "status": status,
        "owner": existing_record.get("owner", "web-console-user"),
        "policy": policy,
    }

    save_api_key_record(
        virtual_api_key,
        updated_record,
    )

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "api_keys": list_api_keys_for_dashboard(),
            "created_key": None,
            "edit_item": None,
            "message": "API key updated successfully.",
        },
    )


@app.post("/api-keys/{virtual_api_key}/delete")
def delete_api_key(
    request: Request,
    virtual_api_key: str,
):
    if not require_login(request):
        return RedirectResponse(
            url="/login",
            status_code=302,
        )

    delete_api_key_record(virtual_api_key)

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "api_keys": list_api_keys_for_dashboard(),
            "created_key": None,
            "edit_item": None,
            "message": "API key deleted successfully.",
        },
    )


@app.post("/logout")
def logout():
    response = RedirectResponse(
        url="/login",
        status_code=302,
    )

    response.delete_cookie("cms_session")

    return response