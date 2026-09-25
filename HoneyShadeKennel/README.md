# Honey Shade Kennel

Flask alapú, reszponzív tenyészet-weboldal adminfelülettel.

## Indítás Windows alatt
A projekt gyökerében PowerShellből futtasd:
```powershell
if (!(Test-Path .venv)) { py -m venv .venv }; .\.venv\Scripts\python.exe -m pip install -r requirements.txt; .\.venv\Scripts\python.exe app.py
```
Ezután: http://127.0.0.1:5000

## Admin
Cím: `/admin/login` · Felhasználó: `admin`
Élesítés előtt állítsd be az `ADMIN_PASSWORD`, `ADMIN_USER` és `SECRET_KEY` környezeti változókat.

## Cloudflare
A Flask alkalmazást Python-képes hosztingon kell futtatni, amelyhez a Cloudflare DNS/proxy kapcsolható.
