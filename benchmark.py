#!/usr/bin/env python3
"""Misst eine Lese- oder Update-Operation nach einem Container-Neustart.

run_benchmark.sh ruft dieses Script für acht Szenarien je zehnmal auf.
Der Index wird vor der Zeitmessung eingerichtet; der Cache-Zustand ist
nicht kontrolliert. Die feste Kunden-ID hält die Abfrage konstant.
Gemessen wird die vom Python-Treiber beobachtete Dauer in Millisekunden.
"""
import sys
import time       # time.perf_counter → hochpräzise Zeitmessung
import csv
import os

# ── Parameter vom Shellscript einlesen ─────────────────────────────────────
# Aufruf z.B.: python3 benchmark.py mysql read with_index 1
DB_TYPE     = sys.argv[1]     # "mysql" oder "mongo"
OPERATION   = sys.argv[2]     # "read" oder "update"
INDEX_STATE = sys.argv[3]     # "with_index" oder "without_index"
MEASUREMENT = int(sys.argv[4])  # Nummer der Messung (1..10) — nur zum Loggen

# ── Konfiguration ──────────────────────────────────────────────────────────
CSV_PATH = "/tmp/bench_results.csv"

# FESTE kunde_id für ALLE Messungen und ALLE Szenarien.
# So wird in jedem einzelnen Szenario und jeder Wiederholung exakt dieselbe
# Workload ausgeführt → direkter Vergleich zwischen MySQL und Mongo möglich,
# und direkte Vergleichbarkeit der 10 Wiederholungen untereinander.
FIXED_KUNDE_ID = 25000


# ═══════════════════════════════════════════════════════════════════════════
#  MySQL — eine einzige Operation messen
# ═══════════════════════════════════════════════════════════════════════════
def bench_mysql():
    import pymysql

    # Verbindung zur frisch neu gestarteten MySQL
    conn = pymysql.connect(
        host="127.0.0.1", port=3306,
        user="root", password="root",
        database="onlineshop",
        autocommit=True,
    )
    cur = conn.cursor()

    # ── Index-Zustand herstellen ───────────────────────────────────────────
    # MySQL legt auf Fremdschlüsseln AUTOMATISCH einen Index an. Für den
    # "ohne Index"-Fall müssen wir den FK-Constraint droppen, sonst lässt
    # MySQL den Index nicht löschen.
    cur.execute("SHOW INDEX FROM bestellung WHERE Key_name != 'PRIMARY'")
    existing_indexes = [row[2] for row in cur.fetchall()]  # row[2] = Key_name

    if INDEX_STATE == "with_index":
        if "idx_kunde" not in existing_indexes:
            cur.execute("CREATE INDEX idx_kunde ON bestellung(kundeID)")
    else:  # without_index
        # FK-Constraints auf kundeID finden und droppen
        cur.execute("""
            SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA='onlineshop' AND TABLE_NAME='bestellung'
              AND COLUMN_NAME='kundeID' AND REFERENCED_TABLE_NAME IS NOT NULL
        """)
        for (fk_name,) in cur.fetchall():
            cur.execute(f"ALTER TABLE bestellung DROP FOREIGN KEY {fk_name}")
        # Jetzt alle Indizes auf kundeID droppen
        cur.execute("SHOW INDEX FROM bestellung WHERE Column_name='kundeID'")
        for row in cur.fetchall():
            idx_name = row[2]
            if idx_name != "PRIMARY":
                cur.execute(f"DROP INDEX {idx_name} ON bestellung")

    # Das Index-Setup liegt außerhalb der Zeitmessung, kann aber Caches füllen.

    # ── Die EINE Messung ───────────────────────────────────────────────────
    if OPERATION == "read":
        t0 = time.perf_counter()
        cur.execute("SELECT * FROM bestellung WHERE kundeID = %s", (FIXED_KUNDE_ID,))
        cur.fetchall()   # Ergebnisse wirklich abholen, nicht nur Query absetzen
        elapsed_ms = (time.perf_counter() - t0) * 1000
    else:  # update
        t0 = time.perf_counter()
        cur.execute(
            "UPDATE bestellung SET status = 'bearbeitet' WHERE kundeID = %s",
            (FIXED_KUNDE_ID,),
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000

    cur.close()
    conn.close()
    return elapsed_ms


# ═══════════════════════════════════════════════════════════════════════════
#  MongoDB — eine einzige Operation messen
# ═══════════════════════════════════════════════════════════════════════════
def bench_mongo():
    from pymongo import MongoClient

    client = MongoClient("mongodb://127.0.0.1:27017/")
    db = client["onlineshop"]
    coll = db["bestellungen"]   # Plural! (in MySQL heißt die Tabelle "bestellung")

    # ── Index-Zustand herstellen ───────────────────────────────────────────
    # Mongo hat keine automatischen Indizes auf Feldern (außer _id).
    # Der Index auf kunde_id heißt standardmäßig "kunde_id_1".
    existing_indexes = [ix["name"] for ix in coll.list_indexes()]

    if INDEX_STATE == "with_index":
        if "kunde_id_1" not in existing_indexes:
            coll.create_index("kunde_id")
    else:
        if "kunde_id_1" in existing_indexes:
            coll.drop_index("kunde_id_1")

    # ── Die EINE Messung ───────────────────────────────────────────────────
    if OPERATION == "read":
        t0 = time.perf_counter()
        # list() zwingt den Cursor zum vollständigen Lesen — analog zum
        # fetchall() bei MySQL. Sonst würden wir nur das Absetzen der
        # Query messen, nicht die tatsächliche Datenübertragung.
        list(coll.find({"kunde_id": FIXED_KUNDE_ID}))
        elapsed_ms = (time.perf_counter() - t0) * 1000
    else:  # update
        t0 = time.perf_counter()
        # update_many weil ein Kunde mehrere Bestellungen haben kann und
        # wir alle treffen wollen (analog zum MySQL-UPDATE ohne LIMIT).
        coll.update_many({"kunde_id": FIXED_KUNDE_ID}, {"$set": {"status": "bearbeitet"}})
        elapsed_ms = (time.perf_counter() - t0) * 1000

    client.close()
    return elapsed_ms


# ═══════════════════════════════════════════════════════════════════════════
#  Main: richtige Benchmark-Funktion wählen, Ergebnis in CSV schreiben
# ═══════════════════════════════════════════════════════════════════════════
def main():
    if DB_TYPE == "mysql":
        elapsed_ms = bench_mysql()
    elif DB_TYPE == "mongo":
        elapsed_ms = bench_mongo()
    else:
        print(f"Unbekannte DB: {DB_TYPE}", file=sys.stderr)
        sys.exit(1)

    # Ergebnis an die CSV anhängen (Header einmalig beim ersten Schreiben)
    write_header = not os.path.exists(CSV_PATH)
    with open(CSV_PATH, "a", newline="") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(["db", "operation", "index_state", "measurement", "elapsed_ms"])
        w.writerow([DB_TYPE, OPERATION, INDEX_STATE, MEASUREMENT, f"{elapsed_ms:.4f}"])

    # Live-Ausgabe im Terminal
    print(f"  [{DB_TYPE}/{OPERATION}/{INDEX_STATE}] "
          f"Messung {MEASUREMENT}/10: {elapsed_ms:.4f} ms")


if __name__ == "__main__":
    main()
