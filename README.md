# TecnoStock — Laboratorio 8

**Este Laboratorio 8 es la continuación directa del Laboratorio 7.** Se retomó la misma aplicación monolítica TecnoStock de inventario y se amplió con control de acceso por roles y tienda, registro con política de contraseñas, bloqueo temporal, verificación TOTP, JWT e inicio de sesión con Google y GitHub. El trabajo del Laboratorio 8 se publica por separado; el código y las evidencias originales del Laboratorio 7 permanecen en [su repositorio](https://github.com/Andy-CE17/Laboratorio-7-Desarrolo-de-soluciones-en-la-nube).

## Qué se construyó en el Laboratorio 7

En la Parte A, Docker Compose ejecutó PostgreSQL, tres instancias de Django (`backend1`, `backend2`, `backend3`) y Nginx. Se probaron Round Robin, distribución ponderada `5:3:2`, Least Connections e IP Hash, además de la continuidad del servicio al detener una instancia. Las configuraciones están en `nginx/` y las capturas en `evidencias/parte-a/`.

En la Parte B, la aplicación se desplegó en AWS con un Application Load Balancer público, dos EC2 en distintas zonas de disponibilidad y PostgreSQL RDS compartido. El grupo de destino comprobaba `/health/`; CloudFront proporcionó HTTPS al navegador. Se verificó el reparto de solicitudes, el estado compartido y la recuperación tras reiniciar una instancia. Los recursos de AWS de esa práctica se eliminaron al terminar para evitar cargos. Los archivos de despliegue permanecen en `deploy/aws/` como código del laboratorio.

## Laboratorio 8: identidad y permisos

## Ejecutar localmente

Con Python 3.11 y Node.js instalados, desde la carpeta `App`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
npm ci
npm run build:css
Copy-Item .env.example .env
```

Edita `.env` para asignar un `DJANGO_SECRET_KEY` aleatorio, `DJANGO_DEBUG=1`, `DJANGO_CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8001` y, si deseas una contraseña reproducible para las cuentas de ejemplo, `DEMO_PASSWORD`. El valor `DATABASE_URL=sqlite:///local-dev.sqlite3` es solo para la ejecución local.

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8001
```

Abre `http://127.0.0.1:8001/login/`. `seed_demo` muestra la contraseña inicial y crea cuentas con los correos `admin@tecnostock.local`, `gerente@tecnostock.local`, `ventas@tecnostock.local` y `auditor@tecnostock.local`. En el primer acceso, cada cuenta configura una aplicación TOTP escaneando un código QR. La contraseña queda en `.env` si definiste `DEMO_PASSWORD`; nunca subas ese archivo.

## Permisos

| Rol | Alcance | Acciones |
| --- | --- | --- |
| Administrador | Todas las tiendas | Productos, reportes, usuarios y roles |
| Gerente | Su tienda | Productos y reportes; no modifica otra tienda |
| Ventas | Su tienda | Consulta productos y actualiza stock; no modifica precios |
| Auditor | Todas las tiendas | Consulta productos y reportes; sin cambios |

El registro aparece en la misma pantalla de inicio de sesión y crea cuentas con el rol inicial **Empleado de ventas**. Requiere correo único, nombre completo, tienda y contraseña de al menos ocho caracteres con mayúscula, número y símbolo. El administrador puede cambiar el rol y la tienda en **Equipo y roles**. Después de cinco contraseñas incorrectas para una cuenta existente, esta se bloquea por 15 minutos. El segundo factor admite tres intentos por acceso. Al verificarlo se emite un JWT de 15 minutos en una cookie HttpOnly; la ruta `/api/session/` valida el token y la sesión. Cada usuario puede poner un enlace HTTPS a su foto desde **Mi perfil**.

## Activar Google y GitHub

Los botones se muestran como pendientes hasta configurar aplicaciones OAuth. En los portales oficiales de cada proveedor, registra las siguientes URL de retorno para la ejecución local:

- Google: `http://127.0.0.1:8001/accounts/google/login/callback/`
- GitHub: `http://127.0.0.1:8001/accounts/github/login/callback/`

Guarda `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GITHUB_CLIENT_ID` y `GITHUB_CLIENT_SECRET` en `.env`; reinicia Django. Las cuentas sociales nuevas entran como **Ventas** en la primera tienda y pasan por el mismo segundo factor TOTP. Si Google devuelve un correo verificado que ya pertenece a una cuenta con correo verificado, ambas formas de acceso usan la misma cuenta y conservan su rol. También se pueden vincular Google y GitHub desde **Mi perfil**. Para evitar el error `redirect_uri_mismatch`, abre la aplicación con `127.0.0.1:8001` (la pantalla local de `localhost:8001` redirige allí).

## Verificación

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test
```

No se han desplegado recursos de AWS para el Laboratorio 8. La configuración OAuth necesita credenciales creadas en Google y GitHub; no se incluyen claves en el repositorio.
