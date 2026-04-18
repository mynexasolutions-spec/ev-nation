import re
from urllib.parse import quote


_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
_MULTI_UNDERSCORE_RE = re.compile(r"_+")
_HEX_COLOR_RE = re.compile(r"^#[0-9A-F]{6}$")


def normalize_slug(value: str) -> str:
    normalized = _NON_ALNUM_RE.sub("-", value.strip().lower()).strip("-")
    return normalized


def normalize_spec_key(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    return _MULTI_UNDERSCORE_RE.sub("_", normalized)


def normalize_phone(value: str) -> str:
    trimmed = value.strip()
    digits = re.sub(r"\D", "", trimmed)
    if not digits:
        return ""
    return f"+{digits}" if trimmed.startswith("+") else digits


def normalize_hex_color(value: str | None) -> str | None:
    if value is None:
        return None

    candidate = value.strip().upper()
    if not candidate:
        return None
    if not candidate.startswith("#"):
        candidate = f"#{candidate}"
    if not _HEX_COLOR_RE.fullmatch(candidate):
        raise ValueError("Color code must be a valid 6-digit hex value.")
    return candidate


def compact_whitespace(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(value.split())
    return cleaned or None


def build_whatsapp_url(phone_number: str, message: str) -> str:
    normalized_phone = normalize_phone(phone_number).lstrip("+")
    return f"https://wa.me/{normalized_phone}?text={quote(message)}"
