ALTER TABLE visit_locations RENAME TO visit_locations_before_reset;
--> statement-breakpoint
CREATE TABLE visit_locations (
  country TEXT NOT NULL,
  region TEXT NOT NULL,
  count INTEGER NOT NULL CHECK (count > 0),
  PRIMARY KEY (country, region)
);
--> statement-breakpoint
UPDATE visits SET count = 10 WHERE id = 1;
