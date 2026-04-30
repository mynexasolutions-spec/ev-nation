#!/bin/bash

# Setup systemd service
cat << 'EOF' | sudo tee /etc/systemd/system/ev-nation.service
[Unit]
Description=EV Nation FastAPI Application
After=network.target

[Service]
User=ec2-user
Group=ec2-user
WorkingDirectory=/home/ec2-user/ev-nation
Environment="PATH=/home/ec2-user/ev-nation/venv/bin"
EnvironmentFile=/home/ec2-user/ev-nation/.env
ExecStart=/home/ec2-user/ev-nation/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8002 --proxy-headers --forwarded-allow-ips='*'
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable ev-nation
sudo systemctl start ev-nation

# Setup Nginx
sudo cp /home/ec2-user/ev-nation/evnationsre.conf /etc/nginx/conf.d/
sudo systemctl enable nginx
sudo systemctl restart nginx
