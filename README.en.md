# MySQL vs. MongoDB: data modelling and index benchmark

[Deutsch](README.md) · [Setup](docs/SETUP.en.md) · [Methodology](docs/METHODOLOGY.en.md) · [License](LICENSE)

A practical project from a university NoSQL course: the same online shop represented as a relational MySQL schema and a MongoDB document model. A Python benchmark investigates how an index on the customer reference affects read and update operations.

**Technologies:** Python · SQL · MongoDB · JavaScript · Bash · Docker Compose

Developed entirely by **Yakub Uyar** during his sixth semester. This is a learning and comparison project, not a shop application used in production. It has no frontend.

## What the project demonstrates

- Modelling one-to-one, one-to-many and many-to-many relationships using foreign keys, embedded documents and references.
- Comparing queries with and without a secondary index using the same dataset and a fixed customer ID.
- Automating eight scenarios with ten measurements each and calculating the mean, sample standard deviation, minimum and maximum.
- Interpreting the results within the limitations of the experiment.

## Data model

| Business object | MySQL | MongoDB |
| --- | --- | --- |
| Customer and profile | `kunde` and `kundenprofil`, connected by a foreign key | `kunden` with an embedded `profil` |
| Product and category | `produkt` and `kategorie` | `produkte` with an embedded `kategorie` |
| Order and line items | `bestellung` and `bestellposition` | `bestellungen` with a `positionen` array |
| Customer of an order | `bestellung.kundeID` with a foreign key in the initial schema | Reference `bestellungen.kunde_id` |
| Product of a line item | `bestellposition.produktID` with a foreign key | Reference `positionen.produkt_id` |

The supplied, generated dataset contains **50,000 customers, 50,000 orders, 500 products, 10 categories and 149,623 line items**. MySQL represents it in six tables; MongoDB uses three collections containing 100,500 documents. Customer records are test data only.

## Examples

Two real terminal captures extracted from the author's April 2026 course presentation. They show the original run with generated test data. The historical label “kalte Messungen” in the first image refers only to measurements after container restarts; fully empty caches were not established. These are not captures of a new verification run.

### Measurement run

The shell script restarts the databases before each measurement and logs the scenario and measured duration.

![Historical German terminal output showing the beginning and first measurements of the benchmark](assets/screenshots/benchmark-lauf.png)

### Summary

Mean, sample standard deviation, minimum and maximum for all eight scenarios.

![Historical German terminal output showing the complete benchmark statistics](assets/screenshots/benchmark-ergebnisse.png)

## Existing results

Calculated from the [80 original measurements](results/bench_results.csv). All times are in milliseconds. These values come from the original project run and were not measured again for this release.

The original MySQL run used Oracle's MySQL Connector/Python. The current code uses PyMySQL for licensing reasons. New MySQL measurements therefore use a different driver and cannot be compared directly with this historical series.

| Database | Operation | Without index, mean | With index, mean |
| --- | --- | ---: | ---: |
| MySQL | Read | 20.98 | 7.39 |
| MongoDB | Read | 52.63 | 24.43 |
| MySQL | Update | 36.65 | 7.40 |
| MongoDB | Update | 59.39 | 16.16 |

In this series, an index reduces the measured duration for both databases. This does not establish a general ranking: the data model, workload, drivers and experiment setup affect the results. The [methodology and complete statistics](docs/METHODOLOGY.en.md) explain the limitations.

## Run locally

Requirements: Docker with Compose, Python 3.9 or later and Node.js; the shell script requires Bash, for example on macOS, Linux or WSL. Run all commands from the project directory.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
docker compose up -d
```

Import and check the databases as described in [docs/SETUP.en.md](docs/SETUP.en.md). Only then run:

```bash
bash run_benchmark.sh
```

The script performs 80 container restarts and prints a statistical summary. New measurements are written to `/tmp/bench_results.csv`; another run replaces that file. The reference measurements in `results/` remain unchanged.

**Use only the supplied local test database:** the benchmark changes order status, indexes and, in the MySQL scenario without an index, the foreign key on `bestellung.kundeID`. Updates are not reset between measurements. Database ports are bound to `127.0.0.1`; the fixed MySQL password `root` and MongoDB without authentication are intended only for this local test environment.

## Static checks and limitations

There is no application build or graphical interface. Automated GitHub checks validate syntax and local documentation links without starting databases:

```bash
python3 -m py_compile benchmark.py summarize.py
bash -n run_benchmark.sh
node --check convert_seed.js
```

For this release, the dataset, existing statistics and file consistency were checked. At the author's request, no new Docker or functional test was performed. A successful static check does not prove correct database execution. This is a limited experiment; known limitations are documented in the [methodology](docs/METHODOLOGY.en.md).

The switch to PyMySQL was also not tested against a running database. The package is installed with the RSA extra, which may be required for MySQL 8 password authentication.

## Files

| File | Purpose |
| --- | --- |
| `docker-compose.yml` | MySQL 8.0 and MongoDB 7.0 with persistent volumes |
| `onlineshop_schema.sql` | Tables, data types and foreign keys |
| `onlineshop_mysql_testdaten.sql` | Generated relational test data |
| `mongodb_testdaten_onlineshop.js` | Generated MongoDB documents |
| `convert_seed.js` | Converts the MongoDB seed into JSONL for import |
| `benchmark.py` | Measures one operation for a scenario |
| `run_benchmark.sh` | Restarts, readiness checks and measurement runs |
| `summarize.py` | Summarises new measurements from `/tmp/bench_results.csv` |
| `requirements.txt` | Fixed Python driver versions for new runs |
| `docs/` | Setup and interpretation |
| `results/bench_results.csv` | Unchanged raw data from the original series |

JSONL exports are generated locally and are not versioned again. Complete seed files are included to preserve the dataset. Personal course documents, drafts and presentation notes are excluded from this public selection.

## History

Git history preserves the genuine first GitHub upload from **13 April 2026**, including its original ZIP contents and timestamps. The private author email was replaced with the GitHub noreply address; this changed the commit ID and required removing the old GitHub signature. The ZIP now belongs only to the historical revision. Earlier development without Git was not reconstructed using invented commits.

## License and responsibility

Copyright © 2026 **Yakub Uyar**. Original code and content are published under [custom German and English terms](LICENSE). Viewing, downloading, personal use, modification and free distribution while retaining the terms are permitted. Associations and businesses may use the project for their own work and to support their own economic activities.

Selling the software or derived versions and offering paid software services require express permission. These terms are **not an open-source license** in the usual sense. Third-party rights and obligations remain in effect; see [third-party notices](THIRD_PARTY.md).

Use at your own risk, as is, without any commitment to maintenance, support or warranty, to the extent permitted by law. Before real use, operators must review suitability, functionality, security, data protection and applicable requirements. They are responsible for setup, operation, access control, backups and restoration. Mandatory liability remains unaffected. The full terms in [LICENSE](LICENSE) apply.
