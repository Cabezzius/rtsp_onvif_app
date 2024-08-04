# Visor y Controlador de Cámaras IP RTSP

Este proyecto es una aplicación Python que permite visualizar y controlar cámaras IP utilizando los protocolos RTSP y ONVIF. La aplicación se ejecuta en un contenedor Docker y utiliza VNC para la visualización remota.

## Características

- Visualización en tiempo real de múltiples cámaras IP
- Control de movimiento PTZ (Pan, Tilt, Zoom) para cámaras compatibles con ONVIF
- Grabación de video de alta calidad con compresión eficiente usando H.265
- Interfaz gráfica de usuario intuitiva construida con PyQt5
- Containerización con Docker para fácil implementación y portabilidad

## Requisitos previos

- Docker
- Docker Compose

## Configuración

1. Clona este repositorio:
   ```
   git clone https://github.com/tu-usuario/nombre-del-repo.git
   cd nombre-del-repo
   ```

2. Configura las variables de entorno en el archivo `docker-compose.yml`:
   ```yaml
   environment:
     - CAMERA1_IP=192.168.x.x
     - CAMERA1_PORT=8899
     - CAMERA1_USER=usuario
     - CAMERA1_PASS=contraseña
     - CAMERA2_IP=192.168.x.x
     - CAMERA2_PORT=8899
     - CAMERA2_USER=usuario
     - CAMERA2_PASS=contraseña
   ```

## Uso

1. Construye e inicia el contenedor Docker:
   ```
   docker-compose up --build
   ```

2. Conéctate al contenedor usando un cliente VNC en `localhost:5900`.

3. La interfaz de la aplicación debería aparecer, mostrando las transmisiones de video de las cámaras configuradas.

4. Usa los botones de control para mover las cámaras (si son compatibles con ONVIF) y para iniciar/detener la grabación.

## Estructura del proyecto

- `rtsp_onvif_app.py`: Archivo principal de la aplicación
- `ui_module.py`: Módulo que contiene la interfaz de usuario
- `Dockerfile`: Configuración para construir la imagen Docker
- `docker-compose.yml`: Configuración para ejecutar el contenedor Docker
- `run_app.sh`: Script para iniciar la aplicación dentro del contenedor

## Solución de problemas

- Si una cámara no se conecta, verifica la configuración de red y las credenciales en `docker-compose.yml`.
- Para problemas de visualización, asegúrate de que el cliente VNC esté configurado correctamente.

## Contribuir

Las contribuciones son bienvenidas. Por favor, abre un issue para discutir cambios mayores antes de enviar un pull request.

## Licencia

[MIT License](https://opensource.org/licenses/MIT)