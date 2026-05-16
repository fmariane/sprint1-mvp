from __future__ import annotations

import mimetypes

# Render's proxy can strip or misidentify MIME types for static assets.
# Register them explicitly before Dash/Flask initialise.
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("application/json", ".json")

import dash
import dash_bootstrap_components as dbc

from dashboard import callbacks, data_loader, layout

DATA = data_loader.load_all()

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="Segurança Operacional — Aeroportos do Brasil",
)
server = app.server


@server.after_request
def fix_content_type(response):
    """Ensure JS and CSS files are served with correct MIME types on Render."""
    path = getattr(response, "direct_passthrough", False)
    content_type = response.content_type or ""
    if "text/plain" in content_type:
        from flask import request as flask_request
        url = flask_request.path
        if url.endswith(".js"):
            response.headers["Content-Type"] = "application/javascript"
        elif url.endswith(".css"):
            response.headers["Content-Type"] = "text/css"
        elif url.endswith(".json"):
            response.headers["Content-Type"] = "application/json"
    return response


app.layout = layout.build(DATA)
callbacks.register(app, DATA)

if __name__ == "__main__":
    app.run(debug=True)
