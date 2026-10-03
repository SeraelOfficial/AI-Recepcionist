#!/usr/bin/env python3
import os
import secrets
import sys
from pathlib import Path
from urllib.parse import urlsplit

root = Path(__file__).resolve().parents[1]
if len(sys.argv) != 2:
    sys.exit("Usage: python3 scripts/init_env.py https://citas.your-domain.com")
url = sys.argv[1].rstrip("/")
p = urlsplit(url)
if p.scheme != "https" or not p.hostname or p.username or p.password or p.query or p.fragment or p.path or any(c.isspace() for c in url):
    sys.exit("Use a plain HTTPS origin without path or credentials.")
content = (root / ".env.example").read_text()
content = content.replace("https://citas.example.com", url)
content = content.replace("DB_PASSWORD=\n", "DB_PASSWORD=" + secrets.token_hex(32) + "\n")
content = content.replace("MYSQL_ROOT_PASSWORD=\n", "MYSQL_ROOT_PASSWORD=" + secrets.token_hex(32) + "\n")
try:
    fd = os.open(root / ".env", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
except FileExistsError:
    sys.exit(".env already exists; preserved without changes.")
with os.fdopen(fd, "w") as f:
    f.write(content)
print(".env created with permissions 600. Configure SMTP locally.")
