"""Modelllücken - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 9 der Reihe „Zielfunktionsdesign“: Aufgaben werden auf Personen verteilt. Die Wirklichkeit hat vier Nebenbedingungen (Kapazität, Mindestbesetzung, Qualifikation, Konflikt),
das Modell kennt nur einige. Die Demo zeigt, was der Optimierer ausnutzt, was nicht modelliert ist: wie billig seine Lösung aussieht (Scheinersparnis), was sie verletzt,
welche Lücke am meisten zählt, wie viele Runden Prüfen und Nachbessern nötig sind und was ein einfacher Auffälligkeitstest taugt.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import mlk_constants as C
from mlk_evaluation import (
    Settings,
    analyse,
    cap_rows,
    compare,
    de,
    flag_check,
    model_text,
    names,
    omit_rows,
    pct,
    pressure,
    repair_rows,
    summary_caps,
    summary_flag,
    summary_none,
    summary_omit,
    summary_pressure,
    summary_repair,
    sweep_all,
    verdict_cap,
    verdict_cap_sweep,
    verdict_compare,
    verdict_flag,
    verdict_flag_sweep,
    verdict_none_sweep,
    verdict_omit,
    verdict_omit_sweep,
    verdict_pressure,
    verdict_pressure_sweep,
    verdict_repair,
    verdict_repair_sweep,
)
from mlk_pdf_export import build_pdf
from mlk_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from mlk_layout import dunkles_design, kopf_css
from mlk_visualization import build_cap_line, build_cloud, build_omit_bars, build_pressure, build_repair, build_saving_bars

st.set_page_config(page_title="Modelllücken – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner="20 feste Instanzen werden gerechnet (je 65 536 Zuordnungen, drei Familien) ...")
def _sweep():
    return sweep_all()


def assignment_text(plan, n: int) -> str:
    """Person -> Aufgaben: „P1: A2, A5 | P2: –“."""
    parts = []
    for i in range(n):
        tasks = [f"A{j + 1}" for j, person in enumerate(plan) if int(person) == i]
        parts.append(f"P{i + 1}: " + (", ".join(tasks) if tasks else "–"))
    return " | ".join(parts)


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in mlk_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🧩 Modelllücken")
st.markdown(
    """
**Was nutzt der Optimierer aus, das niemand modelliert hat?** **m Aufgaben** werden auf **n Personen** verteilt, jede Aufgabe an genau eine Person; Kosten und Zeit hängen an Person und Aufgabe.
Die **Wirklichkeit** hat vier Nebenbedingungen: **Kapazität** (die Zeit einer Person ist begrenzt), **Mindestbesetzung** (jede Person bekommt eine Aufgabe), **Qualifikation** (verbotene Paare)
und **Konflikt** (zwei Aufgaben nicht bei derselben Person). Das **Modell** kennt nur die Nebenbedingungen, die Sie links einschalten. Was fehlt, ist für den Optimierer frei, und billig ist oft gerade das, was die Wirklichkeit verbietet.

Weiter unten: **🔬 Das Modell**, **🔬 Welche Lücke zählt**, **🔬 Wie eng**, **🔬 Prüfen und Nachbessern**, **🔬 Auffälligkeitstest und Druck**, **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert der Vergleich", expanded=True):
    st.markdown(
        """
1. **Alle Zuordnungen** (n^m, bis 390 625) werden aufgezählt; das **Modell-Optimum** ist die billigste Zuordnung, die die eingeschalteten Nebenbedingungen erfüllt (bei Gleichstand der kleinste Index der Aufzählung), das **wirkliche Optimum** die billigste, die alle vier erfüllt.
2. **Scheinersparnis:** wie viel billiger das Modell-Optimum aussieht als das wirkliche, in Prozent der wirklichen Kosten. Sie ist der Gewinn, den der Optimierer aus der Lücke zieht und den es in der Wirklichkeit nicht gibt.
3. **Prüfen und Nachbessern:** das Modell lösen, gegen die Wirklichkeit prüfen, verletzte Nebenbedingungen aufnehmen, bis das Optimum wirklich zulässig ist.
4. **Messungen, kein Satz:** Alle Zahlen sind Zählungen und Spannen über feste Instanzen dieses Zufallsmodells; sie sagen nichts über echte Dienstpläne.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Instanz**")
    n = st.slider("Personen n", *bounds("n_slider"), key="n_slider", help="Alle n^m Zuordnungen werden aufgezählt.")
    m = st.slider("Aufgaben m", *bounds("m_slider"), key="m_slider", help="Bei 5 Personen und 8 Aufgaben sind es 390 625 Zuordnungen; die Rechnung dauert dann einige Sekunden.")
    family = st.selectbox("Kosten", list(range(len(C.FAMILIES))), key="family_select", format_func=lambda i: C.FAMILIES[i],
                          help="Beim starken Personeneffekt ist eine Person für fast alle Aufgaben die billigste.")
    seed = st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)
    st.markdown("**Kapazität der Wirklichkeit**")
    cap = st.slider("Kapazitätsfaktor f in %", *bounds("cap_slider"), key="cap_slider", step=C.CAP_STEP,
                    help="Die Kapazität je Person ist aufgerundet f mal die Summe der mittleren Zeiten je Aufgabe, geteilt durch n. Je kleiner f, desto enger.")
    st.markdown("**Das Modell kennt …**")
    k_in = st.toggle("Kapazität", key="k_in_toggle", help=C.KEY_HELP["K"])
    b_in = st.toggle("Mindestbesetzung", key="b_in_toggle", help=C.KEY_HELP["B"])
    q_in = st.toggle("Qualifikation", key="q_in_toggle", help=C.KEY_HELP["Q"])
    w_in = st.toggle("Konflikt", key="w_in_toggle", help=C.KEY_HELP["W"])

sync_query_params({"n_slider": int(n), "m_slider": int(m), "family_select": int(family), "seed_input": int(seed), "cap_slider": int(cap),
                   "k_in_toggle": int(k_in), "b_in_toggle": int(b_in), "q_in_toggle": int(q_in), "w_in_toggle": int(w_in)})

settings = Settings(int(n), int(m), int(family), int(seed), int(cap), bool(k_in), bool(b_in), bool(q_in), bool(w_in))
a = _analysis(settings)
c = compare(a)

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis: was wählt das Modell, und wie billig sieht es aus?")
m1, m2, m3 = st.columns(3)
m1.metric("Kosten des Modell-Optimums", "–" if c["model"] is None else str(c["model"]["cost"]), delta=model_text(settings.keys), delta_color="off")
m2.metric("Kosten des wirklichen Optimums", "unlösbar" if c["real"] is None else str(c["real"]["cost"]), delta=f"Kapazität {a.p.inst.cap} Stunden", delta_color="off")
m3.metric("Scheinersparnis", "–" if c["saving"] is None else pct(c["saving"]), delta=f"{pct(c['share_real'], 2)} wirklich zulässig", delta_color="off")
st.plotly_chart(build_cloud(a.p, None if a.model is None else a.model[0], None if a.real is None else a.real[0]), width="stretch", key="cloud_chart")
st.caption("Jeder Punkt ist eine Zuordnung: Kosten waagerecht, Überlast senkrecht. Blau: die wirklich zulässigen (Überlast null und alle anderen Nebenbedingungen erfüllt); die Raute ist das Modell-Optimum, der Stern das wirkliche. Das Modell-Optimum liegt links von allem Wirklichen: dort ist es billiger.")
st.download_button("📄 Ergebnis als PDF", data=build_pdf(a), file_name="modellluecken.pdf", mime="application/pdf", key="pdf_download")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Ist die billigste Lösung des Modells auch eine Lösung der Wirklichkeit?")
kind, text = verdict_compare(c)
getattr(st, kind)(text)

st.markdown("---")

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Das Modell")
st.caption("Modell-Optimum und wirkliches Optimum nebeneinander: wer macht was, und was wird verletzt?")
if c["model"] is not None and c["real"] is not None:
    v = c["model"]["violated"]
    rows_md = ["| | Kosten | Zuordnung | Überlast | ohne Aufgabe | verbotene Paare | Konflikte |", "|---|---|---|---|---|---|---|"]
    rows_md.append(f"| **Modell-Optimum** ({model_text(settings.keys)}) | {c['model']['cost']} | {assignment_text(c['model']['plan'], a.p.inst.n)} | {v['K']} h | {v['B']} | {v['Q']} | {v['W']} |")
    rows_md.append(f"| **Wirkliches Optimum** | {c['real']['cost']} | {assignment_text(c['real']['plan'], a.p.inst.n)} | 0 h | 0 | 0 | 0 |")
    st.markdown("\n".join(rows_md))
    st.caption(f"Das Modell-Optimum ist {'eindeutig' if c['model']['n_opt'] == 1 else f'eines von {c['model']['n_opt']} gleich guten Plänen'}; "
               f"{'er' if c['model']['n_opt'] == 1 else 'der erste der Aufzählung'} ist {'wirklich zulässig' if c['model']['first_ok'] else 'nicht wirklich zulässig'}.")
else:
    st.info("Das Modell oder die Wirklichkeit hat keine zulässige Zuordnung; ein Vergleich ist nicht möglich.")
if st.toggle("Modell ohne jede Nebenbedingung über feste Instanzen nachrechnen", value=False, key="sweep_none"):
    sw = _sweep()
    st.info("; ".join(verdict_none_sweep(summary_none(recs), C.FAMILIES[fam]) for fam, recs in sw.items()) + ".")

st.markdown("---")

st.subheader("🔬 Welche Lücke zählt")
st.caption("Je Nebenbedingung als einzige ausgelassen (alle anderen im Modell) auf dieser Instanz: wird sie verletzt, wie stark, und wie viel billiger sieht die Lösung aus?")
if a.real is not None:
    orows = omit_rows(a)
    st.plotly_chart(build_omit_bars(orows), width="stretch", key="omit_chart")
    kind, text = verdict_omit(orows)
    getattr(st, kind)(text)
else:
    st.info("Ohne wirkliches Optimum gibt es keine Scheinersparnis.")
if st.toggle("Je ausgelassene Nebenbedingung über feste Instanzen nachrechnen", value=False, key="sweep_omit"):
    sw = _sweep()
    res = {fam: summary_omit(recs) for fam, recs in sw.items()}
    kind, text = verdict_omit_sweep(res)
    getattr(st, kind)(text)
    st.plotly_chart(build_saving_bars(res), width="stretch", key="sweep_omit_chart")

st.markdown("---")

st.subheader("🔬 Wie eng")
st.caption("Fehlt nur die Kapazität: je enger sie ist, desto größer die Lücke. Alle vier Kapazitätsfaktoren auf dieser Instanz (die anderen drei Nebenbedingungen im Modell).")
crows = cap_rows(a)
st.plotly_chart(build_cap_line(crows), width="stretch", key="cap_chart")
kind, text = verdict_cap(crows)
getattr(st, kind)(text)
if st.toggle("Kapazitätsfaktor über feste Instanzen nachrechnen", value=False, key="sweep_cap"):
    sw = _sweep()
    kind, text = verdict_cap_sweep(summary_caps(sw[0]))
    getattr(st, kind)(text)

st.markdown("---")

st.subheader("🔬 Prüfen und Nachbessern")
st.caption("Das Modell lösen, gegen die Wirklichkeit prüfen, verletzte Nebenbedingungen aufnehmen: wie viele Runden, bis das Optimum wirklich zulässig ist? Der Start ist immer das Modell ohne Nebenbedingung, unabhängig von den Schaltern links.")
mode = st.radio("Aufnahme", ["all", "one"], format_func=lambda x: "alle verletzten auf einmal" if x == "all" else "eine je Runde (Reihenfolge Kapazität, Mindestbesetzung, Qualifikation, Konflikt)", horizontal=True, key="repair_mode")
rounds = repair_rows(a, mode)
st.plotly_chart(build_repair(rounds), width="stretch", key="repair_chart")
rows_md = ["| Runde | Modell kennt | Kosten des Optimums | Verletzt | Kommt dazu |", "|---|---|---|---|---|"]
for i, r in enumerate(rounds):
    viol_txt = "–" if r["idx"] is None else (", ".join(f"{C.KEY_NAMES[k]} {x}" for k, x in r["violated"].items() if x > 0) or "nichts: wirklich zulässig")
    rows_md.append(f"| {i} | {names(r['keys'])} | {'unlösbar' if r['cost'] is None else r['cost']} | {viol_txt} | {names(r['add']) if r['add'] else '–'} |")
st.markdown("\n".join(rows_md))
kind, text = verdict_repair(rounds)
getattr(st, kind)(text)
if st.toggle("Prüfen und Nachbessern über feste Instanzen nachrechnen", value=False, key="sweep_repair"):
    sw = _sweep()
    kind, text = verdict_repair_sweep({fam: summary_repair(recs) for fam, recs in sw.items()})
    getattr(st, kind)(text)

st.markdown("---")

st.subheader("🔬 Auffälligkeitstest und Druck")
st.caption(f"Ein einfacher Test an der Lösung: trägt die am stärksten belastete Person mindestens das {de(C.FLAG_RATIO)}-fache der mittleren Last? Und was geschieht, wenn man das Modell stärker optimiert (Best-of-k wie in Stück 8)?")
kind, text = verdict_flag(flag_check(a))
getattr(st, kind)(text)
pr = pressure(a)
if pr["cost"]:
    st.plotly_chart(build_pressure(pr), width="stretch", key="pressure_chart")
    kind, text = verdict_pressure(pr)
    getattr(st, kind)(text)
if st.toggle("Auffälligkeitstest über feste Instanzen nachrechnen", value=False, key="sweep_flag"):
    sw = _sweep()
    kind, text = verdict_flag_sweep({fam: summary_flag(recs) for fam, recs in sw.items()})
    getattr(st, kind)(text)
if st.toggle("Druck über feste Instanzen nachrechnen (Modell ohne Nebenbedingung)", value=False, key="sweep_pressure"):
    sw = _sweep()
    kind, text = verdict_pressure_sweep(summary_pressure(sw[0]))
    getattr(st, kind)(text)

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Vier Nebenbedingungen, ein Zufallsmodell** | Qualifikation (20 % verboten), Konflikt (drei Paare) und Kapazität (1,25-fach) sind gewählte Größen; echte Pläne haben andere und mehr Nebenbedingungen | Fehlerkatalog „Relaxierung erlaubt Unsinn“ (FK-011) |
| **Alle Zuordnungen aufgezählt** | Bis n^m = 390 625; bei größeren Problemen braucht es einen Löser, das Verhalten der Lücken ändert sich nicht, die Aufzählung ist nur der Beweis | Dokumentation des Lösers |
| **Gleichstand: kleinster Index** | Das Modell-Optimum ist hier fast immer eindeutig (Median ein Plan); bei Gleichstand wählt die Regel, nicht das Ziel | Stück 5 (Gleichstände) |
| **Prüfen heißt: alle vier Nebenbedingungen sind bekannt** | Das Nachbessern kennt die Wirklichkeit; eine unbekannte Nebenbedingung findet es nicht | Stück 13 (Ziel testen) |
| **Der Auffälligkeitstest ist eine Regel mit einer Schwelle** | Er schlägt auch beim wirklichen Optimum an und übersieht Verletzungen, die nichts mit der Last zu tun haben (Qualifikation, Konflikt) | Stück 13 (Ziel testen) |
| **Mehr Druck heißt: Best-of-k über die modellzulässigen Zuordnungen** | Ein Löser mit Toleranz oder ein Verfahren mit Strafterm (Stück 6) verhalten sich anders | Stück 6 (Hart gegen weich), Stück 8 (Goodhart-Kurve) |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Problem.** $m$ Aufgaben auf $n$ Personen; eine Zuordnung ist $x \in \{1, \dots, n\}^m$ ($x_j$ ist die Person der Aufgabe $j$). Kosten $\sum_j a_{x_j j}$, Zeit $b_{ij}$, Last der Person $i$: $L_i(x) = \sum_{j: x_j = i} b_{ij}$.

**Nebenbedingungen der Wirklichkeit.** **K** $L_i(x) \le \mathrm{cap}$ für alle $i$ (Überlast $\sum_i \max(0, L_i - \mathrm{cap})$); **B** jede Person hat mindestens eine Aufgabe; **Q** $F_{x_j j} = 0$ für alle $j$ (verbotene Paare $F$); **W** $x_{j} \ne x_{j'}$ für die Konfliktpaare $(j, j')$. Die Kapazität ist $\mathrm{cap} = \lceil f \cdot \sum_j \bar b_j / n \rceil$ mit der mittleren Zeit $\bar b_j$ der Aufgabe $j$.

**Modell.** $\mathcal{M} \subseteq \{K, B, Q, W\}$: das Modell kennt nur diese Nebenbedingungen. Modell-Optimum $x^{\mathcal{M}} \in \arg\min \{c(x) : x \text{ erfüllt } \mathcal{M}\}$ (bei Gleichstand der kleinste Index), wirkliches Optimum $x^\star$ mit $\mathcal{M} = \{K, B, Q, W\}$. Da $\{x \text{ erfüllt alle}\} \subseteq \{x \text{ erfüllt } \mathcal{M}\}$, gilt $c(x^{\mathcal{M}}) \le c(x^\star)$.

**Scheinersparnis.** $(c(x^\star) - c(x^{\mathcal{M}})) / c(x^\star) \ge 0$; sie ist null, wenn $x^{\mathcal{M}}$ wirklich zulässig ist.

**Prüfen und Nachbessern.** Start $\mathcal{M}_0 = \emptyset$; in Runde $t$ wird $x^{\mathcal{M}_t}$ gelöst und, wenn es eine Nebenbedingung verletzt, die verletzten (alle auf einmal) oder die erste verletzte in der Reihenfolge $K, B, Q, W$ in $\mathcal{M}_{t+1}$ aufgenommen. Das endet nach höchstens vier Runden mit dem wirklichen Optimum: ist $x^{\mathcal{M}_t}$ wirklich zulässig, ist es optimal, denn $\mathcal{M}_t$ ist eine Relaxierung.

**Druck.** Best-of-$k$ unter den modellzulässigen Zuordnungen: der Plan auf Rang $r$ (nach Kosten) wird mit Wahrscheinlichkeit $((N - r + 1)/N)^k - ((N - r)/N)^k$ gewählt (Formel aus Stück 8); $k = \infty$ ist das Modell-Optimum.

**Literatur.** Amodei u. a., „Concrete Problems in AI Safety“ (arXiv 1606.06565, Abstract gelesen): Unfälle aus einem falschen Ziel, darunter „avoiding side effects“ und „avoiding reward hacking“. Krakovna u. a., „Specification gaming: the flip side of AI ingenuity“ (Google DeepMind, 2020, gelesen): „Specification gaming is a behaviour that satisfies the literal specification of an objective without achieving the intended outcome.“ Diese Demo übernimmt keine Zahl daraus; alle Zahlen sind Messungen an dem Zufallsmodell der Demo.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
