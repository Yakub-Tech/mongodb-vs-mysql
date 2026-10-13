#!/usr/bin/env python3
"""
============================================================================
 summarize.py — Aggregiert die 10 Messungen nach Container-Neustart pro Szenario
============================================================================

Input:  /tmp/bench_results.csv  (80 Zeilen: 8 Szenarien × 10 Messungen)
Output: Textausgabe im Terminal mit Mittelwert, Standardabweichung,
        Minimum und Maximum pro Szenario.

Berechnung pro Szenario:
  Mittelwert     = arithmetisches Mittel der 10 Einzelmessungen
  Std.abw. (σ)   = Stichproben-Standardabweichung (n-1 Korrektur)
  Min / Max      = schnellste / langsamste der 10 Messungen
"""
import csv
import statistics
from collections import defaultdict

CSV_PATH = "/tmp/bench_results.csv"

# ── Einlesen: alle Messwerte pro Szenario sammeln ─────────────────────────
# Schlüssel = (db, operation, index_state), Wert = Liste der 10 Zeiten
groups = defaultdict(list)
with open(CSV_PATH) as f:
    r = csv.DictReader(f)
    for row in r:
        key = (row["db"], row["operation"], row["index_state"])
        groups[key].append(float(row["elapsed_ms"]))

# ── Tabelle drucken ────────────────────────────────────────────────────────
print()
print("=" * 92)
print(f"{'Szenario':<40} {'Mittelwert':>13} {'Std.abw.':>13} {'Min':>11} {'Max':>11}")
print("=" * 92)

# Feste Reihenfolge: erst alle Reads, dann alle Updates
order = [
    ("mysql", "read",   "without_index"),
    ("mysql", "read",   "with_index"),
    ("mongo", "read",   "without_index"),
    ("mongo", "read",   "with_index"),
    ("mysql", "update", "without_index"),
    ("mysql", "update", "with_index"),
    ("mongo", "update", "without_index"),
    ("mongo", "update", "with_index"),
]

for key in order:
    if key not in groups:
        continue
    vals = groups[key]

    # Statistik rechnen
    mean_ms  = statistics.mean(vals)
    # stdev braucht mindestens 2 Werte, sonst Exception
    stdev_ms = statistics.stdev(vals) if len(vals) > 1 else 0.0
    min_ms   = min(vals)
    max_ms   = max(vals)

    label = f"{key[0].upper():<6} {key[1]:<7} {key[2]}"
    print(f"{label:<40} "
          f"{mean_ms:>10.4f} ms "
          f"{stdev_ms:>10.4f} ms "
          f"{min_ms:>8.4f} ms "
          f"{max_ms:>8.4f} ms")

print("=" * 92)
print(f"Rohdaten (80 Einzelmessungen): {CSV_PATH}")
