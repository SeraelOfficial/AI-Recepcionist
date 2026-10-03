#!/usr/bin/env python3
"""Initialize a new local demo installation and validate API; keep credentials on server."""
import base64, datetime, http.cookiejar, json, os, secrets, sys
from pathlib import Path
from urllib.request import Request, build_opener, HTTPCookieProcessor, HTTPRedirectHandler
from urllib.parse import urlencode
from urllib.error import HTTPError

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args):
        return None

root=Path(__file__).resolve().parents[1]
creds_file=root/".bootstrap.json"
base="http://127.0.0.1:8095/index.php"
jar=http.cookiejar.CookieJar()
client=build_opener(HTTPCookieProcessor(jar),NoRedirect())
if creds_file.exists():
    creds=json.loads(creds_file.read_text())
else:
    with client.open(base+"/installation",timeout=30) as r:
        assert r.status==200
    creds={"username":"serael_admin","password":secrets.token_urlsafe(32),"api_token":secrets.token_hex(32)}
    fd=os.open(creds_file,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,"w") as f: json.dump(creds,f)
    token=next(c.value for c in jar if c.name=="csrf_cookie")
    data={"csrf_token":token,"admin[first_name]":"Serael","admin[last_name]":"Administrador",
          "admin[email]":"gabo.1985cr@gmail.com","admin[username]":creds["username"],
          "admin[password]":creds["password"],"admin[language]":"spanish",
          "company[company_name]":"Serael Recepcion Demo","company[company_email]":"gabo.1985cr@gmail.com",
          "company[company_link]":"https://citas.divinosoft.ca"}
    with client.open(Request(base+"/installation/perform",data=urlencode(data).encode()),timeout=60) as r:
        result=json.load(r)
    if not result.get("success"):
        sys.exit("Initialization did not succeed; inspect locally. Credentials preserved.")
    print("Installation initialized; credentials saved privately on server.")

auth="Basic "+base64.b64encode((creds["username"]+":"+creds["password"]).encode()).decode()
def api(path,method="GET",body=None):
    req=Request(base+"/api/v1/"+path,method=method,
                headers={"Authorization":auth,"Content-Type":"application/json","Accept":"application/json"},
                data=json.dumps(body).encode() if body is not None else None)
    try:
        with client.open(req,timeout=30) as r:
            raw=r.read()
            return json.loads(raw) if raw else None
    except HTTPError as e:
        print("API failed:",method,path,"HTTP",e.code)
        raise SystemExit(1)

# Demo initialization is private until the public domain is configured.
api("settings/api_token","PUT",{"value":creds["api_token"]})
api("settings/customer_notifications","PUT",{"value":"0"})
for admin in api("admins"):
    api("admins/"+str(admin["id"]),"PUT",{"timezone":"America/Costa_Rica","settings":{"notifications":False}})
providers=api("providers")
services=api("services")
assert len(providers)==1 and len(services)==1, "Only bootstrap demo data expected."
p=providers[0]
api("providers/"+str(p["id"]),"PUT",{"timezone":"America/Costa_Rica","settings":{"notifications":False}})
s=services[0]
api("services/"+str(s["id"]),"PUT",{"name":"Cita de demostracion","description":"Servicio de prueba; configurar catalogo real antes de produccion."})
print("Services and providers API: OK; demo timezone configured.")
day=None
slots=[]
for offset in range(2,16):
    candidate=(datetime.date.today()+datetime.timedelta(days=offset)).isoformat()
    found=api("availabilities?"+urlencode({"providerId":p["id"],"serviceId":s["id"],"date":candidate}))
    if len(found)>=2:
        day=candidate; slots=found; break
assert day, "No demo availability found"
c=api("customers","POST",{"firstName":"Serael","lastName":"Prueba API","email":"booking-test@example.invalid","phone":"+50600000000"})
appointment=None
try:
    start=datetime.datetime.fromisoformat(day+" "+slots[0])
    end=start+datetime.timedelta(minutes=int(s["duration"]))
    appointment=api("appointments","POST",{"start":str(start),"end":str(end),"serviceId":s["id"],"providerId":p["id"],"customerId":c["id"],"notes":"Automated installation validation; delete after test"})
    aid=appointment["id"]
    assert api("appointments/"+str(aid))["id"]==aid
    newstart=datetime.datetime.fromisoformat(day+" "+slots[1])
    updated=api("appointments/"+str(aid),"PUT",{"start":str(newstart),"end":str(newstart+datetime.timedelta(minutes=int(s["duration"])))})
    assert updated["start"]==str(newstart)
    api("appointments/"+str(aid),"DELETE")
    appointment=None
    print("Booking API lifecycle: availability, create, read, reschedule and cancel PASSED.")
finally:
    if appointment:
        api("appointments/"+str(appointment["id"]),"DELETE")
    api("customers/"+str(c["id"]),"DELETE")
print("Test customer and appointment removed. SMTP remains pending.")
