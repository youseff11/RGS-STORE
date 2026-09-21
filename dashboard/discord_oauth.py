"""Minimal «Sign in with Discord» client (OAuth 2.0 authorization-code grant).

Standard library only — same approach as `google_oauth.py` and `paypal.py`:

    1. the customer clicks the button  → we send them to `auth_url()`
    2. Discord sends them back with a one-time `code`
    3. `fetch_profile()` swaps that code for an access token and reads
       `/users/@me` (id, name, avatar, email + whether it is verified)

Discord sits behind Cloudflare and blocks requests without a proper
User-Agent, so every call sends one (`DiscordBot (url, version)` — the format
Discord's docs ask for).
"""

import json
import secrets
import urllib.error
import urllib.parse
import urllib.request

from django.urls import reverse

AUTH_ENDPOINT = 'https://discord.com/oauth2/authorize'
TOKEN_ENDPOINT = 'https://discord.com/api/oauth2/token'
ME_ENDPOINT = 'https://discord.com/api/v10/users/@me'
CDN = 'https://cdn.discordapp.com'
SCOPE = 'identify email'
TIMEOUT = 20
VERSION = '1.0'


class DiscordError(Exception):
    """Anything that stops us from trusting what came back from Discord."""

    def __init__(self, message, status=None, payload=None):
        super().__init__(message)
        self.status = status
        self.payload = payload or {}


def random_token():
    """A fresh value for the `state` we hand to Discord."""
    return secrets.token_urlsafe(24)


def redirect_uri(request, site):
    """Where Discord sends the customer back — it must match one of the
    Redirects saved in the Developer Portal exactly.

    Same rule as Google: the saved store URL wins when the visitor is on that
    host (so a site behind a proxy still gets `https://…`); anywhere else
    (localhost) it's built from the request.
    """
    path = reverse('discord_callback')
    base = ((site.site_url if site else '') or '').strip().rstrip('/')
    if base:
        host = urllib.parse.urlparse(base).netloc.lower()
        if host and host == request.get_host().lower():
            return base + path
    return request.build_absolute_uri(path)


def auth_url(site, redirect_uri, state):
    """Where to send the customer to approve the store on Discord."""
    params = {
        'client_id': (site.discord_client_id or '').strip(),
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': SCOPE,
        'state': state,
    }
    return f'{AUTH_ENDPOINT}?{urllib.parse.urlencode(params)}'


def _user_agent(site):
    url = ((site.site_url if site else '') or '').strip() or 'https://rgs-tower.local'
    return f'DiscordBot ({url}, {VERSION})'


def _request(site, url, *, method='GET', headers=None, data=None):
    body = urllib.parse.urlencode(data).encode('utf-8') if data is not None else None
    all_headers = {'Accept': 'application/json', 'User-Agent': _user_agent(site)}
    all_headers.update(headers or {})
    req = urllib.request.Request(url, data=body, method=method, headers=all_headers)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode('utf-8') or '{}')
    except urllib.error.HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode('utf-8') or '{}')
        except ValueError:
            payload = {}
        message = payload.get('error_description') or payload.get('error') or payload.get('message') or str(exc)
        raise DiscordError(message, exc.code, payload) from exc
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise DiscordError(str(exc)) from exc


def exchange_code(site, code, redirect_uri):
    """One-time code → access token. The client secret never leaves the server.
    (Discord's token URL only accepts form data, never JSON.)"""
    return _request(
        site, TOKEN_ENDPOINT, method='POST',
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        data={
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
            'client_id': (site.discord_client_id or '').strip(),
            'client_secret': (site.discord_client_secret or '').strip(),
        },
    )


def current_user(site, access_token):
    return _request(site, ME_ENDPOINT, headers={'Authorization': f'Bearer {access_token}'})


def avatar_url(user):
    """CDN link of the Discord avatar ('' when the account uses the default one)."""
    avatar = user.get('avatar') or ''
    if not avatar or not user.get('id'):
        return ''
    return f"{CDN}/avatars/{user['id']}/{avatar}.png?size=128"


def fetch_profile(site, code, redirect_uri):
    """code → the handful of fields the store actually needs."""
    tokens = exchange_code(site, code, redirect_uri)
    access_token = tokens.get('access_token')
    if not access_token:
        raise DiscordError('Discord returned no access token')
    user = current_user(site, access_token)
    uid = str(user.get('id') or '')
    if not uid:
        raise DiscordError('Discord returned no user id')
    name = (user.get('global_name') or user.get('username') or '').strip()
    return {
        'sub': uid[:32],
        'email': (user.get('email') or '').strip().lower(),
        # an unverified email could belong to anyone — never trust it for linking
        'verified': user.get('verified') is True,
        'name': name,
        'given_name': name.partition(' ')[0],
        'family_name': name.partition(' ')[2],
        'username': (user.get('username') or '').strip(),
        'picture': avatar_url(user)[:500],
    }
