-- Default migration — always part of the repo, ships with every clone.
-- Applied via backend/scripts/init_db.js (Phase 5) against a fresh local MySQL database.

CREATE TABLE person_events (
  id INT AUTO_INCREMENT PRIMARY KEY,
  person_name VARCHAR(50),        -- 'unknown' if stranger
  is_known BOOLEAN,
  confidence FLOAT,
  event_type ENUM('entry','exit','detected'),
  snapshot_path VARCHAR(255),
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
