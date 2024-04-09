# API

## Dependencies
[Poetry](https://python-poetry.org/docs/#:~:text=to%20install%20Poetry.-,Install%20Poetry,-pipx%20install%20poetry)
[Docker](https://www.docker.com/)

## Uso

### Ejecutar RabbitMQ

Si no tenemos una instancia de RabbitMQ corriendo, debemos levantar una en nuestro local

Para levantar el contenedor de rabbit hay dos opciones:

- Clonar el repositorio: [rabbitmq](https://github.com/Trabajo-profesional-grupo-21/rabbitmq) y seguir los pasos del README para ejecutarla usando `docker-compose`
- Seguir los siguientes pasos: ⬇️⬇️⬇️

Primero creamos una network de docker:

```bash
docker network create custom_network
```

Luego ejecutamos el contenedor con rabbit:

```bash
docker run -d --name rabbitmq \
  -p 15672:15672 \
  -p 5672:5672 \
  --network custom_network \
  --rm \
  rabbitmq:3.9.16-management-alpine \
  && docker logs -f rabbitmq
```

Para detener el contenedor de rabbit:

```bash
docker container stop rabbitmq
```



### Ejecutar API

Ahora podemos usar el `docker-compose.yaml` para ejecutar la api:

```bash
docker compose up --build
```

Para remover el contenedor:
```bash
docker compose down
```
