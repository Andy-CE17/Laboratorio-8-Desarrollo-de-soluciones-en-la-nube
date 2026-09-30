# TecnoStock — Laboratorio 7

Aplicación monolítica de inventario con inicio de sesión y gestión de productos (crear, consultar, editar y eliminar). Se desarrolló con Django y PostgreSQL para demostrar el balanceo de carga en un entorno local y en AWS.

## Parte A: balanceador local

Docker Compose levanta PostgreSQL, tres instancias de Django (`backend1`, `backend2` y `backend3`) y Nginx. Los backends se pueden consultar individualmente en los puertos `8081`, `8082` y `8083`; Nginx publica la aplicación en `http://localhost/` por el puerto 80.

Se probaron Round Robin, distribución ponderada `5:3:2`, Least Connections e IP Hash. También se comprobó la continuidad del servicio al detener un backend y el estado compartido de productos y sesiones en PostgreSQL. Las configuraciones están en `nginx/` y los resultados de las pruebas en `evidencias/parte-a/`.

Para levantar el entorno local, configura primero `.env` con las variables requeridas por `compose.yaml` y ejecuta:

```powershell
docker compose up -d --build
docker compose ps
```

## Parte B: balanceador en AWS

La pila `tecnostock-lab7` despliega una VPC, un Application Load Balancer público en HTTP:80, dos EC2 en `us-east-1a` y `us-east-1b` y PostgreSQL RDS compartido en subredes privadas. El grupo de destino `tg-lab-web` verifica la ruta `/health/`. CloudFront ofrece una dirección HTTPS para usar la aplicación en el navegador; el ALB permanece en HTTP:80 para las pruebas del laboratorio.

Se verificó que ambas instancias estuvieran saludables, que el ALB distribuyera solicitudes entre `web-server-1` y `web-server-2`, que el login y los productos funcionaran con la base compartida y que el servicio continuara al detener una instancia. Tras reiniciarla, ambas volvieron a estar saludables.

- Aplicación: https://d200k3ba463pp2.cloudfront.net/login/
- Identificación del servidor por el ALB: http://alb-lab-web-814426920.us-east-1.elb.amazonaws.com/instance/
- Infraestructura y scripts de despliegue: `deploy/aws/`.

Los recursos de AWS pueden generar cargos mientras sigan activos. La base RDS es Single-AZ; la prueba de tolerancia a fallos se realizó sobre los servidores web.
