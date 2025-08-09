DROP TABLE IF EXISTS users;

CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  role TEXT NOT NULL CHECK(role IN ('director', 'admin', 'viewer')),
  status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'suspended'))
);