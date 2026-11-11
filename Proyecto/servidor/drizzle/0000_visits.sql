CREATE TABLE visits (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  count INTEGER NOT NULL DEFAULT 0 CHECK (count >= 0)
);
--> statement-breakpoint
INSERT INTO visits (id) VALUES (1);
