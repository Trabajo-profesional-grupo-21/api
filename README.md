# API

## Dependencies
[Docker](https://www.docker.com/)

[Docker-compose](https://docs.docker.com/compose/)

## Uso

### Ejecutar el sistema completo

Para ejecutar el sistema completo seguir la siguiente guía: [Manual de ejecución](https://trabajo-profesional-grupo-21.github.io/manual-ejecucion/)



### Ejecutar API

Para que la API funcione correctamente debe indicar los accesos a todos los servicios necesarios por la API, estos son: RabbitMQ, Redis, MongoDB y Google cloud Object storage. Para esto se puede utilizar un `.env` (a partir del template en `.env_example`). También detallado en el Manual de ejecución.

Ahora podemos usar el `docker-compose.yaml`:

```bash
docker compose up --build
```

Para remover el contenedor:
```bash
docker compose down
```
