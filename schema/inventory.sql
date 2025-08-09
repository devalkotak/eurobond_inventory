DROP TABLE IF EXISTS inventory;

CREATE TABLE inventory (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  color_code INTEGER NOT NULL,
  grade TEXT NOT NULL,
  quantity INTEGER NOT NULL
);

-- Sample data (sr_no is no longer needed here)
INSERT INTO inventory (color_code, grade, quantity) VALUES
(401, 'A', 150),
(402, 'B', 25),
(550, 'A', 0),
(610, 'C', 88);
