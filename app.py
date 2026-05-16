from __future__ import annotations

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

app.layout = layout.build(DATA)
callbacks.register(app, DATA)

if __name__ == "__main__":
    app.run(debug=True)
