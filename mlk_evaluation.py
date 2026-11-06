"""Kennzahlen, Verdikt-Logik und Sweeps. Verdikte sind reine Funktionen (Art, Text); jede Zahl im Text kommt aus der Rechnung.

Gefragt wird: Was nutzt der Optimierer aus, wenn dem Modell Nebenbedingungen der Wirklichkeit fehlen? Wie viel billiger sieht seine Lösung aus (Scheinersparnis), was verletzt sie,
welche fehlende Nebenbedingung zählt am meisten, wie viele Runden „Prüfen und Nachbessern“ braucht man, und taugt ein einfacher Auffälligkeitstest?"""

from dataclasses import dataclass, replace

import numpy as np

import mlk_algorithm as A
import mlk_constants as C
import mlk_scenario as S


def de(x: float, digits: int = 1) -> str:
    """Zahl mit Dezimalkomma; kein „-0,0“."""
    text = f"{x:.{digits}f}"
    if float(text) == 0.0:
        text = f"{0.0:.{digits}f}"
    return text.replace(".", ",")


def pct(x: float, digits: int = 1) -> str:
    """Anteil als Prozent: 0,05 -> „5,0 %“."""
    return de(x * 100.0, digits) + " %"


def names(keys) -> str:
    """„Kapazität, Qualifikation“ (oder „keine“)."""
    return ", ".join(C.KEY_NAMES[k] for k in keys) if keys else "keine"


def model_text(keys) -> str:
    """„ohne Nebenbedingung“ oder „mit Kapazität, Qualifikation“."""
    return f"mit {names(keys)}" if keys else "ohne Nebenbedingung"


@dataclass(frozen=True)
class Settings:
    n: int = C.DEFAULT_N
    m: int = C.DEFAULT_M
    family: int = C.DEFAULT_FAMILY
    seed: int = C.DEFAULT_SEED
    cap: int = C.DEFAULT_CAP
    k_in: bool = C.DEFAULT_IN["K"]
    b_in: bool = C.DEFAULT_IN["B"]
    q_in: bool = C.DEFAULT_IN["Q"]
    w_in: bool = C.DEFAULT_IN["W"]

    @property
    def keys(self) -> tuple:
        """Die Nebenbedingungen, die das Modell kennt (in der Reihenfolge K, B, Q, W)."""
        flags = {"K": self.k_in, "B": self.b_in, "Q": self.q_in, "W": self.w_in}
        return tuple(k for k in C.KEYS if flags[k])


@dataclass
class Analysis:
    settings: Settings
    p: A.Problem
    model: tuple | None        # (erster Optimalplan, alle Optimalpläne) des Modells; None, wenn das Modell unlösbar ist
    real: tuple | None         # dasselbe für die Wirklichkeit (alle vier Nebenbedingungen)


def analyse(settings: Settings) -> Analysis:
    inst = S.make_instance(settings.n, settings.m, settings.family, settings.seed, settings.cap)
    p = A.build(inst)
    return Analysis(settings, p, A.optimum(p, settings.keys), A.optimum(p, C.KEYS))


# --- Experimente auf einer Instanz ---------------------------------------------------------------------------------------------------------

def compare(a: Analysis) -> dict:
    """Modell-Optimum gegen wirkliches Optimum: Kosten, Scheinersparnis, Verletzungen, Zulässigkeit insgesamt."""
    p, keys = a.p, a.settings.keys
    n_real = int(p.feasible(C.KEYS).sum())
    out = {"keys": keys, "n_plans": p.n_plans, "n_real": n_real, "share_real": n_real / p.n_plans, "n_model": int(p.feasible(keys).sum()), "model": None, "real": None}
    if a.model is not None:
        j, opt = a.model
        real_ok = p.feasible(C.KEYS)[opt]
        out["model"] = {"idx": j, "cost": int(p.cost[j]), "plan": p.X[j].astype(int), "violated": A.violated(p, j), "n_opt": len(opt), "first_ok": bool(p.feasible(C.KEYS)[j]), "any_ok": bool(real_ok.any()),
                        "counts": p.counts[j].astype(int), "loads": p.loads[j].astype(int)}
    if a.real is not None:
        r, opt = a.real
        out["real"] = {"idx": r, "cost": int(p.cost[r]), "plan": p.X[r].astype(int), "n_opt": len(opt), "counts": p.counts[r].astype(int), "loads": p.loads[r].astype(int)}
    out["saving"] = A.saving(out["real"]["cost"], out["model"]["cost"]) if out["model"] and out["real"] else None
    return out


def omit_rows(a: Analysis) -> list[dict]:
    """Je Nebenbedingung als einzige ausgelassen (alle anderen im Modell): Verletzung, Größe, Scheinersparnis."""
    p = a.p
    real = a.real
    rows = []
    for omit in C.KEYS:
        keys = tuple(k for k in C.KEYS if k != omit)
        res = A.optimum(p, keys)
        row = {"omit": omit, "idx": None, "cost": None, "size": 0, "violated": False, "saving": None}
        if res is not None:
            j = res[0]
            row.update({"idx": j, "cost": int(p.cost[j]), "size": int(p.viol[omit][j]), "violated": int(p.viol[omit][j]) > 0})
            if real is not None:
                row["saving"] = A.saving(int(p.cost[real[0]]), int(p.cost[j]))
        rows.append(row)
    return rows


def cap_rows(a: Analysis, caps=C.SWEEP_CAPS) -> list[dict]:
    """Kapazitätsfaktor f: ohne Kapazität im Modell (die anderen drin): Überlast, Scheinersparnis; mit der Kapazität der Wirklichkeit bei jedem f."""
    rows = []
    base = a.p
    inst = base.inst
    a_, b_, _ = inst.arrays()
    for pc in caps:
        cap = S.capacity(b_, inst.n, pc)
        p = A.with_cap(base, cap)
        res = A.optimum(p, ("B", "Q", "W"))
        real = A.optimum(p, C.KEYS)
        row = {"cap_pct": pc, "cap": cap, "over": None, "saving": None, "violated": False}
        if res is not None:
            j = res[0]
            row.update({"over": int(p.over[j]), "violated": int(p.over[j]) > 0})
            if real is not None:
                row["saving"] = A.saving(int(p.cost[real[0]]), int(p.cost[j]))
        rows.append(row)
    return rows


def repair_rows(a: Analysis, mode: str = "all") -> list[dict]:
    return A.repair(a.p, mode)


def flag_check(a: Analysis) -> dict:
    """Auffälligkeitstest an der Modell-Lösung und am wirklichen Optimum."""
    out = {"model": None, "real": None}
    if a.model is not None:
        j = a.model[0]
        out["model"] = {"flagged": A.flagged(a.p.loads[j]), "ratio": float(a.p.loads[j].max() / a.p.loads[j].mean()) if a.p.loads[j].mean() else 0.0, "overload": int(a.p.over[j])}
    if a.real is not None:
        r = a.real[0]
        out["real"] = {"flagged": A.flagged(a.p.loads[r]), "ratio": float(a.p.loads[r].max() / a.p.loads[r].mean()) if a.p.loads[r].mean() else 0.0}
    return out


def pressure(a: Analysis) -> dict:
    return A.best_of_k(a.p, a.settings.keys)


# --- Sweeps über feste Instanzen -----------------------------------------------------------------------------------------------------------

def _q3(vals) -> tuple[float, float, float]:
    v = np.asarray(vals, dtype=float)
    return float(v.min()), float(np.median(v)), float(v.max())


def _record(family: int, seed: int, with_pressure: bool) -> dict:
    inst = S.make_instance(C.SWEEP_N, C.SWEEP_M, family, seed)
    p = A.build(inst)
    real = A.optimum(p, C.KEYS)
    r = real[0]                                          # mit 4 Personen, 8 Aufgaben und f = 125 % hat jede feste Instanz eine zulässige Zuordnung (geprüft im Test)
    rc = int(p.cost[r])
    rec = {"family": family, "seed": seed, "n_real": int(p.feasible(C.KEYS).sum()), "n_plans": p.n_plans}
    j, _ = A.optimum(p, ())
    rec["none"] = {"conc": int(p.counts[j].max()), "idle": int(p.idle[j]), "over": int(p.over[j]), "saving": A.saving(rc, int(p.cost[j]))}
    om = {}
    for omit in C.KEYS:
        keys = tuple(k for k in C.KEYS if k != omit)
        jj, opt = A.optimum(p, keys)
        real_ok = p.feasible(C.KEYS)
        om[omit] = {"size": int(p.viol[omit][jj]), "saving": A.saving(rc, int(p.cost[jj])), "n_opt": len(opt), "first_ok": bool(real_ok[jj]), "any_ok": bool(real_ok[opt].any())}
    jn, optn = A.optimum(p, ())
    om["none"] = {"n_opt": len(optn), "first_ok": bool(p.feasible(C.KEYS)[jn]), "any_ok": bool(p.feasible(C.KEYS)[optn].any())}
    rec["omit"] = om
    caps = []
    _, b_, _ = inst.arrays()
    for pc in C.SWEEP_CAPS:
        pp = A.with_cap(p, S.capacity(b_, inst.n, pc))
        jj, _ = A.optimum(pp, ("B", "Q", "W"))
        rr = A.optimum(pp, C.KEYS)
        caps.append({"cap_pct": pc, "cap": pp.inst.cap, "over": int(pp.over[jj]), "saving": None if rr is None else A.saving(int(pp.cost[rr[0]]), int(pp.cost[jj]))})
    rec["caps"] = caps
    rec["repair"] = {mode: {"rounds": len(A.repair(p, mode)) - 1, "same": int(A.repair(p, mode)[-1]["cost"]) == rc} for mode in ("all", "one")}
    jk, _ = A.optimum(p, ("B", "Q", "W"))
    rec["flag"] = {"over": int(p.over[jk]), "model_flag": A.flagged(p.loads[jk]), "real_flag": A.flagged(p.loads[r])}
    if with_pressure:
        rec["pressure"] = A.best_of_k(p, ())
    return rec


def sweep_all(families=C.SWEEP_FAMILIES, seeds=C.SWEEP_SEEDS) -> dict:
    """Je Familie 20 feste Instanzen (4 Personen, 8 Aufgaben, alle 65 536 Zuordnungen): alle Kennzahlen in einem Durchgang; die Zusammenfassungen unten lesen daraus."""
    return {fam: [_record(fam, s, with_pressure=(fam == 0)) for s in seeds] for fam in families}


def summary_none(recs: list[dict]) -> dict:
    """Modell ohne jede Nebenbedingung."""
    return {"conc": _q3([r["none"]["conc"] for r in recs]), "all_one": sum(r["none"]["conc"] == r["none"]["conc"] and r["none"]["conc"] >= C.SWEEP_M for r in recs),
            "idle3": sum(r["none"]["idle"] >= 3 for r in recs), "over": _q3([r["none"]["over"] for r in recs]), "saving": _q3([r["none"]["saving"] for r in recs]),
            "n_real": _q3([r["n_real"] for r in recs]), "share_real": _q3([r["n_real"] / r["n_plans"] for r in recs]), "seeds": len(recs)}


def summary_omit(recs: list[dict]) -> dict:
    """Je ausgelassene Nebenbedingung: Instanzen mit Verletzung, Größe, Scheinersparnis, Optimalmenge, erster Optimalplan wirklich zulässig."""
    out = {}
    for k in C.KEYS:
        sizes = [r["omit"][k]["size"] for r in recs if r["omit"][k]["size"] > 0]
        out[k] = {"violated": len(sizes), "size_med": float(np.median(sizes)) if sizes else 0.0, "size_max": max(sizes) if sizes else 0, "saving": _q3([r["omit"][k]["saving"] for r in recs]),
                  "n_opt": _q3([r["omit"][k]["n_opt"] for r in recs]), "first_ok": sum(r["omit"][k]["first_ok"] for r in recs), "any_ok": sum(r["omit"][k]["any_ok"] for r in recs), "seeds": len(recs)}
    out["none"] = {"first_ok": sum(r["omit"]["none"]["first_ok"] for r in recs), "any_ok": sum(r["omit"]["none"]["any_ok"] for r in recs), "n_opt": _q3([r["omit"]["none"]["n_opt"] for r in recs])}
    return out


def summary_caps(recs: list[dict]) -> list[dict]:
    rows = []
    for i, pc in enumerate(C.SWEEP_CAPS):
        solvable = [r for r in recs if r["caps"][i]["saving"] is not None]
        rows.append({"cap_pct": pc, "cap": recs[0]["caps"][i]["cap"], "violated": sum(r["caps"][i]["over"] > 0 for r in recs), "over_med": float(np.median([r["caps"][i]["over"] for r in recs])),
                     "saving": _q3([r["caps"][i]["saving"] for r in solvable]) if solvable else (0.0, 0.0, 0.0), "unsolvable": len(recs) - len(solvable), "seeds": len(recs)})
    return rows


def summary_repair(recs: list[dict]) -> dict:
    out = {}
    for mode in ("all", "one"):
        rounds = [r["repair"][mode]["rounds"] for r in recs]
        out[mode] = {"rounds": _q3(rounds), "hist": np.bincount(rounds).tolist(), "same": sum(r["repair"][mode]["same"] for r in recs), "seeds": len(recs)}
    return out


def summary_flag(recs: list[dict]) -> dict:
    over = [r for r in recs if r["flag"]["over"] > 0]
    ok = [r for r in recs if r["flag"]["over"] == 0]
    return {"n_over": len(over), "flag_over": sum(r["flag"]["model_flag"] for r in over), "n_ok": len(ok), "flag_ok": sum(r["flag"]["model_flag"] for r in ok), "real_flag": sum(r["flag"]["real_flag"] for r in recs), "seeds": len(recs)}


def summary_pressure(recs: list[dict]) -> dict:
    ks = recs[0]["pressure"]["ks"]
    out = {"ks": ks}
    for key in ("p_real", "cost", "over", "forbid"):
        out[key] = [float(np.median([r["pressure"][key][i] for r in recs])) for i in range(len(ks))]
    return out


# --- Verdikte ------------------------------------------------------------------------------------------------------------------------------

def _violation_text(v: dict) -> str:
    parts = []
    if v.get("K"):
        parts.append(f"Überlast {v['K']} Stunden")
    if v.get("B"):
        parts.append(f"{v['B']} {'Person' if v['B'] == 1 else 'Personen'} ohne Aufgabe")
    if v.get("Q"):
        parts.append(f"{v['Q']} verbotene{'s Paar' if v['Q'] == 1 else ' Paare'}")
    if v.get("W"):
        parts.append(f"{v['W']} verletzte{'r Konflikt' if v['W'] == 1 else ' Konflikte'}")
    return ", ".join(parts)


def verdict_compare(c: dict) -> tuple[str, str]:
    """Experiment Modell: was wählt das Modell, und wie billig sieht es aus?"""
    if c["real"] is None:
        return "warning", f"In der Wirklichkeit ist **keine** Zuordnung zulässig (alle vier Nebenbedingungen zusammen): das Problem ist unlösbar; das Modell {model_text(c['keys'])} kennt das nicht."
    if c["model"] is None:
        return "warning", f"Schon das Modell {model_text(c['keys'])} hat keine zulässige Zuordnung."
    v = {k: x for k, x in c["model"]["violated"].items() if x > 0 and k not in c["keys"]}
    if not v:
        if c["model"]["cost"] == c["real"]["cost"]:
            extra = " Das Modell kennt alle Nebenbedingungen, die hier zählen: keine Lücke." if len(c["keys"]) == 4 else " Hier ist keine fehlende Nebenbedingung verletzt: das Modell liegt zufällig richtig."
            return "success", f"Das Modell {model_text(c['keys'])} wählt Kosten {c['model']['cost']}, genau das wirkliche Optimum.{extra}"
        return "info", f"Das Modell wählt Kosten {c['model']['cost']}, das wirkliche Optimum kostet {c['real']['cost']}: die Lösung ist zulässig, aber nicht optimal."
    return "warning", (f"Das Modell {model_text(c['keys'])} wählt Kosten **{c['model']['cost']}** und verletzt, was fehlt: **{_violation_text(v)}**. Das wirkliche Optimum kostet {c['real']['cost']}: "
                       f"die Lösung des Modells sieht **{pct(c['saving'])} billiger** aus, als sie sein kann (Scheinersparnis). Wirklich zulässig sind {c['n_real']} von {c['n_plans']} Zuordnungen ({pct(c['share_real'], 2)}).")


def verdict_omit(rows: list[dict]) -> tuple[str, str]:
    """Experiment Welche Lücke: je Nebenbedingung als einzige ausgelassen."""
    parts = []
    for r in rows:
        if r["cost"] is None:
            parts.append(f"ohne {C.KEY_NAMES[r['omit']]}: unlösbar")
        elif r["violated"]:
            parts.append(f"ohne {C.KEY_NAMES[r['omit']]} verletzt (Größe {r['size']}, Scheinersparnis {pct(r['saving'])})")
        else:
            parts.append(f"ohne {C.KEY_NAMES[r['omit']]} nicht verletzt (Scheinersparnis {pct(r['saving'])})")
    worst = max((r for r in rows if r["saving"] is not None), key=lambda r: r["saving"], default=None)
    tail = f" Die größte Scheinersparnis entsteht ohne {C.KEY_NAMES[worst['omit']]} ({pct(worst['saving'])})." if worst and worst["saving"] > 0 else " Keine einzelne Lücke bringt hier Scheinersparnis."
    return "info", "; ".join(parts) + "." + tail


def verdict_cap(rows: list[dict]) -> tuple[str, str]:
    """Experiment Wie eng: Kapazitätsfaktor."""
    cells = [f"f = {r['cap_pct']} %: Kapazität {r['cap']} h, " + ("Überlast " + str(r["over"]) + " h, Scheinersparnis " + pct(r["saving"]) if r["saving"] is not None else "unlösbar") for r in rows if r["over"] is not None]
    first_ok = next((r for r in rows if r["over"] == 0), None)
    tail = f" Ab f = {first_ok['cap_pct']} % bindet die Kapazität bei dieser Instanz nicht mehr." if first_ok else " Bei keinem f verschwindet die Überlast."
    return "info", "Ohne Kapazität im Modell: " + "; ".join(cells) + "." + tail


def verdict_repair(rounds: list[dict]) -> tuple[str, str]:
    """Experiment Prüfen und Nachbessern."""
    last = rounds[-1]
    if last["idx"] is None:
        return "warning", "Prüfen und Nachbessern endet ohne Lösung: mit allen Nebenbedingungen ist nichts zulässig."
    n_rounds = len(rounds) - 1
    first = rounds[0]
    if n_rounds == 0:
        return "success", f"Schon das Modell ohne Nebenbedingung ist wirklich zulässig (Kosten {first['cost']}): keine Nachbesserung nötig."
    return "info", (f"Nach **{n_rounds}** {'Runde' if n_rounds == 1 else 'Runden'} Prüfen und Nachbessern ist das Optimum wirklich zulässig: die Kosten steigen von {first['cost']} auf **{last['cost']}** "
                    f"({pct((last['cost'] - first['cost']) / last['cost'])} der wirklichen Kosten waren Schein). Aufgenommen wurden: {names(tuple(k for r in rounds for k in r['add']))}.")


def verdict_flag(f: dict) -> tuple[str, str]:
    """Experiment Auffälligkeitstest."""
    if f["model"] is None or f["real"] is None:
        return "info", "Der Auffälligkeitstest braucht eine Lösung des Modells und eine der Wirklichkeit."
    m, r = f["model"], f["real"]
    text = (f"Die Last der am stärksten belasteten Person ist bei der Modell-Lösung das {de(m['ratio'], 2)}-fache der mittleren Last ({'schlägt an' if m['flagged'] else 'schlägt nicht an'}, Schwelle {de(C.FLAG_RATIO)}), "
            f"beim wirklichen Optimum das {de(r['ratio'], 2)}-fache ({'schlägt an' if r['flagged'] else 'schlägt nicht an'}).")
    if m["flagged"] and r["flagged"]:
        return "warning", text + " **Auch das wirkliche Optimum schlägt an:** ein Alarm ohne Prüfung gegen die Nebenbedingung sagt wenig."
    if m["overload"] > 0 and not m["flagged"]:
        return "warning", text + " Die Modell-Lösung hat Überlast und schlägt **nicht** an: der Test übersieht sie."
    return "info", text


def verdict_pressure(pr: dict) -> tuple[str, str]:
    """Experiment Druck: Best-of-k im Modell."""
    if not pr["cost"]:
        return "info", "Das Modell hat keine zulässige Zuordnung."
    k1, kinf = pr["p_real"][0], pr["p_real"][-1]
    return "info", (f"Mit stärkerem Druck (k von 1 bis ∞) fallen die erwarteten Kosten von {de(pr['cost'][0])} auf {de(pr['cost'][-1])}, und die Wahrscheinlichkeit einer wirklich zulässigen Wahl von {pct(k1, 2)} auf {pct(kinf, 2)}. "
                    f"Die Erwartung der Überlast liegt bei {de(pr['over'][0])} und {de(pr['over'][-1])} Stunden: der Druck macht die Lösung billiger, nicht unbedingt „mehr verletzt“.")


def verdict_none_sweep(s: dict, fam: str) -> str:
    return (f"{fam}: Aufgaben bei der am stärksten belasteten Person {int(s['conc'][0])} / {int(s['conc'][1])} / {int(s['conc'][2])} (Minimum / Median / Maximum), alle {C.SWEEP_M} bei einer Person in {s['all_one']} von {s['seeds']}, "
            f"mindestens 3 Personen ohne Aufgabe in {s['idle3']}; Überlast {int(s['over'][0])} / {int(s['over'][1])} / {int(s['over'][2])} Stunden; Scheinersparnis {pct(s['saving'][0])} / {pct(s['saving'][1])} / {pct(s['saving'][2])}; "
            f"wirklich zulässig {pct(s['share_real'][1], 2)} der Zuordnungen (Median)")


def verdict_omit_sweep(res: dict) -> tuple[str, str]:
    parts = []
    for fam, s in res.items():
        cells = [f"ohne {C.KEY_NAMES[k]}: verletzt in {s[k]['violated']} von {s[k]['seeds']}, Scheinersparnis Median {pct(s[k]['saving'][1])} (Maximum {pct(s[k]['saving'][2])})" for k in C.KEYS]
        parts.append(f"{C.FAMILIES[fam]}: " + "; ".join(cells))
    return "info", f"Je Nebenbedingung als einzige ausgelassen, {C.SWEEP_N} Personen, {C.SWEEP_M} Aufgaben, je {len(C.SWEEP_SEEDS)} feste Instanzen: " + ". ".join(parts) + "."


def verdict_cap_sweep(rows: list[dict]) -> tuple[str, str]:
    cells = [f"f = {r['cap_pct']} % (Kapazität {r['cap']} h): Überlast in {r['violated']} von {r['seeds']}, Scheinersparnis Median {pct(r['saving'][1])} (Maximum {pct(r['saving'][2])})"
             + (f"; in {r['unsolvable']} Instanzen ist mit allen Nebenbedingungen nichts zulässig" if r["unsolvable"] else "") for r in rows]
    return "info", "Ohne Kapazität im Modell, Kosten unabhängig: " + "; ".join(cells) + "."


def verdict_repair_sweep(res: dict) -> tuple[str, str]:
    parts = []
    for fam, s in res.items():
        parts.append(f"{C.FAMILIES[fam]}: alle auf einmal {int(s['all']['rounds'][0])} / {int(s['all']['rounds'][1])} / {int(s['all']['rounds'][2])} Runden (Verteilung {s['all']['hist'][1:]}), "
                     f"eine je Runde {int(s['one']['rounds'][0])} / {int(s['one']['rounds'][1])} / {int(s['one']['rounds'][2])} (Verteilung {s['one']['hist'][1:]}), Ergebnis gleich dem wirklichen Optimum in {s['all']['same']} von {s['all']['seeds']}")
    return "info", "Prüfen und Nachbessern (Runden: Minimum / Median / Maximum): " + "; ".join(parts) + "."


def verdict_flag_sweep(res: dict) -> tuple[str, str]:
    parts = [f"{C.FAMILIES[fam]}: bei Überlast ({s['n_over']} Instanzen) schlägt der Test in {s['flag_over']} an, ohne Überlast ({s['n_ok']}) in {s['flag_ok']}; das wirkliche Optimum schlägt in {s['real_flag']} von {s['seeds']} an" for fam, s in res.items()]
    return "info", f"Auffälligkeitstest (Last des Höchstbelasteten ≥ {de(C.FLAG_RATIO)} × Mittel), Modell ohne Kapazität: " + "; ".join(parts) + "."


def verdict_pressure_sweep(s: dict) -> tuple[str, str]:
    cells = [f"k = {'∞' if k is None else k}: Wahrscheinlichkeit zulässig {pct(s['p_real'][i], 2)}, E[Kosten] {de(s['cost'][i])}" for i, k in enumerate(s['ks'])]
    return "info", "Best-of-k im Modell ohne Nebenbedingung, Kosten unabhängig (Median über 20 Instanzen): " + "; ".join(cells) + "."
