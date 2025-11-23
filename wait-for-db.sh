#!/bin/sh
# Script to wait for PostgreSQL database to be ready

set -e

host="$1"
shift
cmd="$@"

# Check that environment variables are set
if [ -z "$POSTGRES_DB" ] || [ -z "$POSTGRES_USER" ] || [ -z "$POSTGRES_PASSWORD" ]; then
  >&2 echo "Error: POSTGRES_DB, POSTGRES_USER, or POSTGRES_PASSWORD not set"
  exit 1
fi

>&2 echo "Waiting for PostgreSQL to be ready..."
>&2 echo "Host: $host, Database: $POSTGRES_DB, User: $POSTGRES_USER"

until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$host" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q' 2>/dev/null; do
  >&2 echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

>&2 echo "PostgreSQL is up - executing command"
exec $cmd

