# Methodology and limitations

## Research question

How does a secondary index on the customer reference affect the duration of read and update operations observed by a Python driver in two differently modelled online-shop databases?

The experiment covers two databases, two operations and two index states: eight scenarios with ten measurements each. Every query uses customer 25000, who has two orders in the seed.

| Operation | MySQL | MongoDB |
| --- | --- | --- |
| Read | `SELECT * FROM bestellung WHERE kundeID = 25000`, fetching all results | `find({kunde_id: 25000})`, fetching all results |
| Update | Set all matching orders to `status = 'bearbeitet'` | `update_many` with the same filter and status |
| Secondary index | `bestellung(kundeID)` | `bestellungen(kunde_id)` |

Primary-key and `_id` indexes remain in place. In the MySQL scenario without the index, the script removes the foreign key on `bestellung.kundeID`, because its supporting index could otherwise not be dropped. The comparison concerns an index on this search field, not databases without any indexes.

## One measurement

1. Both containers are removed and started again; data is preserved in persistent volumes.
2. The shell script waits for the services to become available.
3. Python connects and establishes the requested index state.
4. `time.perf_counter()` measures the operation, including fetching read results or returning from the driver's update call.
5. A CSV row records the database, operation, index state, measurement number and duration in milliseconds.

Connection setup, container restarts and index management are outside the explicit timing window. MongoDB's deferred driver connection work may still enter the measured call.

## Complete reference statistics

Calculated from [the existing CSV data](../results/bench_results.csv). Standard deviation is the sample standard deviation with `n - 1`, using `n = 10` for each scenario. All times are in milliseconds.

The MySQL values were collected using Oracle MySQL Connector/Python. For the current version, only the MySQL driver was replaced with PyMySQL so the restricted custom license does not rely on Oracle's FOSS exception. Queries and historical data are preserved. At the author's request, the new driver was not checked against a running database; no new series exists for this version.

| Database | Operation | Index | Mean | Std. dev. | Min | Max |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| MySQL | Read | Without | 20.9825 | 5.6494 | 15.9760 | 34.2520 |
| MySQL | Read | With | 7.3914 | 5.3369 | 0.5017 | 16.5440 |
| MongoDB | Read | Without | 52.6304 | 10.9427 | 36.5466 | 68.9666 |
| MongoDB | Read | With | 24.4259 | 8.1420 | 2.0263 | 30.0733 |
| MySQL | Update | Without | 36.6458 | 10.1770 | 25.4338 | 60.8735 |
| MySQL | Update | With | 7.3987 | 5.8222 | 0.5165 | 18.5979 |
| MongoDB | Update | Without | 59.3890 | 11.3783 | 41.0082 | 73.1894 |
| MongoDB | Update | With | 16.1565 | 5.5890 | 1.7847 | 22.4627 |

## Interpretation limits

- **Restarting does not establish a controlled cold cache.** The host or Docker VM may retain filesystem caches. Database recovery and index creation may read data before timing begins. The setup does not enforce identical cache states.
- **Updates do not have a constant initial state.** Status is not reset between repetitions. After the first update, it is already `bearbeitet`; later updates may do different work. Changes also persist between index scenarios. Update measurements therefore require particular caution.
- **Returned records differ.** MySQL reads order headers; MongoDB returns order documents including embedded line items. Result sizes and transferred data are not identical.
- **Drivers and write acknowledgements differ.** MySQL uses autocommit; MongoDB uses the driver and server defaults. Identical persistence guarantees were not explicitly configured or demonstrated.
- **Ten measurements and a fixed scenario order limit the conclusions.** There is no randomisation, load test, concurrent-user workload or controlled warm operation. Variation is particularly visible for indexed reads.
- **The historical environment is incompletely documented.** The values come from a local Docker run. Exact historical driver versions, image digests and resource limits were not recorded in the CSV. The current `requirements.txt` fixes driver versions for new runs, but does not establish the old versions. The image tags `mysql:8.0` and `mongo:7.0` do not fix patch versions.

The observation supported by this limited setup: the measured mean durations with an index are lower in all four combinations. These raw data do not establish which database is generally faster or more suitable for a production online shop.

## Repository scope

The original course report and presentation materials also discussed an older series collected using a different method. Its complete automated measurement scripts and raw data are not included here. This repository therefore documents only the supplied eight-scenario benchmark and its 80 traceable CSV values.
