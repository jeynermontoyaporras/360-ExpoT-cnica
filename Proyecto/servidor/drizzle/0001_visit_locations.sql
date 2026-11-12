CREATE TABLE visit_locations (
  country TEXT NOT NULL,
  region TEXT NOT NULL,
  count INTEGER NOT NULL CHECK (count > 0),
  PRIMARY KEY (country, region)
);
