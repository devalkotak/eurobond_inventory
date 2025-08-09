#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Create the databases if they don't exist
if [ ! -f instance/inventory.db ]; then
  echo "Creating inventory database..."
  python -c "from app import init_db; init_db('instance/inventory.db', 'schema/schema_inventory.sql')"
fi

if [ ! -f instance/users.db ]; then
  echo "Creating users database..."
  python -c "from app import init_db; init_db('instance/users.db', 'schema/schema_users.sql')"
fi

if [ ! -f instance/log.db ]; then
  echo "Creating log database..."
  python -c "from app import init_db; init_db('instance/log.db', 'schema/schema_log.sql')"
fi