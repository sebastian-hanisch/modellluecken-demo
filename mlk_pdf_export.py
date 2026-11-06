"""PDF-Export des aktuellen Ergebnisses (fpdf2). Kernschriften sind latin-1: Umlaute gehen, Sonderzeichen werden ersetzt."""

from __future__ import annotations

from fpdf import FPDF

import mlk_constants as C
from mlk_evaluation import Analysis, compare, model_text, pct

_REPLACE = {"→": "->", "–": "-", "—": "-", "−": "-", "≤": "<=", "≥": ">=", "·": "*", "×": "x", "„": '"', "“": '"', "²": "2", "∞": "unendlich"}


def _s(text) -> str:
    out = str(text).replace("**", "").replace("`", "")
    for old, new in _REPLACE.items():
        out = out.replace(old, new)
    return out.encode("latin-1", "replace").decode("latin-1")


def build_pdf(a: Analysis) -> bytes:
    s = a.settings
    c = compare(a)
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _s("Modelllücken"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, _s(f"{s.n} Personen, {s.m} Aufgaben, Familie: {C.FAMILIES[s.family]}, Seed {s.seed}, Kapazität {a.p.inst.cap} Stunden. Alles simuliert."), new_x="LMARGIN", new_y="NEXT")
    pdf.multi_cell(0, 5, _s(f"Das Modell {model_text(s.keys)}; die Wirklichkeit hat alle vier Nebenbedingungen (Kapazität, Mindestbesetzung, Qualifikation, Konflikt)."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    if c["model"] is None or c["real"] is None:
        pdf.multi_cell(0, 5, _s("Das Modell oder die Wirklichkeit hat keine zulässige Zuordnung."), new_x="LMARGIN", new_y="NEXT")
        return bytes(pdf.output())
    pdf.multi_cell(0, 5, _s(f"Modell-Optimum: Kosten {c['model']['cost']}; wirkliches Optimum: Kosten {c['real']['cost']}; Scheinersparnis {pct(c['saving'])}. "
                            f"Wirklich zulässig: {c['n_real']} von {c['n_plans']} Zuordnungen ({pct(c['share_real'], 2)})."), new_x="LMARGIN", new_y="NEXT")
    v = c["model"]["violated"]
    pdf.multi_cell(0, 5, _s(f"Verletzungen des Modell-Optimums: Überlast {v['K']} h, Personen ohne Aufgabe {v['B']}, verbotene Paare {v['Q']}, Konflikte {v['W']}."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, _s("Bei Gleichstand gilt der kleinste Index der Aufzählung. Quelle: modellluecken-demo, Sebastian Hanisch."), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
