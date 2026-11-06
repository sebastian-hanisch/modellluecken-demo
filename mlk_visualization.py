"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import mlk_constants as C

FAM_COLORS = {0: "#4c78a8", 1: "#d8a13a", 2: "#7b5ea7"}


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_cloud(p, model_idx, real_idx):
    """Alle Zuordnungen (Kosten waagerecht, Überlast senkrecht): die wirklich zulässigen blau; das Modell-Optimum (Raute) und das wirkliche Optimum (Stern)."""
    cost, over = np.asarray(p.cost, dtype=float), np.asarray(p.over, dtype=float)
    ok = p.feasible(C.KEYS)
    fig = go.Figure(go.Scattergl(x=cost[~ok], y=over[~ok], mode="markers", marker=dict(size=3, color=C.COLOR_ALL), name="nicht zulässig", hovertemplate="Kosten %{x:.0f} / Überlast %{y:.0f}<extra></extra>"))
    if ok.any():
        fig.add_trace(go.Scattergl(x=cost[ok], y=over[ok], mode="markers", marker=dict(size=5, color=C.COLOR_REAL), name="wirklich zulässig", hovertemplate="Kosten %{x:.0f} / Überlast %{y:.0f}<extra></extra>"))
    if model_idx is not None:
        fig.add_trace(go.Scatter(x=[cost[model_idx]], y=[over[model_idx]], mode="markers", marker=dict(symbol="diamond", size=14, color=C.COLOR_MARK, line=dict(width=1.5, color="white")), name="Modell-Optimum",
                                 hovertemplate="Modell-Optimum: Kosten %{x:.0f} / Überlast %{y:.0f}<extra></extra>"))
    if real_idx is not None:
        fig.add_trace(go.Scatter(x=[cost[real_idx]], y=[over[real_idx]], mode="markers", marker=dict(symbol="star", size=16, color=C.COLOR_OK, line=dict(width=1.5, color="white")), name="wirkliches Optimum",
                                 hovertemplate="wirkliches Optimum: Kosten %{x:.0f} / Überlast %{y:.0f}<extra></extra>"))
    fig.update_xaxes(title_text="Kosten der Zuordnung")
    fig.update_yaxes(title_text="Überlast in Stunden (Kapazität)")
    return _base(fig, height=400)


def build_omit_bars(rows: list[dict]):
    """Scheinersparnis je einzeln ausgelassener Nebenbedingung; rot: die Nebenbedingung wird verletzt."""
    labels = [C.KEY_NAMES[r["omit"]] for r in rows]
    vals = [(r["saving"] or 0.0) * 100 for r in rows]
    fig = go.Figure(go.Bar(x=labels, y=vals, marker_color=[C.COLOR_BAD if r["violated"] else C.COLOR_OK for r in rows], text=[f"{v:.1f} %".replace(".", ",") for v in vals], textposition="outside",
                           hovertemplate="ohne %{x}: %{y:.1f} % Scheinersparnis<extra></extra>"))
    fig.update_yaxes(title_text="Scheinersparnis in % der wirklichen Kosten", range=[0, max(10.0, max(vals) * 1.25)])
    fig.update_xaxes(type="category", title_text="Fehlende Nebenbedingung (alle anderen im Modell)")
    return _base(fig, height=320)


def build_cap_line(rows: list[dict]):
    """Scheinersparnis und Überlast über den Kapazitätsfaktor (Modell ohne Kapazität)."""
    rows = [r for r in rows if r["over"] is not None]
    xs = [f"{r['cap_pct']} % ({r['cap']} h)" for r in rows]
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12, subplot_titles=("Scheinersparnis in % der wirklichen Kosten", "Überlast des Modell-Optimums in Stunden"))
    fig.add_trace(go.Scatter(x=xs, y=[(r["saving"] or 0.0) * 100 for r in rows], mode="lines+markers", line=dict(color=C.COLOR_MARK), name="Scheinersparnis", hovertemplate="%{x}: %{y:.1f} %<extra></extra>"), row=1, col=1)
    fig.add_trace(go.Bar(x=xs, y=[r["over"] for r in rows], marker_color=C.COLOR_BAD, name="Überlast", hovertemplate="%{x}: %{y} h<extra></extra>"), row=2, col=1)
    fig.update_layout(showlegend=False)
    fig.update_xaxes(type="category", title_text="Kapazitätsfaktor f (Kapazität in Stunden)", row=2, col=1)
    return _base(fig, height=380)


def build_repair(rounds: list[dict]):
    """Kosten des Optimums je Runde Prüfen und Nachbessern; die Beschriftung nennt die aufgenommenen Nebenbedingungen."""
    rounds = [r for r in rounds if r["cost"] is not None]
    xs = [f"Runde {i}" for i in range(len(rounds))]
    text = ["ohne Nebenbedingung" if not r["keys"] else "+ " + ", ".join(C.KEY_NAMES[k] for k in r["keys"][-len(r["keys"]):]) for r in rounds]
    fig = go.Figure(go.Scatter(x=xs, y=[r["cost"] for r in rounds], mode="lines+markers+text", text=[str(r["cost"]) for r in rounds], textposition="top center", line=dict(color=C.COLOR_REAL),
                               marker=dict(size=10, color=[C.COLOR_OK if r["feasible"] else C.COLOR_BAD for r in rounds]), hovertemplate="%{x}: Kosten %{y}<extra></extra>"))
    fig.update_xaxes(type="category", title_text="Runde (die Modell-Optima werden teurer, bis sie wirklich zulässig sind)")
    fig.update_yaxes(title_text="Kosten des Optimums", rangemode="tozero")
    return _base(fig, height=300)


def build_pressure(pr: dict):
    """Best-of-k im Modell: oben die erwarteten Kosten, unten die Wahrscheinlichkeit einer wirklich zulässigen Wahl."""
    xs = ["∞" if k is None else str(k) for k in pr["ks"]]
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12, subplot_titles=("Erwartete Kosten der Wahl", "Wahrscheinlichkeit einer wirklich zulässigen Wahl in %"))
    fig.add_trace(go.Scatter(x=xs, y=pr["cost"], mode="lines+markers", line=dict(color=C.COLOR_MARK), hovertemplate="k = %{x}: %{y:.1f}<extra></extra>"), row=1, col=1)
    fig.add_trace(go.Scatter(x=xs, y=[v * 100 for v in pr["p_real"]], mode="lines+markers", line=dict(color=C.COLOR_OK), hovertemplate="k = %{x}: %{y:.2f} %<extra></extra>"), row=2, col=1)
    fig.update_layout(showlegend=False)
    fig.update_xaxes(type="category", title_text="Optimierungsstärke k (unter k gezogenen Zuordnungen die billigste wählen; ∞: das Optimum)", row=2, col=1)
    return _base(fig, height=380)


def build_saving_bars(res: dict):
    """Scheinersparnis (Median) je Familie und einzeln ausgelassener Nebenbedingung."""
    keys = C.KEYS
    fams = list(res)
    fig = go.Figure([go.Bar(x=[C.KEY_NAMES[k] for k in keys], y=[res[f][k]["saving"][1] * 100 for k in keys], name=C.FAMILIES[f], marker_color=FAM_COLORS[f],
                            hovertemplate=C.FAMILIES[f] + ": %{y:.1f} %<extra></extra>") for f in fams])
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Scheinersparnis in % (Median über 20 Instanzen)")
    fig.update_xaxes(type="category", title_text="Fehlende Nebenbedingung (alle anderen im Modell)")
    return _base(fig, height=340)
