#!/bin/bash

echo "=========================================="
echo "       Docker Environment Reset Tool      "
echo "=========================================="
echo "WARNING: This will stop all containers and DELETE all volumes (database data will be lost)."
echo "Project context: /workspaces/port-rally"
echo ""
read -p "Are you sure you want to proceed? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Operation cancelled."
    exit 1
fi

echo ""
echo "[1] Shutting down services and removing volumes..."
# Uses the project root docker-compose files implicitly by being run from project context or explicit path
# We assume the user might run this from anywhere, so let's try to locate the compose file or run in root
if [ -f "docker-compose.yml" ]; then
    docker compose down --volumes --remove-orphans
elif [ -f "../../docker-compose.yml" ]; then
    # In case running from inside stash/manage
    docker compose -f ../../docker-compose.yml down --volumes --remove-orphans
else
    echo "Could not find docker-compose.yml. Running generic container cleanup..."
    # Fallback: simple down
    docker compose down --volumes --remove-orphans
fi

echo ""
echo "[2] Pruning unused Docker system objects..."
docker system prune -f

echo ""
echo "=========================================="
echo "Cleanup complete."
echo "To restart services, run: ./run-local.sh"
echo "If you still see 'file exists' errors, try: sudo systemctl restart docker"
