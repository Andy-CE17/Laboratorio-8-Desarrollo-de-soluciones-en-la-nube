"""Verify login and a temporary product across the two EC2 instances.

Usage: set DEMO_PASSWORD, then run `python scripts/verify_aws.py http://ALB-DNS`.
"""

import os
import re
import sys
import uuid

import requests


base = sys.argv[1].rstrip("/")
password = os.environ["DEMO_PASSWORD"]
session = requests.Session()


def get(path):
    response = session.get(base + path, timeout=15)
    response.raise_for_status()
    return response.text, response.url


def post(path, data):
    response = session.post(base + path, data=data, timeout=15)
    response.raise_for_status()
    return response.text, response.url


def csrf(html):
    match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html)
    if not match:
        raise AssertionError("No se encontró el token CSRF")
    return match.group(1)


login_html, _ = get("/login/")
html, url = post("/login/", {"username": "laboratorio", "password": password, "csrfmiddlewaretoken": csrf(login_html)})
assert url.rstrip("/") == base, f"El inicio de sesión no llegó al inventario: {url}"
assert "TEC-001" in html, "No se encontraron los productos de demostración"

new_html, _ = get("/products/new/")
code = "AWS-" + uuid.uuid4().hex[:8].upper()
post("/products/new/", {
    "csrfmiddlewaretoken": csrf(new_html),
    "code": code, "name": "Verificación temporal AWS", "category": "perifericos",
    "description": "Prueba de estado compartido", "price": "12.50", "stock": "3",
})

seen = set()
delete_path = None
try:
    for _ in range(30):
        html, _ = get("/")
        assert code in html, "El producto temporal no aparece en el inventario"
        server = re.search(r"Servidor:\s*(web-server-[12])", html)
        if server:
            seen.add(server.group(1))
        row = next((row for row in re.findall(r"<tr\b[^>]*>.*?</tr>", html, re.S) if code in row), None)
        if row:
            action = re.search(r'action="(/products/\d+/delete/)"', row)
            if action:
                delete_path = action.group(1)
        if len(seen) == 2 and delete_path:
            break
    assert len(seen) == 2, f"No se observaron ambas instancias: {seen}"
    print(f"Login, lectura y producto compartido verificados en: {', '.join(sorted(seen))}")
finally:
    if delete_path:
        html, _ = get("/")
        post(delete_path, {"csrfmiddlewaretoken": csrf(html)})
        html, _ = get("/")
        assert code not in html, "No se pudo eliminar el producto temporal"
        print("Producto temporal eliminado")
