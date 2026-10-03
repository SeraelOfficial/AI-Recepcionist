#!/usr/bin/env python3
import getpass
import json
import sys
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

if len(sys.argv) != 2:
    sys.exit("Usage: python3 scripts/check_api.py https://citas.your-domain.com")
base = sys.argv[1].rstrip("/")
p = urlsplit(base)
if p.scheme != "https" or not p.hostname or p.username or p.password or p.query or p.fragment or p.path:
    sys.exit("Use an HTTPS origin without path or credentials.")
token = getpass.getpass("API token (hidden): ").strip()
if not token:
    sys.exit("Token required.")
opener = build_opener(NoRedirect())
for resource in ("services", "providers"):
    request = Request(base + "/index.php/api/v1/" + resource,
                      headers={"Authorization": "Bearer " + token, "Accept": "application/json"})
    try:
        with opener.open(request, timeout=20) as response:
            data = json.load(response)
        if not isinstance(data, list):
            sys.exit(resource + ": unexpected API response")
        print(resource + ": OK, records=" + str(len(data)))
    except HTTPError as exc:
        sys.exit(resource + ": HTTP " + str(exc.code) + " (check setup, token and proxy)")
    except (URLError, ValueError):
        sys.exit(resource + ": connection or JSON error")
print("Read-only API check passed. Booking lifecycle test still required.")
