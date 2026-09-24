"""Vercel serverless entrypoint for the Flask web app.

Vercel's Python runtime imports this module and calls the WSGI ``app``
object directly per-invocation; it does not run the Gunicorn command
used by the other deployment targets. Flask sessions (and so the CSRF
token) are signed cookies, not server-side state, so they survive fine
across the stateless, per-request cold starts this runtime uses.

This file lives under deploy/vercel/ rather than the repo root, so the
Vercel project's "Root Directory" setting must point at deploy/vercel,
with "Include files outside the Root Directory in the Build Step"
enabled so the build can still import the zotero_client package.
"""

from zotero_client.web import create_app

app = create_app()
