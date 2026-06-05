#!/bin/bash
set -e
sudo cp camera-stream.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable camera-stream
sudo systemctl start camera-stream
echo ""
echo "Done! Camera stream will now auto-start on every boot."
echo "Check status: sudo systemctl status camera-stream"
