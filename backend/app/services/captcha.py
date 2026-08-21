import hashlib
import random
import secrets
import time
import uuid
from dataclasses import dataclass

import jwt

from app.core.security import create_captcha_token, decode_captcha_token

# Ambiguous glyphs (0/O, 1/I/L/l) are excluded so the code is never a coin-flip
# to read even before the distortion is applied — L is excluded alongside the
# usual I/O/0/1 because the code is displayed lowercase, where "l" reads as "1".
_CAPTCHA_CHARS = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"
_CODE_LENGTH = 5
_EXPIRE_MINUTES = 5
_WIDTH, _HEIGHT = 140, 50
_BACKGROUND = "#eef7ef"
_COLORS = ["#2a78d6", "#22a35e", "#c2412d", "#7e14ff", "#c98a12", "#1f9c9c"]

# Each captcha token is meant to authorize exactly one /auth/login attempt.
# Since verification is a stateless signed token (works across process
# restarts, needs no DB table for something this short-lived), single-use is
# enforced with a small in-memory "already spent" set instead — a captured
# valid token+answer can't be replayed for a second login attempt. Entries
# are pruned by their own expiry on every check, so this never grows unbounded.
_spent_jtis: dict[str, float] = {}


def _prune_spent() -> None:
    now = time.time()
    expired = [jti for jti, exp in _spent_jtis.items() if exp < now]
    for jti in expired:
        del _spent_jtis[jti]


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def _render_svg(code: str) -> str:
    rng = random.Random(secrets.randbits(64))
    seed = rng.randint(1, 999)
    display = code.lower()

    char_width = _WIDTH / (len(display) + 1)
    chars_svg = []
    for i, ch in enumerate(display):
        x = char_width * (i + 0.8)
        color = rng.choice(_COLORS)
        chars_svg.append(
            f'<text x="{x:.1f}" y="{_HEIGHT / 2 + 8}" font-size="26" '
            'font-family="\'Comic Sans MS\', \'Trebuchet MS\', sans-serif" font-weight="700" '
            f'fill="{color}" text-anchor="middle">{ch}</text>'
        )

    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" '
        f'viewBox="0 0 {_WIDTH} {_HEIGHT}" preserveAspectRatio="xMidYMid meet">'
        '<defs><filter id="warp" x="-20%" y="-20%" width="140%" height="140%">'
        f'<feTurbulence type="fractalNoise" baseFrequency="0.01 0.1" numOctaves="2" seed="{seed}" result="turb"/>'
        '<feDisplacementMap in="SourceGraphic" in2="turb" scale="6"/>'
        "</filter></defs>"
        f'<rect width="{_WIDTH}" height="{_HEIGHT}" fill="{_BACKGROUND}"/>'
        '<g filter="url(#warp)">' + "".join(chars_svg) + "</g></svg>"
    )
    return svg


@dataclass
class CaptchaChallenge:
    captcha_token: str
    image_svg: str


def create_captcha() -> CaptchaChallenge:
    code = "".join(secrets.choice(_CAPTCHA_CHARS) for _ in range(_CODE_LENGTH))
    jti = uuid.uuid4().hex
    token = create_captcha_token(jti, _hash_code(code), _EXPIRE_MINUTES)
    # Sent as raw SVG markup — not a data: URI for an <img> tag — because
    # Safari/WebKit (both desktop and iOS) silently drops SVG <filter>
    # effects (the feTurbulence/feDisplacementMap warp) on SVGs loaded as an
    # external image resource. Inlining the markup into the page's own DOM
    # is the only reliably cross-browser way to keep the filter rendering.
    svg = _render_svg(code)
    return CaptchaChallenge(captcha_token=token, image_svg=svg)


def verify_and_consume_captcha(token: str, answer: str) -> bool:
    _prune_spent()
    try:
        payload = decode_captcha_token(token)
    except jwt.PyJWTError:
        return False

    jti = payload.get("jti")
    if not jti or jti in _spent_jtis:
        return False
    _spent_jtis[jti] = payload["exp"]

    expected_hash = payload.get("code_hash", "")
    actual_hash = _hash_code((answer or "").strip().upper())
    return secrets.compare_digest(expected_hash, actual_hash)
