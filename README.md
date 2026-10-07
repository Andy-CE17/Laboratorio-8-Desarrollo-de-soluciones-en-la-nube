# TecnoStock — Laboratorio 8

Este proyecto es la **continuación del Laboratorio 7**: parte de su aplicación Django de inventario y agrega autenticación y control de acceso. El [repositorio del Laboratorio 7](https://github.com/Andy-CE17/Laboratorio-7-Desarrolo-de-soluciones-en-la-nube) conserva la práctica de balanceo de carga con Docker, Nginx y AWS.

## Funcionamiento

TecnoStock permite gestionar productos, stock, tiendas y reportes. Los usuarios ingresan con contraseña o con Google/GitHub y completan un segundo factor con una aplicación autenticadora. La aplicación bloquea temporalmente una cuenta tras cinco contraseñas incorrectas y protege la sesión con JWT en una cookie HttpOnly.

## Roles

| Rol | Acceso |
| --- | --- |
| Administrador | Gestiona todas las tiendas, productos, reportes, usuarios y roles. |
| Gerente de tienda | Gestiona productos y reportes de su tienda. |
| Empleado de ventas | Consulta productos y actualiza el stock de su tienda. |
| Auditor | Consulta productos y reportes sin modificarlos. |

Las cuentas nuevas reciben el rol **Empleado de ventas**. El administrador puede cambiar el rol y la tienda en **Equipo y roles**.

## Enlaces

- [Laboratorio 8 en GitHub](https://github.com/Andy-CE17/Laboratorio-8-Desarrollo-de-soluciones-en-la-nube)
- [Laboratorio 7 en GitHub](https://github.com/Andy-CE17/Laboratorio-7-Desarrolo-de-soluciones-en-la-nube)
- Aplicación local: [http://127.0.0.1:8001/](http://127.0.0.1:8001/)
- Inicio de sesión: [http://127.0.0.1:8001/login/](http://127.0.0.1:8001/login/)
- Reportes: [http://127.0.0.1:8001/reports/](http://127.0.0.1:8001/reports/)

Los enlaces locales funcionan cuando el servidor está en ejecución. El Laboratorio 8 no tiene un despliegue público activo.

## Ejecutar rápido con Docker

Desde la carpeta `App`, crea `.env` a partir de `.env.example`, cambia `DJANGO_SECRET_KEY` y ejecuta:

```powershell
Copy-Item .env.example .env  # omite esta línea si ya tienes .env
docker compose up -d --build
```

Abre [http://127.0.0.1:8001/login/](http://127.0.0.1:8001/login/). Docker aplica las migraciones y crea las cuentas `admin@tecnostock.local`, `gerente@tecnostock.local`, `ventas@tecnostock.local` y `auditor@tecnostock.local`. Su contraseña inicial es `DEMO_PASSWORD` de `.env`; cámbiala allí antes del **primer** arranque si deseas otra. El segundo factor se configura con el QR en el primer acceso.

La base se guarda en el volumen `lab8_data`, separado de `local-dev.sqlite3`; `docker compose down` detiene la aplicación sin borrar los datos. Para Google y GitHub, coloca sus credenciales OAuth en `.env` antes de iniciar. Los retornos son `http://127.0.0.1:8001/accounts/google/login/callback/` y `http://127.0.0.1:8001/accounts/github/login/callback/`.

## Ejecutar sin Docker en Windows

Con Python 3.11 y Node.js instalados, desde la carpeta `App`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
npm ci
npm run build:css
Copy-Item .env.example .env
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8001
```

Antes de iniciar, configura `DJANGO_SECRET_KEY` y `DJANGO_DEBUG=1` en `.env`. Para activar Google y GitHub, agrega allí sus credenciales OAuth; los retornos son `http://127.0.0.1:8001/accounts/google/login/callback/` y `http://127.0.0.1:8001/accounts/github/login/callback/`. El archivo `.env` y la base de datos local no se publican en GitHub.
