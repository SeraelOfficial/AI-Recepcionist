#!/usr/bin/env python3
"""Create missing private Splendor assessment services; preserve existing records."""
import json
from pathlib import Path
from urllib.request import Request, urlopen
BASE = "http://127.0.0.1:8095/index.php/api/v1/"
ROOT = Path(__file__).resolve().parent.parent
TOKEN = json.loads((ROOT / ".bootstrap.json").read_text())["api_token"]
catalog = json.loads((ROOT / "data/splendor-services.json").read_text())
def api(method, path, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    request = Request(BASE + path, data=data, method=method,
        headers={"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"})
    with urlopen(request, timeout=30) as response:
        body = response.read()
        return json.loads(body) if body else None
def listing(resource):
    results = []
    page = 1
    while True:
        batch = api("GET", resource + "?length=100&page=" + str(page))
        assert isinstance(batch, list), "Unexpected list response"
        results.extend(batch)
        if len(batch) < 100:
            return results
        page += 1
categories = {item["name"]: item for item in listing("service_categories")}
services = {item["name"]: item for item in listing("services")}
created = 0
for entry in catalog["services"]:
    category = entry["category"]
    if category not in categories:
        categories[category] = api("POST", "service_categories", {
            "name": category, "description": "Splendor Centro Médico: citas de valoración."})
    name = entry["name"]
    if name in services:
        continue
    services[name] = api("POST", "services", {
        "name": name, "duration": catalog["consultation_duration_minutes"],
        "price": 0, "currency": "CRC", "slotInterval": 30,
        "attendantsNumber": 1, "isPrivate": True,
        "serviceCategoryId": categories[category]["id"],
        "description": "Consulta de valoración para " + entry["procedure"] +
            ". Tarifa y duración por confirmar con la clínica. No incluye la realización del procedimiento. Fuente: " + entry["source"]
    })
    created += 1
verified = {item["name"]: item for item in listing("services")}
for entry in catalog["services"]:
    item = verified[entry["name"]]
    assert item["serviceCategoryId"] == categories[entry["category"]]["id"]
print(json.dumps({"created": created, "verified": len(catalog["services"]),
    "private": sum(bool(verified[e["name"]]["isPrivate"]) for e in catalog["services"]),
    "categories": len(set(e["category"] for e in catalog["services"])),
    "duration_minutes_provisional": 30, "tariffs_confirmed": False}))
