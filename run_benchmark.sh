#!/usr/bin/env bash
# Acht Szenarien mit je zehn Messungen nach Container-Neustart.
# Die Daten bleiben in den Docker-Volumes erhalten. Ein Neustart garantiert
# keine leeren Caches; das Index-Setup kann Daten bereits vorab lesen.
# Voraussetzungen und Import: docs/SETUP.md. Vom Projektordner aus starten.
# Grobe Laufzeit des ursprünglichen Laufs: 16-20 Minuten.

set -e   # bei Fehler sofort abbrechen

# Pfade
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BENCH_PY="${SCRIPT_DIR}/benchmark.py"
SUMMARIZE_PY="${SCRIPT_DIR}/summarize.py"
RESULTS_CSV="/tmp/bench_results.csv"

# Anzahl Messungen pro Szenario
N_MEASUREMENTS=10

# Alte Ergebnisse wegräumen, sonst würden die hier angehängt werden
rm -f "$RESULTS_CSV"

# ── Die 8 Szenarien ────────────────────────────────────────────────────────
SCENARIOS=(
    "mysql read without_index"
    "mysql read with_index"
    "mongo read without_index"
    "mongo read with_index"
    "mysql update without_index"
    "mysql update with_index"
    "mongo update without_index"
    "mongo update with_index"
)

# ── Hilfsfunktion: Warten bis MySQL bereit ist ─────────────────────────────
wait_for_mysql() {
    echo -n "   warte auf MySQL"
    for i in {1..60}; do
        if docker exec onlineshop-mysql mysqladmin ping -uroot -proot --silent >/dev/null 2>&1; then
            echo " ✓"
            # Kleine Sicherheits-Wartezeit: "ping ok" heißt nicht 100% ready
            sleep 2
            return 0
        fi
        echo -n "."
        sleep 1
    done
    echo " ✗ Timeout"
    exit 1
}

# ── Hilfsfunktion: Warten bis MongoDB bereit ist ───────────────────────────
wait_for_mongo() {
    echo -n "   warte auf MongoDB"
    for i in {1..60}; do
        if docker exec onlineshop-mongodb mongosh --quiet --eval "db.adminCommand('ping')" >/dev/null 2>&1; then
            echo " ✓"
            sleep 1
            return 0
        fi
        echo -n "."
        sleep 1
    done
    echo " ✗ Timeout"
    exit 1
}

# ── Hilfsfunktion: Container komplett neu starten ─────────────────────────
cold_restart() {
    docker compose down >/dev/null 2>&1
    docker compose up -d >/dev/null 2>&1
    wait_for_mysql
    wait_for_mongo
}

# ── Hauptlauf ──────────────────────────────────────────────────────────────
echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║  Benchmark: MySQL vs MongoDB                                            ║"
echo "║  8 Szenarien × 10 Messungen nach Neustart = 80 Durchläufe                       ║"
echo "║  Vor JEDER einzelnen Messung: docker compose down + up                  ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"

total=0
total_max=$((${#SCENARIOS[@]} * N_MEASUREMENTS))

for scenario in "${SCENARIOS[@]}"; do
    read -r db op idx <<< "$scenario"
    echo
    echo "════════════════════════════════════════════════════════════════════"
    echo " Szenario: ${db} / ${op} / ${idx}"
    echo "════════════════════════════════════════════════════════════════════"

    for measurement in $(seq 1 $N_MEASUREMENTS); do
        total=$((total + 1))
        echo
        echo "── [${total}/${total_max}] Messung ${measurement}/${N_MEASUREMENTS} ──"
        cold_restart
        python3 "$BENCH_PY" "$db" "$op" "$idx" "$measurement"
    done
done

# ── Zusammenfassung anzeigen ───────────────────────────────────────────────
echo
echo "Alle Messungen fertig. Rechne Mittelwert und Standardabweichung aus..."
python3 "$SUMMARIZE_PY"
