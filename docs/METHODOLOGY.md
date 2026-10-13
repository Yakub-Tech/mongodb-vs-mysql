# Messmethodik und Grenzen

## Fragestellung

Wie verändert ein sekundärer Index auf der Kundenreferenz die vom Python-Treiber beobachtete Dauer von Lese- und Update-Operationen in zwei unterschiedlich modellierten Online-Shop-Datenbanken?

Der Vergleich umfasst zwei Datenbanken, zwei Operationen und zwei Indexzustände: acht Szenarien mit jeweils zehn Messungen. Die Abfrage verwendet immer Kunde 25000, der im Seed zwei Bestellungen hat.

| Operation | MySQL | MongoDB |
| --- | --- | --- |
| Lesen | `SELECT * FROM bestellung WHERE kundeID = 25000` mit vollständigem Abruf | `find({kunde_id: 25000})` mit vollständigem Abruf |
| Update | Alle passenden Bestellungen auf `status = 'bearbeitet'` setzen | `update_many` mit demselben Filter und Status |
| Sekundärer Index | `bestellung(kundeID)` | `bestellungen(kunde_id)` |

Primärschlüssel beziehungsweise `_id`-Indizes bleiben bestehen. Im MySQL-Fall ohne Index entfernt das Script den Fremdschlüssel auf `bestellung.kundeID`, weil dessen unterstützender Index sonst nicht gelöscht werden kann. Verglichen wird der Index auf diesem Suchfeld, keine vollständig indexfreie Datenbank.

## Ablauf einer Messung

1. Beide Container werden entfernt und wieder gestartet; die Daten bleiben in persistenten Volumes erhalten.
2. Das Shellscript wartet auf die Bereitschaft der Dienste.
3. Python verbindet sich und stellt den gewünschten Indexzustand her.
4. `time.perf_counter()` misst die Operation einschließlich Ergebnisabruf beim Lesen beziehungsweise der Rückkehr des Treiberaufrufs beim Update.
5. Eine CSV-Zeile hält Datenbank, Operation, Indexzustand, Messnummer und Dauer in Millisekunden fest.

Verbindungsaufbau, Container-Neustart und Indexverwaltung liegen außerhalb des expliziten Zeitfensters. Bei MongoDB können verzögerte Verbindungsarbeiten des Treibers trotzdem in den gemessenen Aufruf hineinreichen.

## Vollständige Referenzstatistik

Berechnet aus [den vorhandenen CSV-Rohdaten](../results/bench_results.csv). Standardabweichung als Stichproben-Standardabweichung mit `n - 1`, jeweils `n = 10`; alle Zeiten in Millisekunden.

Die MySQL-Werte wurden mit Oracle MySQL Connector/Python erhoben. Für die aktuelle Version wurde ausschließlich der MySQL-Treiber gegen PyMySQL ausgetauscht, damit die eigene eingeschränkte Projektlizenz nicht auf Oracles FOSS-Ausnahme angewiesen ist. Die Abfragen und historischen Daten bleiben erhalten. Der neue Treiber wurde auf Wunsch des Autors nicht mit einer laufenden Datenbank geprüft; es gibt keine neue Messreihe für diese Version.

| Datenbank | Operation | Index | Mittelwert | Std.abw. | Min | Max |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| MySQL | Lesen | Ohne | 20,9825 | 5,6494 | 15,9760 | 34,2520 |
| MySQL | Lesen | Mit | 7,3914 | 5,3369 | 0,5017 | 16,5440 |
| MongoDB | Lesen | Ohne | 52,6304 | 10,9427 | 36,5466 | 68,9666 |
| MongoDB | Lesen | Mit | 24,4259 | 8,1420 | 2,0263 | 30,0733 |
| MySQL | Update | Ohne | 36,6458 | 10,1770 | 25,4338 | 60,8735 |
| MySQL | Update | Mit | 7,3987 | 5,8222 | 0,5165 | 18,5979 |
| MongoDB | Update | Ohne | 59,3890 | 11,3783 | 41,0082 | 73,1894 |
| MongoDB | Update | Mit | 16,1565 | 5,5890 | 1,7847 | 22,4627 |

## Grenzen der Interpretation

- **Neustart bedeutet keinen kontrollierten kalten Cache.** Der Host beziehungsweise die Docker-VM behalten möglicherweise Dateisystem-Caches. Datenbankinterne Wiederherstellung und das Anlegen eines Index können Daten vor der Messung lesen. Der Aufbau erzwingt keine identischen Cache-Zustände.
- **Updates haben keinen konstanten Ausgangszustand.** Der Status wird zwischen Wiederholungen nicht zurückgesetzt. Nach dem ersten Update steht er bereits auf `bearbeitet`; spätere Updates können andere Arbeit verursachen. Auch zwischen den Indexszenarien bleiben diese Änderungen erhalten. Die Update-Werte sind daher besonders vorsichtig zu interpretieren.
- **Die zurückgegebenen Datensätze unterscheiden sich.** MySQL liest Bestellköpfe; MongoDB liefert Bestelldokumente einschließlich eingebetteter Positionen. Ergebnisumfang und Übertragungsmenge sind nicht identisch.
- **Treiber und Schreibbestätigungen unterscheiden sich.** MySQL nutzt Autocommit, MongoDB die Treiber- und Servervorgaben. Identische Persistenzgarantien wurden nicht eigens eingestellt oder nachgewiesen.
- **Zehn Messungen und feste Szenarioreihenfolge begrenzen die Aussage.** Es gibt keine Randomisierung, Lasttests, parallelen Nutzer oder kontrollierten Warmbetrieb. Besonders beim Lesen mit Index ist die Streuung sichtbar.
- **Die historische Umgebung ist nicht vollständig dokumentiert.** Die Werte stammen aus einem lokalen Docker-Lauf. Exakte damalige Treiberversionen, Image-Digests und Ressourcenlimits wurden nicht in der CSV aufgezeichnet. Die heutige `requirements.txt` legt Treiberversionen für neue Läufe fest, belegt aber nicht die damaligen Versionen. Die Image-Tags `mysql:8.0` und `mongo:7.0` fixieren keine Patch-Version.

Die belastbare Beobachtung für diesen begrenzten Aufbau: Mit Index fallen die gemessenen mittleren Laufzeiten in allen vier Kombinationen geringer aus. Die Rohdaten erlauben keine allgemeine Aussage, welche Datenbank für einen produktiven Online-Shop schneller oder besser geeignet ist.

## Umfang des Repositorys

Die ursprüngliche Kursausarbeitung und Vorführungsunterlagen enthielten auch eine ältere, anders erhobene Messreihe. Deren vollständige automatisierte Messskripte und Rohdaten liegen in dieser Auswahl nicht vor. Dieses Repository dokumentiert deshalb ausschließlich den enthaltenen Acht-Szenarien-Benchmark und dessen 80 nachvollziehbare CSV-Werte.
