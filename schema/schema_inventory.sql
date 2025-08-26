DROP TABLE IF EXISTS inventory;

CREATE TABLE inventory (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  item TEXT NOT NULL,
  color TEXT NOT NULL,
  grade TEXT NOT NULL,
  batch_no TEXT NOT NULL,
  sqm REAL NOT NULL,
  remark TEXT
);

-- Sample data matching the new structure
INSERT INTO inventory (item, color, grade, batch_no, sqm, remark) VALUES
('AR-1101', 'Bright Silver', 'BS', 'LJ-2422', 2852, 'Reserved for Project A'),
('AR-1101', 'Bright Silver', 'BS', 'LJ-2423', 2612, 'idk'),
('AR-1102', 'Silver', 'GL', 'ETA203A', 206, 'Check for defects');
