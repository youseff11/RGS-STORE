"""Minimal «Sign in with Google» client (OAuth 2.0 / OpenID Connect).

Standard library only — same approach as `dashboard/paypal.py`, so the store
keeps running without any extra package:

    1. the customer clicks the button  → we send them to `auth_url()`
    2. Google sends them back with a one-time `code`
    3. `fetch_profile()` swaps that code for an ID token over HTTPS and reads
       the email / name / picture out of it

The ID token arrives straight from Google's token endpoint over a TLS
connection we opened ourselves, so — as Google's own documentation allows —
its signature does not need to be re-verified locally; what still matters
(issuer, audience, expiry, nonce) is checked in `read_id_token()`.
"""

import base64
import json
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request

from django.urls import reverse

AUTH_ENDPOINT = 'https://accounts.google.com/o/oauth2/v2/auth'
TOKEN_ENDPOINT = 'https://oauth2.googleapis.com/token'
USERINFO_ENDPOINT = 'https://openidconnect.googleapis.com/v1/userinfo'
ISSUERS = ('https://accounts.google.com', 'accounts.google.com')
SCOPE = 'openid email profile'
TIMEOUT = 20
CLOCK_SKEW = 300  # seconds of tolerance for a slow server clock


class GoogleError(Exception):
    """Anything that stops us from trusting what came back from Google."""

    def __init__(self, message, status=None, payload=None):
        super().__init__(message)
        self.status = status
        self.payload = payload or {}


def random_token():
    """A fresh value for the `state` / `nonce` we hand to Google."""
    return secrets.token_urlsafe(24)


def redirect_uri(request, site):
    """The address Google sends the customer back to — it has to match the one
    registered in Google Cloud character for character.

    The saved store URL wins whenever the visitor is actually on that host, so
    a site behind a proxy still gets `https://…` instead of the `http://` the
    proxy reports. Anywhere else (localhost while developing) we build it from
    the request itself.
    """
    path = reverse('google_callback')
    base = ((site.site_url if site else '') or '').strip().rstrip('/')
    if base:
        host = urllib.parse.urlparse(base).netloc.lower()
        if host and host == request.get_host().lower():
            return base + path
    return request.build_absolute_uri(path)


def auth_url(site, redirect_uri, state, nonce):
    """Where to send the customer to pick their Google account."""
    params = {
        'client_id': (site.google_client_id or '').strip(),
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': SCOPE,
        'state': state,
        'nonce': nonce,
        'access_type': 'online',
        'include_granted_scopes': 'true',
        # always show the account chooser: shared devices are common
        'prompt': 'select_account',
    }
    return f'{AUTH_ENDPOINT}?{urllib.parse.urlencode(params)}'


def _request(url, *, method='GET', headers=None, data=None):
    body = None
    if data is not None:
        body = data if isinstance(data, bytes) else urllib.parse.urlencode(data).encode('utf-8')
    req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            raw = resp.read().decode('utf-8') or '{}'
            return json.loads(raw)
    except urllib.error.HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode('utf-8') or '{}')
        except ValueError:
            payload = {}
        message = payload.get('error_description') or payload.get('error') or str(exc)
        raise GoogleError(message, exc.code, payload) from exc
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise GoogleError(str(exc)) from exc


def exchange_code(site, code, redirect_uri):
    """One-time code → tokens. The client secret never leaves the server."""
    return _request(
        TOKEN_ENDPOINT, method='POST',
        headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
        },
        data={
            'code': code,
            'client_id': (site.google_client_id or '').strip(),
            'client_secret': (site.google_client_secret or '').strip(),
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code',
        },
    )


def _b64_json(segment):
    padded = segment + '=' * (-len(segment) % 4)
    return json.loads(base64.urlsafe_b64decode(padded.encode('ascii')).decode('utf-8'))


def read_id_token(site, id_token, nonce=''):
    """Read the claims out of the ID token after checking they are ours."""
    parts = (id_token or '').split('.')
    if len(parts) != 3:
        raise GoogleError('Malformed ID token')
    try:
        claims = _b64_json(parts[1])
    except (ValueError, UnicodeDecodeError) as exc:
        raise GoogleError('Unreadable ID token') from exc

    if claims.get('iss') not in ISSUERS:
        raise GoogleError('Unexpected token issuer')

    audience = claims.get('aud')
    if audience != (site.google_client_id or '').strip():
        raise GoogleError('This token was issued for another app')

    try:
        expires = int(claims.get('exp') or 0)
    except (TypeError, ValueError):
        expires = 0
    if expires and time.time() > expires + CLOCK_SKEW:
        raise GoogleError('Expired token')

    if nonce and claims.get('nonce') != nonce:
        raise GoogleError('Nonce mismatch')

    return claims


def userinfo(access_token):
    """Fallback when the token response carries no ID token."""
    return _request(
        USERINFO_ENDPOINT,
        headers={'Authorization': f'Bearer {access_token}', 'Accept': 'application/json'},
    )


def fetch_profile(site, code, redirect_uri, nonce=''):
    """code → the handful of fields the store actually needs."""
    tokens = exchange_code(site, code, redirect_uri)
    id_token = tokens.get('id_token')
    if id_token:
        claims = read_id_token(site, id_token, nonce)
    elif tokens.get('access_token'):
        claims = userinfo(tokens['access_token'])
    else:
        raise GoogleError('Google returned no identity token')

    email = (claims.get('email') or '').strip().lower()
    if not email:
        raise GoogleError('This Google account has no email address')
    if claims.get('email_verified') in (False, 'false'):
        raise GoogleError('This Google email is not verified')

    return {
        'sub': str(claims.get('sub') or '')[:64],
        'email': email,
        'name': (claims.get('name') or '').strip(),
        'given_name': (claims.get('given_name') or '').strip(),
        'family_name': (claims.get('family_name') or '').strip(),
        'picture': (claims.get('picture') or '').strip()[:500],
    }
