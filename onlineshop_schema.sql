-- =====================================================================
-- Schema fuer Online-Shop (MySQL)
-- Passt zu onlineshop_mysql_testdaten.sql
-- =====================================================================

USE onlineshop;

-- Falls schon vorhanden: alles sauber loeschen (FK-Reihenfolge beachten)
DROP TABLE IF EXISTS bestellposition;
DROP TABLE IF EXISTS bestellung;
DROP TABLE IF EXISTS kundenprofil;
DROP TABLE IF EXISTS kunde;
DROP TABLE IF EXISTS produkt;
DROP TABLE IF EXISTS kategorie;

-- ---------------------------------------------------------------------
-- kategorie
-- ---------------------------------------------------------------------
CREATE TABLE kategorie (
    kategorieID   INT           NOT NULL,
    name          VARCHAR(100)  NOT NULL,
    beschreibung  TEXT,
    PRIMARY KEY (kategorieID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- produkt
-- ---------------------------------------------------------------------
CREATE TABLE produkt (
    produktID     INT            NOT NULL,
    kategorieID   INT            NOT NULL,
    name          VARCHAR(200)   NOT NULL,
    beschreibung  TEXT,
    preis         DECIMAL(10,2)  NOT NULL,
    lagerbestand  INT            NOT NULL,
    PRIMARY KEY (produktID),
    CONSTRAINT fk_produkt_kategorie
        FOREIGN KEY (kategorieID) REFERENCES kategorie(kategorieID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- kunde
-- ---------------------------------------------------------------------
CREATE TABLE kunde (
    kundeID    INT           NOT NULL,
    vorname    VARCHAR(100)  NOT NULL,
    nachname   VARCHAR(100)  NOT NULL,
    email      VARCHAR(200)  NOT NULL,
    strasse    VARCHAR(200),
    plz        VARCHAR(20),
    stadt      VARCHAR(100),
    PRIMARY KEY (kundeID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- kundenprofil (1:1 zu kunde)
-- ---------------------------------------------------------------------
CREATE TABLE kundenprofil (
    profilID      INT           NOT NULL,
    kundeID       INT           NOT NULL,
    telefon       VARCHAR(50),
    geburtsdatum  DATE,
    newsletter    TINYINT(1)    NOT NULL DEFAULT 0,
    PRIMARY KEY (profilID),
    CONSTRAINT fk_profil_kunde
        FOREIGN KEY (kundeID) REFERENCES kunde(kundeID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- bestellung
-- ---------------------------------------------------------------------
CREATE TABLE bestellung (
    bestellungID  INT           NOT NULL,
    kundeID       INT           NOT NULL,
    bestelldatum  DATE          NOT NULL,
    status        VARCHAR(50)   NOT NULL,
    PRIMARY KEY (bestellungID),
    CONSTRAINT fk_bestellung_kunde
        FOREIGN KEY (kundeID) REFERENCES kunde(kundeID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- bestellposition
-- ---------------------------------------------------------------------
CREATE TABLE bestellposition (
    positionID    INT            NOT NULL,
    bestellungID  INT            NOT NULL,
    produktID     INT            NOT NULL,
    menge         INT            NOT NULL,
    einzelpreis   DECIMAL(10,2)  NOT NULL,
    PRIMARY KEY (positionID),
    CONSTRAINT fk_position_bestellung
        FOREIGN KEY (bestellungID) REFERENCES bestellung(bestellungID),
    CONSTRAINT fk_position_produkt
        FOREIGN KEY (produktID) REFERENCES produkt(produktID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;