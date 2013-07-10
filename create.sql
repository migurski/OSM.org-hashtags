DROP TABLE IF EXISTS changesets;

CREATE TABLE changesets
(
    id      INTEGER PRIMARY KEY,
    created INTEGER,

    uid     INTEGER,
    user    TEXT,

    comment TEXT,
    
    minlat  REAL,
    minlon  REAL,
    maxlat  REAL,
    maxlon  REAL
);
