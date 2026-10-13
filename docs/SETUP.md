# Setup und Datenimport

Alle Befehle gelten für Bash unter macOS, Linux oder WSL und werden im Projektordner ausgeführt. Python 3.9 oder neuer und Node.js werden benötigt. Docker muss laufen; die Ports 3306 und 27017 müssen frei sein. Die festen Containernamen `onlineshop-mysql` und `onlineshop-mongodb` dürfen nicht bereits von einer anderen Umgebung verwendet werden.

## 1. Python-Umgebung und Container

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
docker compose up -d
docker compose ps
```

Vor dem Import prüfen, ob beide Datenbanken Anfragen annehmen. Bei einem Fehler kurz warten und den jeweiligen Befehl wiederholen:

```bash
docker exec onlineshop-mysql mysql -uroot -proot onlineshop -e "SELECT 1;"
docker exec onlineshop-mongodb mongosh --quiet --eval 'db.adminCommand("ping")'
```

## 2. MySQL befüllen

**Achtung:** Das Schema entfernt vorhandene Shop-Tabellen samt Daten. Nur in der vorgesehenen Testumgebung importieren. Für einen erneuten Import immer zuerst das Schema laden.

```bash
docker exec -i onlineshop-mysql mysql -uroot -proot onlineshop < onlineshop_schema.sql
docker exec -i onlineshop-mysql mysql -uroot -proot onlineshop < onlineshop_mysql_testdaten.sql
```

Das Passwort `root` ist ein lokales Testpasswort. Die MySQL-Warnung zur Passwortübergabe über die Kommandozeile ist bei diesem Setup zu erwarten.

## 3. MongoDB befüllen

Der vorhandene Konverter erzeugt aus den `insertMany`-Blöcken drei JSONL-Dateien. Diese werden mit `mongoimport` importiert, sodass die große Seed-Datei nicht direkt in `mongosh` ausgeführt werden muss.

```bash
node convert_seed.js

docker cp produkte.jsonl onlineshop-mongodb:/tmp/produkte.jsonl
docker cp kunden.jsonl onlineshop-mongodb:/tmp/kunden.jsonl
docker cp bestellungen.jsonl onlineshop-mongodb:/tmp/bestellungen.jsonl

docker exec onlineshop-mongodb mongoimport --db onlineshop --collection produkte --file /tmp/produkte.jsonl --drop
docker exec onlineshop-mongodb mongoimport --db onlineshop --collection kunden --file /tmp/kunden.jsonl --drop
docker exec onlineshop-mongodb mongoimport --db onlineshop --collection bestellungen --file /tmp/bestellungen.jsonl --drop
```

**Achtung:** `--drop` entfernt die jeweilige vorhandene Collection samt Indizes und Daten. Dadurch ist ein erneuter Import ohne doppelte IDs möglich. Die generierten JSONL-Dateien sind durch `.gitignore` ausgeschlossen.

Erwartete Ausgabe des Konverters: 151 Blöcke und 100.500 Dokumente.

## 4. Datenbestand prüfen

```bash
docker exec onlineshop-mysql mysql -uroot -proot onlineshop -e "SELECT 'kategorie' AS objekt, COUNT(*) AS anzahl FROM kategorie UNION ALL SELECT 'produkt', COUNT(*) FROM produkt UNION ALL SELECT 'kunde', COUNT(*) FROM kunde UNION ALL SELECT 'kundenprofil', COUNT(*) FROM kundenprofil UNION ALL SELECT 'bestellung', COUNT(*) FROM bestellung UNION ALL SELECT 'bestellposition', COUNT(*) FROM bestellposition;"

docker exec onlineshop-mongodb mongosh onlineshop --quiet --eval 'db.getCollectionNames().forEach(c => print(c + ": " + db.getCollection(c).countDocuments({})))'
```

| Objekt | MySQL | MongoDB |
| --- | ---: | ---: |
| Kategorien | 10 | In Produkten eingebettet |
| Produkte | 500 | 500 |
| Kunden | 50.000 | 50.000 |
| Kundenprofile | 50.000 | In Kunden eingebettet |
| Bestellungen | 50.000 | 50.000 |
| Bestellpositionen | 149.623 | In Bestellungen eingebettet |

Der Benchmark verwendet Kunde 25000. Dieser Kunde hat im gelieferten Seed zwei Bestellungen:

```bash
docker exec onlineshop-mysql mysql -uroot -proot onlineshop -e "SELECT COUNT(*) FROM bestellung WHERE kundeID = 25000;"
docker exec onlineshop-mongodb mongosh onlineshop --quiet --eval 'print(db.bestellungen.countDocuments({kunde_id: 25000}))'
```

## 5. Benchmark und Auswertung

In der aktivierten Python-Umgebung:

```bash
bash run_benchmark.sh
```

Der ursprüngliche Lauf benötigte ungefähr 16-20 Minuten; die Dauer hängt von der Umgebung ab. Das Script startet beide Container vor jeder Messung neu, setzt den Indexzustand und misst eine Lese- oder Update-Operation. Andere Last auf dem Rechner kann die Zeiten beeinflussen.

Neue Ergebnisse werden in `/tmp/bench_results.csv` geschrieben. Eine erneute Zusammenfassung und das Sichern des Laufs sind möglich mit:

```bash
python3 summarize.py
cp /tmp/bench_results.csv bench_results.csv
```

Die lokale Kopie `bench_results.csv` ist ignoriert. Die ursprünglichen Referenzmessungen bleiben in `results/bench_results.csv`. Vor einer weiteren unabhängigen Messreihe beide Datenbanken erneut importieren, damit Status, Fremdschlüssel und Indizes wieder dem Ausgangsbestand entsprechen.

## 6. Beenden

```bash
docker compose down
```

Die Daten bleiben in den benannten Volumes erhalten. **`docker compose down -v` löscht auch diese Volumes und damit alle Testdaten.**
