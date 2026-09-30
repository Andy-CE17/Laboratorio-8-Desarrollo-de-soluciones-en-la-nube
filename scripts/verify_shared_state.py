"""Comprueba sesión y CRUD entre los tres puertos usando el usuario de demostración."""
import http.cookiejar
import os
import re
import urllib.parse
import urllib.request

password = os.environ.get("DEMO_PASSWORD")
if not password:
    raise SystemExit("Define DEMO_PASSWORD en el entorno para ejecutar esta prueba.")

jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def get(url):
    with opener.open(url, timeout=8) as response:
        return response.status, response.read().decode("utf-8"), response.url


def post(url, data):
    body = urllib.parse.urlencode(data).encode()
    with opener.open(urllib.request.Request(url, data=body), timeout=8) as response:
        return response.status, response.read().decode("utf-8"), response.url


def csrf():
    for cookie in jar:
        if cookie.name == "csrftoken":
            return cookie.value
    raise RuntimeError("No se recibió cookie CSRF")


get("http://127.0.0.1:8081/login/")
status, page, url = post("http://127.0.0.1:8081/login/", {
    "username": "laboratorio", "password": password, "csrfmiddlewaretoken": csrf(),
})
assert status == 200 and "Inventario" in page and "/login/" not in url
print("Login en backend-1: correcto")

status, page, url = get("http://127.0.0.1:8082/")
assert status == 200 and "Inventario" in page and "/login/" not in url
print("Misma sesión en backend-2: correcta")

code = "PRUEBA-RED-001"
status, page, url = post("http://127.0.0.1:8083/products/new/", {
    "csrfmiddlewaretoken": csrf(), "code": code, "name": "Producto de prueba de red",
    "category": "otros", "description": "Prueba temporal", "price": "12.50", "stock": "3",
})
assert status == 200 and code in page and "/products/new/" not in url
print("Crear producto en backend-3: correcto")

status, page, url = get("http://127.0.0.1:8081/")
assert status == 200 and code in page
print("Consultar producto en backend-1: correcto")

match = re.search(r'<tr>.*?' + code + r'.*?/products/(\d+)/edit/', page, re.S)
assert match, "No se encontró el enlace para limpiar el producto temporal"
product_id = int(match.group(1))

status, page, url = post(f"http://127.0.0.1:8082/products/{product_id}/delete/", {
    "csrfmiddlewaretoken": csrf(),
})
assert status == 200 and code not in page
print("Eliminar producto en backend-2: correcto")
