# Evidencias de la Parte A — balanceador local

Fecha: 30 de septiembre de 2026. Entorno: Windows con Docker Desktop; Nginx expuesto en el puerto 80, tres backends en 8081–8083, Django y PostgreSQL compartido. Todas las pruebas siguientes se realizaron sobre la aplicación TecnoStock.

## 1. Nginx y tres backends

Los contenedores de Nginx, PostgreSQL y los tres backends quedaron en ejecución. `GET /health/` devolvió HTTP 200 tanto en el puerto 80 como en 8081, 8082 y 8083. Cada backend respondió con su identificador correcto. Ver `01-contenedores.txt`.

## 2. Round Robin

Treinta solicitudes a `http://127.0.0.1/instance/` dieron: backend 1 = 10, backend 2 = 11, backend 3 = 9, con cero fallos (`02-round-robin.txt`). Esto confirma que el tráfico se distribuye entre las tres instancias.

## 3. Pesos 5:3:2

Con `nginx/weighted.conf`, cien solicitudes dieron 55, 28 y 17 respuestas respectivamente (`03-ponderado.txt`). La proporción observada es próxima a la esperada de 50/30/20. Una muestra de 100 peticiones, el momento de recarga y las conexiones abiertas pueden causar desviaciones pequeñas. Se restauró Round Robin al terminar.

## 4. Caída y recuperación

Se detuvo `backend2`. De 20 solicitudes, 15 fueron atendidas por backend 1 y 5 por backend 3; no hubo fallos (`04-caida-backend2.txt`). Después de reiniciarlo y esperar la ventana de `fail_timeout`, 30 solicitudes se repartieron 10/10/10 con cero fallos (`05-recuperacion-backend2.txt`). Esto demuestra continuidad de servicio y reincorporación de la instancia. El reparto durante el breve periodo de falla no tiene que ser exactamente mitad y mitad por el mecanismo de detección pasiva.

## 5. Rendimiento local

| Ruta | Solicitudes | Concurrencia | Solicitudes/s | Latencia media | Fallos |
|---|---:|---:|---:|---:|---:|
| Backend 1 directo | 1000 | 50 | 658.39 | 70.62 ms | 0 |
| Nginx balanceado | 1000 | 50 | 960.52 | 44.82 ms | 0 |

Datos en `06-carga-directa.txt` y `07-carga-balanceada.txt`. Ambas pruebas usaron la misma ruta `/health/` y la misma concurrencia. En esta ejecución, el balanceador atendió más solicitudes por segundo y redujo la latencia media. La ruta consulta PostgreSQL, por lo que la medición incluye aplicación y base de datos. El resultado es una medición puntual de este equipo, no una garantía general de rendimiento. Factores como el calentamiento de procesos, la carga del sistema y los límites de conexiones pueden alterar otra ejecución. La comparación confirma que la configuración no introdujo fallos bajo la carga probada. También muestra el beneficio de disponer de varios procesos para repartir solicitudes concurrentes.

## 6. Login y CRUD compartidos

Se inició sesión en backend 1 y la misma sesión accedió al inventario en backend 2. Se creó un producto temporal en backend 3, se leyó desde backend 1 y se eliminó desde backend 2 (`08-sesion-y-crud.txt`). El registro temporal se limpió al finalizar. Esto verifica que sesión y datos residen en el PostgreSQL compartido y no dependen de la memoria de una sola instancia.

## 7. Algoritmos adicionales

Con `least_conn`, treinta peticiones secuenciales produjeron 17/7/6 (`09-least-connections.txt`). Este algoritmo considera conexiones activas, por lo que las solicitudes secuenciales no demuestran una proporción esperada. Con `ip_hash`, treinta peticiones desde el mismo cliente fueron al mismo backend (30/0/0; `10-ip-hash.txt`). Se restauró Round Robin al terminar.

## Conclusiones

1. Nginx distribuye el tráfico entre tres instancias de la misma aplicación y permite observar distintas políticas de balanceo.
2. PostgreSQL compartido conserva el login y los productos cuando las peticiones llegan a servidores distintos.
3. La detección pasiva de fallos mantiene el servicio disponible con dos backends y reincorpora al tercero después de recuperarse.

La Parte B de AWS queda para la siguiente etapa, según la indicación del propietario del proyecto.
