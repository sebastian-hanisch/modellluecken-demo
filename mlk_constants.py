"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

N_MIN, N_MAX, DEFAULT_N = 2, 5, 4             # Personen
M_MIN, M_MAX, DEFAULT_M = 3, 8, 8             # Aufgaben; alle n^m Zuordnungen werden aufgezählt (bis 5^8 = 390 625)
SEED_MAX, DEFAULT_SEED = 999999, 100018
FAMILIES = ("Kosten unabhängig 1 bis 99", "Personeneffekt (mittel)", "Personeneffekt (stark)")
DEFAULT_FAMILY = 0
CAP_MIN, CAP_MAX, CAP_STEP, DEFAULT_CAP = 100, 200, 25, 125     # Kapazitätsfaktor f in Prozent: cap = aufgerundet f * (Summe der mittleren Zeiten) / n

KEYS = ("K", "B", "Q", "W")                   # Nebenbedingungen der Wirklichkeit, in der Reihenfolge der Nachbesserung
KEY_NAMES = {"K": "Kapazität", "B": "Mindestbesetzung", "Q": "Qualifikation", "W": "Konflikt"}
KEY_HELP = {"K": "Die Zeitsumme jeder Person ist höchstens die Kapazität.", "B": "Jede Person bekommt mindestens eine Aufgabe.",
            "Q": "Verbotene Paare (Person, Aufgabe) dürfen nicht vorkommen.", "W": "Konfliktpaare von Aufgaben dürfen nicht bei derselben Person liegen."}
DEFAULT_IN = {"K": False, "B": False, "Q": False, "W": False}       # Voreinstellung: das Modell kennt keine der vier Nebenbedingungen
FORBID_P = 0.2                                # Anteil verbotener Paare (Person, Aufgabe)
MAX_PAIRS = 3                                 # Konfliktpaare von Aufgaben

SWEEP_SEEDS = tuple(range(100000, 100020))    # feste Instanzen für alle Sweeps: nie ein einzelner Seed als Befund
SWEEP_N, SWEEP_M = 4, 8                       # Größe der Sweeps (alle 65 536 Zuordnungen)
SWEEP_FAMILIES = (0, 1, 2)
SWEEP_CAPS = (100, 125, 150, 200)
PRESSURE_KS = (1, 4, 16, 64, 256, 1024, 4096, None)
FLAG_RATIO = 1.5                              # Auffälligkeitstest: Last der am stärksten belasteten Person gegen die mittlere Last

COLOR_ALL = "rgba(150,150,150,0.35)"
COLOR_REAL = "#4c78a8"
COLOR_OK = "#2F6B65"
COLOR_BAD = "#c0504d"
COLOR_MARK = "#d8a13a"

PRESETS = {
    "Das Modell ohne Nebenbedingung": {"n": 4, "m": 8, "family": 0, "seed": 100018, "cap": 125, "K": False, "B": False, "Q": False, "W": False},
    "Alle Aufgaben bei einer Person": {"n": 4, "m": 8, "family": 2, "seed": 100003, "cap": 125, "K": False, "B": False, "Q": False, "W": False},
    "Es fehlt nur die Kapazität": {"n": 4, "m": 8, "family": 0, "seed": 100014, "cap": 125, "K": False, "B": True, "Q": True, "W": True},
    "Es fehlt nur die Qualifikation": {"n": 4, "m": 8, "family": 0, "seed": 100014, "cap": 125, "K": True, "B": True, "Q": False, "W": True},
    "Es fehlt nur die Mindestbesetzung": {"n": 4, "m": 8, "family": 0, "seed": 100000, "cap": 125, "K": True, "B": False, "Q": True, "W": True},
    "Enge Kapazität, die im Modell fehlt": {"n": 4, "m": 8, "family": 0, "seed": 100000, "cap": 100, "K": False, "B": True, "Q": True, "W": True},
    "Kleinstes Beispiel (2 Personen, 3 Aufgaben)": {"n": 2, "m": 3, "family": 0, "seed": 0, "cap": 125, "K": False, "B": False, "Q": False, "W": False},
    "Alles im Modell: keine Lücke": {"n": 4, "m": 8, "family": 0, "seed": 100018, "cap": 125, "K": True, "B": True, "Q": True, "W": True},
}
PRESET_HELP = {
    "Das Modell ohne Nebenbedingung": "Das Modell wählt Kosten 94 und verletzt alle vier Nebenbedingungen (16 Stunden Überlast); das wirkliche Optimum kostet 242: 61,2 % Scheinersparnis.",
    "Alle Aufgaben bei einer Person": "Bei starkem Personeneffekt landen alle 8 Aufgaben bei einer Person: Kosten 177 statt 551, 22 Stunden Überlast, drei Personen ohne Aufgabe.",
    "Es fehlt nur die Kapazität": "Mit allen anderen Nebenbedingungen wählt das Modell Kosten 270 statt 440 und überschreitet die Kapazität um 12 Stunden (38,6 % Scheinersparnis).",
    "Es fehlt nur die Qualifikation": "Dieselbe Instanz ohne die Qualifikation: Kosten 212 statt 440 mit 4 verbotenen Paaren (51,8 % Scheinersparnis).",
    "Es fehlt nur die Mindestbesetzung": "Hier lässt sich die Mindestbesetzung weglassen: das Modell wählt dieselbe Lösung wie die Wirklichkeit (Kosten 146).",
    "Enge Kapazität, die im Modell fehlt": "Bei knapper Kapazität (10 Stunden) überschreitet das Modell sie um 9 Stunden: Kosten 139 statt 205 (32,2 % Scheinersparnis).",
    "Kleinstes Beispiel (2 Personen, 3 Aufgaben)": "Acht Zuordnungen, nur eine ist wirklich zulässig: das Modell wählt Kosten 63 statt 167 (alle drei Aufgaben bei einer Person).",
    "Alles im Modell: keine Lücke": "Kennt das Modell alle vier Nebenbedingungen, wählt es das wirkliche Optimum: Scheinersparnis 0.",
}
