"""Session-backed CSRF protection for state-changing requests.

Implemented with the standard library only (``secrets`` for the token,
``hmac.compare_digest`` for the comparison) so the web UI gains no new
dependency.

Threat model
------------
This app authenticates with server-side credentials loaded from ``.env``, *not*
with the session: every visitor who can reach the port is treated as the
operator. Flask's session cookie therefore does not gate anything, and its
``SameSite=Lax`` default — which is what blocks the classic cross-site form
POST today — is doing security work the application should own. One cookie
config change, one browser quirk or one ``fetch`` with permissive credentials
and the destructive ``POST /items/<key>/delete`` becomes reachable from any
page the operator visits. So the token is validated here, in the application,
rather than relying on browser defaults.
"""

import hmac
import secrets

from flask import render_template, request, session

#: Session key under which the per-session token is stored.
CSRF_SESSION_KEY = '_csrf_token'

#: Accepted carriers for the token on a state-changing request.
CSRF_FORM_FIELD = 'csrf_token'
CSRF_HEADER = 'X-CSRF-Token'

#: Methods that may not change state and so carry no token.
SAFE_METHODS = frozenset({'GET', 'HEAD', 'OPTIONS', 'TRACE'})

CSRF_ERROR_MESSAGE = (
    'CSRF validation failed: the request was missing a valid CSRF token. '
    'Reload the page and try again.'
)


def get_csrf_token():
    """Return this session's CSRF token, creating it on first use."""
    token = session.get(CSRF_SESSION_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        session[CSRF_SESSION_KEY] = token
    return token


def validate_csrf():
    """Reject state-changing requests without a matching token (400)."""
    if request.method in SAFE_METHODS:
        return None

    expected = session.get(CSRF_SESSION_KEY)
    supplied = request.form.get(CSRF_FORM_FIELD) or request.headers.get(CSRF_HEADER)

    if not expected or not supplied or not hmac.compare_digest(str(expected), str(supplied)):
        return render_template('error.html', code=400, message=CSRF_ERROR_MESSAGE), 400

    return None


def register_csrf(app):
    """Expose the token to templates and validate it on every request."""
    app.jinja_env.globals['csrf_token'] = get_csrf_token
    app.before_request(validate_csrf)
