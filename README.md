# TecnoStock — Laboratorio 7

Aplicación monolítica de inventario desarrollada con Django, plantillas HTML, Tailwind CSS y PostgreSQL. Incluye inicio de sesión, CRUD de productos y una ruta para comprobar qué instancia atiende cada solicitud.

## Parte A: entorno local

La topología sigue la guía del laboratorio: navegador o `curl` → Nginx en el puerto 80 → tres instancias idénticas de la aplicación publicadas en `127.0.0.1:8081`, `:8082` y `:8083`. Nginx corre en Docker, así que dentro de su red usa `backend1:8000`, `backend2:8000` y `backend3:8000`; los puertos 8081–8083 son las equivalencias visibles desde Windows. Las tres instancias comparten la misma base PostgreSQL y la misma clave de Django.

### Iniciar

Requisitos: Docker Desktop con el motor Linux activo. Desde PowerShell, en esta carpeta:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
# Edita .env y reemplaza POSTGRES_PASSWORD y DJANGO_SECRET_KEY con valores aleatorios.
docker compose build
docker compose up -d db
docker compose run --rm migrate
docker compose up -d backend1 backend2 backend3 nginx
docker compose exec backend1 python manage.py seed_demo
```

En este equipo el archivo `.env` ya se creó con valores aleatorios y los contenedores están iniciados. Abre `http://localhost/login/`. `seed_demo` crea el usuario `laboratorio`, imprime su contraseña inicial una sola vez y agrega cinco productos de ejemplo. La contraseña también fue comunicada al propietario del proyecto; si se pierde, puede cambiarse con `python manage.py changepassword laboratorio` dentro de un contenedor.

### Comprobar la topología

```powershell
curl.exe http://localhost/health/
curl.exe http://localhost/instance/
curl.exe http://localhost:8081/instance/
curl.exe http://localhost:8082/instance/
curl.exe http://localhost:8083/instance/
python scripts/sample_distribution.py 30
```

`/health/` consulta también PostgreSQL. Devuelve HTTP 503 si la base no responde. `/instance/` muestra el nombre de la instancia y facilita la prueba de distribución. Estas rutas no requieren inicio de sesión porque el balanceador debe poder consultar el estado y la instancia.

### Cambiar el algoritmo

```powershell
./scripts/select_balancer.ps1 round-robin
./scripts/select_balancer.ps1 weighted
./scripts/select_balancer.ps1 least-connections
./scripts/select_balancer.ps1 ip-hash
```

La configuración ponderada utiliza pesos 5:3:2. El script valida y recarga Nginx. Para volver a la configuración de entrega, ejecuta `round-robin`.

### Probar una caída

```powershell
docker compose stop backend2
python scripts/sample_distribution.py 20
docker compose start backend2
# Espera aproximadamente 15 segundos para que expire fail_timeout.
python scripts/sample_distribution.py 30
```

La detección local es pasiva mediante `max_fails=2` y `fail_timeout=15s`. Los resultados registrados están en `evidencias/parte-a/`.

### Probar login y CRUD entre instancias

El script requiere la contraseña del usuario `laboratorio` en la variable de entorno `DEMO_PASSWORD`:

```powershell
$env:DEMO_PASSWORD = 'tu-contraseña-de-laboratorio'
python scripts/verify_shared_state.py
Remove-Item Env:DEMO_PASSWORD
```

Inicia sesión en el puerto 8081, visita el inventario en 8082, crea un producto temporal en 8083, lo lee en 8081 y lo elimina en 8082.

### Comparar rendimiento

```powershell
python scripts/benchmark.py http://127.0.0.1:8081/health/ 1000 50
python scripts/benchmark.py http://127.0.0.1/health/ 1000 50
docker compose run --rm backend1 python manage.py test
```

El benchmark usa 1000 solicitudes con concurrencia 50. Es una comparación local de la ruta `/health/`; sus resultados dependen del equipo y de la carga concurrente, por lo que no deben extrapolarse directamente a AWS.

## Parte B: AWS

Pendiente por indicación del propietario: primero se completa la evidencia de la Parte A. No se han creado recursos ni generado cargos en AWS.
