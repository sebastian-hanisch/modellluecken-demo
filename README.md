# Modelllücken – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-modellluecken-demo.streamlit.app/)** -->

Stück 9 der Linie **Zielfunktionsdesign** („Das Ziel ist das Modell“) in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“ (Arbeitsname; Name, Bereich und Themenfeld werden erst bei der Einbindung in die Website festgelegt). Es baut auf Stück 1 bis 8 auf (`zielvergleich-demo`, `preis-der-fairness-demo`, `zwei-kriterien-demo`, `lexikographisch-demo`, `gleichstand-demo`, `hart-gegen-weich-demo`, `goodhart-kurve-demo`; Stück 7 ist zurückgestellt): **m Aufgaben werden auf n Personen verteilt**. Die **Wirklichkeit** hat vier Nebenbedingungen, das **Modell** kennt nur eine Auswahl davon. Was fehlt, ist für den Optimierer frei, und billig ist oft gerade das, was die Wirklichkeit verbietet. Die Demo misst, **wie oft, wie stark und mit welchem Scheingewinn** das passiert. Alles ist **simuliert**; keine Aussage über echte Dienstpläne, Personen oder Betriebe.

## Warum dieses Problem

Eine fehlende Nebenbedingung wird nicht „ein bisschen“ verletzt, sondern fast immer, und der Optimierer wird dafür belohnt: sein Modell-Optimum ist deutlich billiger als alles Wirkliche. Welche Lücke am meisten zählt, ist nicht die, die man vermutet. Die Fragen: Wie viel billiger sieht die Lösung des Modells aus (Scheinersparnis)? Was verletzt sie? Welche fehlende Nebenbedingung zählt am meisten, und wie eng muss die Kapazität sein, damit sie zählt? Wie viele Runden „Prüfen und Nachbessern“ braucht man? Und taugt ein einfacher Auffälligkeitstest?

## Modell

Gegeben `n` Personen, `m` Aufgaben, Kosten `a[i][j]` (ganze Zahlen) und Zeit `b[i][j]` (1 bis 9). Eine Zuordnung `x` gibt jeder Aufgabe `j` eine Person `x_j`; **alle `n^m` Zuordnungen werden aufgezählt** (bis `5^8 = 390 625`), alles exakt in ganzen Zahlen. **Wirklichkeit:** **K** Kapazität (die Zeitsumme jeder Person ist höchstens `cap = ⌈f · Σ_j mittlere Zeit / n⌉`, Voreinstellung `f = 1,25`), **B** Mindestbesetzung (jede Person bekommt mindestens eine Aufgabe), **Q** Qualifikation (verbotene Paare (Person, Aufgabe), je Paar mit Wahrscheinlichkeit 0,2; jede Aufgabe hat mindestens eine erlaubte Person), **W** Konflikt (drei disjunkte Aufgabenpaare dürfen nicht bei derselben Person liegen). **Modell:** eine Teilmenge davon; das **Modell-Optimum** hat die kleinsten Kosten unter den Nebenbedingungen des Modells (bei Gleichstand der kleinste Index der Aufzählung), das **wirkliche Optimum** unter allen vier. **Scheinersparnis** ist `(Kosten wirklich − Kosten Modell) / Kosten wirklich`. **Prüfen und Nachbessern:** das Modell lösen, gegen die Wirklichkeit prüfen, verletzte Nebenbedingungen aufnehmen (alle auf einmal oder eine je Runde), bis das Optimum wirklich zulässig ist. **Best-of-k** (aus Stück 8): unter k gleichverteilt aus den modellzulässigen Zuordnungen gezogenen die billigste wählen, Erwartung exakt aus der Ordnungsstatistik. Formeln stehen im 📐-Expander der App.

## Methodik

Drei Kostenfamilien: **unabhängig** (1 bis 99), **Personeneffekt (mittel)** (Personeneffekt 0 bis 40 plus 1 bis 60) und **Personeneffekt (stark)** (0 bis 150 plus 1 bis 30). Die App zeigt: das Modell-Optimum gegen das wirkliche Optimum (Kosten, Zuordnung, Verletzungen), die Punktwolke aller Zuordnungen (Kosten gegen Überlast), je Nebenbedingung als einzige ausgelassen die Scheinersparnis, den Kapazitätsfaktor, Prüfen und Nachbessern Runde für Runde, einen Auffälligkeitstest und die Kurve von Stück 8 im Modell. Zählungen über 20 feste Instanzen (4 Personen, 8 Aufgaben, alle 65 536 Zuordnungen) liegen hinter Schaltern. Verdikte entstehen live aus der Rechnung, jede Zahl im Text kommt aus dem Ergebnis.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stammen aus den Auswertungsfunktionen der App und sind in `tests/test_claims.py` nachgerechnet. „Je 20 feste Instanzen“ heißt `SWEEP_SEEDS` (Seeds 100000 bis 100019), nie ein einzelner Seed; die Zahlen sind **Zählungen und Spannen über Instanzen**, kein Satz und keine Aussage über andere Instanzen. Soweit nicht anders angegeben 4 Personen, 8 Aufgaben, `f = 1,25`. Familien: unabhängig / Person / star.

| Frage | Befund |
|---|---|
| Modell ohne jede Nebenbedingung: Aufgaben bei der am stärksten belasteten Person (Minimum / Median / Maximum) | 2 / 4 / 4; 3 / 4 / 6; 4 / 8 / 8; **alle 8 bei einer Person in 0 / 0 / 13 von 20**; mindestens 3 Personen ohne Aufgabe in 0 / 0 / 13 |
| dabei: Überlast in Stunden (Minimum / Median / Maximum) | 0 / 7 / 19; 2 / 10 / 24; 7 / 26 / 48 |
| dabei: **Scheinersparnis** (Minimum / Median / Maximum) | 0,0 % / 33,4 % / 67,4 %; 13,8 % / 26,9 % / 43,9 %; 19,8 % / 42,4 % / 76,2 % |
| wirklich zulässige Zuordnungen von 65 536 (Minimum / Median / Maximum) | unabhängig 15 / 444 / 1 676 (0,02 % / 0,68 % / 2,56 %); Person und star 34 / 442 / 914 (0,05 % / 0,67 % / 1,39 %) |
| Fehlt nur die **Kapazität**: Instanzen mit Verletzung; Überlast (Median; Maximum); Scheinersparnis (Median; Maximum) | **18 / 20 / 20** von 20; 5,5 (15) / 8,0 (16) / 11,0 (24) Stunden; 15,7 % (48,8 %) / 7,4 % (26,5 %) / 11,8 % (24,4 %) |
| Fehlt nur die **Mindestbesetzung** | verletzt in **3 / 4 / 12** von 20 (je eine Person ohne Aufgabe); Scheinersparnis Median **0,0 % / 0,0 % / 0,7 %** (Maximum 10,4 % / 4,5 % / 24,1 %) |
| Fehlt nur die **Qualifikation** | verletzt in **17 / 19 / 18** von 20 (Median 2 verbotene Paare, Maximum 4 / 4 / 3); Scheinersparnis Median **20,0 % / 11,6 % / 5,6 %** (Maximum **62,4 %** / 31,0 % / 18,0 %) |
| Fehlt nur der **Konflikt** | verletzt in 11 / 13 / 16 von 20; Scheinersparnis Median 1,7 % / 1,8 % / 2,6 % (Maximum 23,7 % / 10,7 % / 18,1 %) |
| Kapazitätsfaktor f = 1,0 / 1,25 / 1,5 / 2,0 (Kapazität 10 / 13 / 15 / 20 Stunden), fehlt nur K, unabhängig: Instanzen mit Überlast; Überlast (Median); Scheinersparnis (Median; Maximum) | **20 / 18 / 14 / 6** von 20; 10,0 / 5,0 / 2,5 / 0,0; 29,1 % (60,0 %) / 15,7 % (48,8 %) / 3,1 % (35,4 %) / 0,0 % (11,2 %); bei f = 1,0 ist in **2** von 20 Instanzen mit allen vier Nebenbedingungen nichts zulässig (ausgenommen) |
| Gleichstände im Modell (unabhängig): Der erste Optimalplan ist wirklich zulässig in … von 20, fehlt K / B / Q / W / alles | **2 / 17 / 3 / 9 / 0**; die Optimalmenge hat im Median einen Plan (Maximum 2) |
| Prüfen und Nachbessern, alle verletzten auf einmal: Runden (Minimum / Median / Maximum); Verteilung 1 / 2 / 3 Runden | unabhängig 1 / 1 / 3; 11 / 8 / 1 von 20; Person 1 / 1 / 2; 16 / 4 / 0; **eine je Runde** unabhängig 1 / 3 / 4 Runden (2 / 7 / 9 / 2 von 20 für 1 bis 4), Person 1 / 3 / 4 (1 / 5 / 6 / 8); Ergebnis gleich dem wirklichen Optimum in **20 / 20** |
| Auffälligkeitstest (Last des Höchstbelasteten ≥ 1,5 × Mittel), Modell ohne K: schlägt an bei Überlast; ohne Überlast; **das wirkliche Optimum schlägt an** | unabhängig 14 von 18; 1 von 2; **7 von 20**. Person 17 von 20; 0 von 0; **4 von 20**. star 19 von 20; 0 von 0; **12 von 20** |
| Best-of-k im Modell ohne Nebenbedingung (unabhängig), k = 1 / 4 / 16 / 64 / 256 / 1 024 / 4 096 / ∞: Wahrscheinlichkeit einer wirklich zulässigen Wahl (Median) | 0,68 % / 0,56 % / 0,59 % / 0,15 % / 0,00 % / 0,00 % / 0,00 % / 0,00 % |
| dasselbe: erwartete Kosten (Median) | 391,1 / 314,6 / 261,3 / 224,5 / 198,6 / 178,6 / 163,9 / 147,5; erwartete Überlast 6,7 / 6,8 / 6,8 / 6,6 / 6,7 / 6,5 / 6,0 / 7,0 Stunden |
| Preset „Das Modell ohne Nebenbedingung“ (Seed 100018) | Kosten **94** statt **242**, Scheinersparnis **61,2 %**; verletzt: Überlast **16** Stunden, 1 Person ohne Aufgabe, 1 verbotenes Paar, 1 Konflikt; **495** von 65 536 Zuordnungen wirklich zulässig; Nachbessern: **1** Runde (alle) beziehungsweise **2** (eine je Runde) |
| Preset „Alle Aufgaben bei einer Person“ (star, Seed 100003) | Kosten **177** statt **551** (**67,9 %**), alle 8 Aufgaben bei Person 2, Überlast **22** Stunden, **3** Personen ohne Aufgabe; eine je Runde **3** Runden |
| Presets „Es fehlt nur die Kapazität“ und „… nur die Qualifikation“ (Seed 100014, **15** zulässige Zuordnungen) | ohne K: Kosten **270** statt **440** (**38,6 %**), Überlast **12** Stunden; ohne Q: Kosten **212** statt **440** (**51,8 %**), **4** verbotene Paare |
| Preset „Es fehlt nur die Mindestbesetzung“ (Seed 100000) | das Modell wählt Kosten **146**, genau das wirkliche Optimum: Scheinersparnis **0** |
| Preset „Enge Kapazität, die im Modell fehlt“ (f = 1,0, Seed 100000) | Kapazität **10** Stunden, Überlast **9**, Kosten **139** statt **205** (**32,2 %**) |
| Preset „Kleinstes Beispiel“ (2 Personen, 3 Aufgaben, Seed 0) | **1** von 8 Zuordnungen zulässig; Kosten **63** statt **167** (**62,3 %**): alle drei Aufgaben bei einer Person, Überlast **14** Stunden |

**Korrektur der Planungshypothese:** Die Gliederung sagte „fehlende Mindestbesetzung: alle Aufgaben bei der billigsten Person“. Das trifft **nur bei einem starken Personeneffekt** zu (13 von 20 in der Familie star, 0 von 20 bei unabhängigen Kosten) und ist **nicht** die wichtigste Lücke: die fehlende Mindestbesetzung kostet kaum Scheinersparnis (Median 0,0 % bis 0,7 %), Kapazität und Qualifikation bis zu 62 %. Auch die Vermutung „stärkerer Druck, mehr Verletzung“ stimmt nicht: im Modell ohne Nebenbedingung verletzt schon ein Zufallsplan fast alles (0,68 % wirklich zulässig); mit dem Druck wächst die Billigkeit, nicht die Zahl der Verletzungen. Die Messreihe hatte außerdem bei f = 1,0 zwei Instanzen ohne zulässige Zuordnung nicht ausgewiesen; die App zeigt sie als „unlösbar“. Der einfache Auffälligkeitstest schlägt auch beim wirklichen Optimum an, und ein Alarm ohne Prüfung gegen die Nebenbedingung sagt wenig. Von der Literatur ist nur gelesen: Amodei u. a. („Concrete Problems in AI Safety“, arXiv 1606.06565, Abstract; zwei der fünf Probleme kommen von einem falschen Ziel, darunter „avoiding side effects“ und „avoiding reward hacking“) und die Definition von Krakovna u. a. (Google DeepMind, 2020): „Specification gaming is a behaviour that satisfies the literal specification of an objective without achieving the intended outcome.“ Ein echter Fall derselben Art ist FK-011 im Fehlerkatalog (`battery-arbitrage-demo`: die LP-Relaxierung erlaubt, Verlustenergie gegen Bezahlung zu „verbrennen“).

## Ehrliche Grenzen

- **Ein Zufallsmodell:** Qualifikation (20 % verboten), Konflikt (drei Paare) und Kapazität (1,25-fach) sind gewählte Größen; echte Pläne haben andere und mehr Nebenbedingungen.
- **Alle Zuordnungen aufgezählt:** bis 390 625; bei größeren Problemen braucht es einen Löser. Das Verhalten der Lücken ändert sich dadurch nicht, die Aufzählung ist der exakte Beweis.
- **Gleichstand: kleinster Index:** Das Modell-Optimum ist fast immer eindeutig (Median ein Plan); bei Gleichstand wählt die Regel, nicht das Ziel (Stück 5).
- **Prüfen heißt: alle vier Nebenbedingungen sind bekannt:** Das Nachbessern kennt die Wirklichkeit; eine unbekannte Nebenbedingung findet es nicht.
- **Der Auffälligkeitstest ist eine Regel mit einer Schwelle:** er sieht nur die Last, nicht die Qualifikation oder den Konflikt.
- **Kein Satz:** „diese Lücke ist die wichtigste“ gilt für diese Familien und diese Parameter, nicht allgemein; die Zahlen sind Zählungen über 20 feste Instanzen.

## Verifikation

Insgesamt 380 Tests (`pytest tests/`), alle grün.

- **Kern:** Handbeispiel (2 Personen, 3 Aufgaben, acht Zuordnungen) von Hand: Kosten und alle vier Verletzungsgrößen jeder Zuordnung, die Optima für die wichtigen Teilmengen, Scheinersparnis 1/3, beide Modi von Prüfen und Nachbessern (1 und 2 Runden), Best-of-k gegen die Formel; Verletzungen, Optimum je Teilmenge der Nebenbedingungen (alle 16), Prüfen und Nachbessern und die Kapazitätsformel gegen reines Python (`itertools.product`, Schleifen, `fractions.Fraction`); Best-of-k gegen die Aufzählung **aller** Ziehungen.
- **Eigenschaften:** das Modell-Optimum ist nie teurer als das wirkliche (Scheinersparnis nicht negativ); mehr Nebenbedingungen im Modell machen das Optimum nie billiger; sind alle im Modell, ist die Lösung wirklich zulässig; Nachbessern endet nach höchstens vier Runden im wirklichen Optimum, die Kosten fallen nie; die Kosten der Optima hängen nicht von der Nummerierung der Personen ab; größere Kapazität schadet nie; Best-of-k: `k = 1` ist der Mittelwert, die erwarteten Kosten fallen; Determinismus.
- **Randfälle:** nichts zulässig (Kapazität zu klein), genau eine zulässige Zuordnung, sehr große Kapazität, Gleichstand im Modell, eine Aufgabe nur mit einer erlaubten Person, jede Familie mal jede Schalterkombination, kleinste und größte Instanz, Aufzählungsgrenze.
- **Verdikte:** reine Funktionen, jede Verzweigung und jede Zahl im Text an Hand- oder Presetwerten (`tests/test_verdicts.py`).
- **Presets:** Vollständigkeit, Werte innerhalb der Reglergrenzen, Standard-Preset gleich Standardeinstellung, kein anderes Preset gleich den Voreinstellungen, und dass jedes Preset zeigt, was sein Name sagt.
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler am Minimum und Maximum), jedes Preset, jeder Schalter, jede Familie, Kapazität, Größen, beide Modi, alle Zählungen, Footer-Test, Layout.
- **Claims:** jede Zahl dieser README in `tests/test_claims.py`.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `mlk_algorithm.py` | Kern: Aufzählung, Nebenbedingungen, Optimum je Modell, Prüfen und Nachbessern, Best-of-k |
| `mlk_constants.py` | Regler-Grenzen, feste Annahmen, Farben, Presets |
| `mlk_evaluation.py` | Experimente, Sweeps, Verdikte |
| `mlk_layout.py` | Fester Kopf (Stylesheet) |
| `mlk_pdf_export.py` | PDF-Export des Ergebnisses |
| `mlk_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste), Zufalls-Seed-Button |
| `mlk_scenario.py` | Instanzen (Kosten, Zeit, verbotene Paare, Konfliktpaare, Kapazität) |
| `mlk_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tests/` | Handbeispiel, Orakel, Eigenschaften, Randfälle, Verdikte, Presets, Claims, Layout, AppTest-Smoke-Test, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Keine Verlagerung in eine nicht gemessene Größe:** Das Wandern der Last in eine Größe, die niemand misst, ist Stück 10; hier fehlt eine **Nebenbedingung**.
- **Kein Test, der die Lücke findet:** Wie man das Ziel vor dem Einsatz gegen die Wirklichkeit prüft, ist Stück 13; hier nur die Messung, dass ein einfacher Test nur halb taugt.
- **Kein Strafterm:** Die Nebenbedingung weich oder hart ins Ziel zu nehmen, ist Stück 6.
- **Kein Löser:** Alle Zuordnungen sind aufgezählt.
- **Keine Nachbauten der Literatur:** Weder „reward hacking“ noch „specification gaming“ sind nachgebaut (nur Abstract und Definition sind gelesen).

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und SciPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
