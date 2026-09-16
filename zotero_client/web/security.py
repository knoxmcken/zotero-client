"""Shared request guards for the web UI.

These run at application level so that *every* endpoint is covered by default,
including endpoints added by a future blueprint. Per-blueprint copies of the
same guard used to live in each route module, which meant a fourth blueprint
could silently skip the credential check.
"""

from flask import current_app, render_template, request

CREDENTIALS_MISSING_MESSAGE = (
    'Zotero credentials are not configured. '
    'Set ZOTERO_API_KEY and ZOTERO_USER_ID in your .env file.'
)

#: Endpoints allowed to answer without Zotero credentials.
#:
#: This allowlist is deliberately tiny and explicit: everything not named here
#: is credential-gated, so adding a blueprint or a route cannot bypass the
#: check by omission. ``static`` serves CSS/JS/images, ``None`` means the URL
#: matched no rule at all (let Flask render its own 404).
PUBLIC_ENDPOINTS = frozenset({'static'})


def check_credentials():
    """Refuse non-public endpoints while Zotero credentials are missing."""
    if request.endpoint is None or request.endpoint in PUBLIC_ENDPOINTS:
        return None

    if not current_app.config.get('CREDENTIALS_MISSING'):
        return None

    return render_template(
        'error.html',
        code=503,
        message=CREDENTIALS_MISSING_MESSAGE,
    ), 503


def register_shared_guards(app):
    """Install the application-wide request guards, in order."""
    # Order matters: the credential check must run before CSRF validation so a
    # credential-less deployment reports the actionable 503, not a CSRF 400.
    app.before_request(check_credentials)
