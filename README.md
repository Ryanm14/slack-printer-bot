## Setup
```bash
pip3 install -r requirements
python3 dx_printer_service.py
```

---

## Autorun for Ubuntu

Note: May need to install requirements into root or user, or use [.venv](https://www.shubhamdipt.com/blog/how-to-create-a-systemd-service-in-linux/)

```bash
cd /etc/systemd/system
sudo vim dx-slack-printer.service
```
```txt
[Unit]
Description=DX Slack Printer

[Service]
User=<user e.g. root>
WorkingDirectory=<directory_of_script e.g. /root>
ExecStart=python3 dx_printer_service.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl start dx-slack-printer.service
sudo systemctl enable dx-slack-printer.service

```

Helpers:
```bash
sudo systemctl status dx-slack-printer.service
sudo systemctl disable dx-slack-printer.service
```