# Setup and data import

All commands use Bash on macOS, Linux or WSL and run from the project directory. Python 3.9 or later and Node.js are required. Docker must be running; ports 3306 and 27017 must be available. The fixed container names `onlineshop-mysql` and `onlineshop-mongodb` must not belong to another environment.

## 1. Python environment and containers

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
docker compose up -d
docker compose ps
```

Before importing data, check that both databases accept requests. If a command fails, wait briefly and repeat it:

```bash
docker exec onlineshop-mysql mysql -uroot -proot onlineshop -e "SELECT 1;"
docker exec onlineshop-mongodb mongosh --quiet --eval 'db.adminCommand("ping")'
```

## 2. Import MySQL data

**Warning:** the schema removes existing shop tables and their data. Import only into the intended test environment. For another import, always load the schema first.

```bash
docker exec -i onlineshop-mysql mysql -uroot -proot onlineshop < onlineshop_schema.sql
docker exec -i onlineshop-mysql mysql -uroot -proot onlineshop < onlineshop_mysql_testdaten.sql
```

The password `root` is a local test password. MySQL's warning about passing a password on the command line is expected in this setup.

## 3. Import MongoDB data

The converter creates three JSONL files from the seed's `insertMany` blocks. They are imported using `mongoimport`, so the large seed file does not need to be executed directly in `mongosh`.

```bash
node convert_seed.js

docker cp produkte.jsonl onlineshop-mongodb:/tmp/produkte.jsonl
docker cp kunden.jsonl onlineshop-mongodb:/tmp/kunden.jsonl
docker cp bestellungen.jsonl onlineshop-mongodb:/tmp/bestellungen.jsonl

docker exec onlineshop-mongodb mongoimport --db onlineshop --collection produkte --file /tmp/produkte.jsonl --drop
docker exec onlineshop-mongodb mongoimport --db onlineshop --collection kunden --file /tmp/kunden.jsonl --drop
docker exec onlineshop-mongodb mongoimport --db onlineshop --collection bestellungen --file /tmp/bestellungen.jsonl --drop
```

**Warning:** `--drop` removes the existing collection, including indexes and data. This permits another import without duplicate IDs. Generated JSONL files are excluded by `.gitignore`.

Expected converter output: 151 blocks and 100,500 documents.

## 4. Check the dataset

```bash
docker exec onlineshop-mysql mysql -uroot -proot onlineshop -e "SELECT 'kategorie' AS objekt, COUNT(*) AS anzahl FROM kategorie UNION ALL SELECT 'produkt', COUNT(*) FROM produkt UNION ALL SELECT 'kunde', COUNT(*) FROM kunde UNION ALL SELECT 'kundenprofil', COUNT(*) FROM kundenprofil UNION ALL SELECT 'bestellung', COUNT(*) FROM bestellung UNION ALL SELECT 'bestellposition', COUNT(*) FROM bestellposition;"

docker exec onlineshop-mongodb mongosh onlineshop --quiet --eval 'db.getCollectionNames().forEach(c => print(c + ": " + db.getCollection(c).countDocuments({})))'
```

| Object | MySQL | MongoDB |
| --- | ---: | ---: |
| Categories | 10 | Embedded in products |
| Products | 500 | 500 |
| Customers | 50,000 | 50,000 |
| Customer profiles | 50,000 | Embedded in customers |
| Orders | 50,000 | 50,000 |
| Line items | 149,623 | Embedded in orders |

The benchmark uses customer 25000, who has two orders in the supplied seed:

```bash
docker exec onlineshop-mysql mysql -uroot -proot onlineshop -e "SELECT COUNT(*) FROM bestellung WHERE kundeID = 25000;"
docker exec onlineshop-mongodb mongosh onlineshop --quiet --eval 'print(db.bestellungen.countDocuments({kunde_id: 25000}))'
```

## 5. Benchmark and summary

With the Python environment activated:

```bash
bash run_benchmark.sh
```

The original run took approximately 16-20 minutes; duration depends on the environment. The script restarts both containers before each measurement, sets the index state and measures one read or update operation. Other workloads on the computer may affect the results.

New results are written to `/tmp/bench_results.csv`. To print the summary again and save the run:

```bash
python3 summarize.py
cp /tmp/bench_results.csv bench_results.csv
```

The local copy `bench_results.csv` is ignored. Original reference measurements remain in `results/bench_results.csv`. Before another independent series, reimport both databases to restore order status, foreign keys and indexes to their initial state.

## 6. Stop

```bash
docker compose down
```

Data is preserved in named volumes. **`docker compose down -v` also deletes those volumes and all test data.**
