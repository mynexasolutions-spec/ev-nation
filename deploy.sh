#!/bin/bash
# EV Nation — Deploy latest code to production
# Usage: bash deploy.sh
# Run from: d:\onedrivee\Cars 3\Desktop\EV_Nation

set -e

SERVER="ec2-user@ec2-13-232-60-185.ap-south-1.compute.amazonaws.com"
PEM="nexa-solutions.pem"
REMOTE_DIR="/home/ec2-user/ev-nation"
SERVICE="ev-nation"

echo "==> Copying updated files to server..."
scp -i "$PEM" -o StrictHostKeyChecking=no -r \
  app \
  alembic \
  alembic.ini \
  requirements.txt \
  "$SERVER:$REMOTE_DIR/"

echo "==> Restarting service..."
ssh -i "$PEM" -o StrictHostKeyChecking=no "$SERVER" \
  "sudo systemctl restart $SERVICE && sleep 3 && sudo systemctl is-active $SERVICE"

echo ""
echo "✅ Deployment complete! Site is live at http://evnationsre.com"
