#!/bin/bash

# Configurar variables de entorno para RTSP
export OPENCV_FFMPEG_CAPTURE_OPTIONS="rtsp_transport;udp|reorder_queue_size;0|max_delay;30000000"

# Configurar variables de entorno para la visualización
export QT_X11_NO_MITSHM=1
export XDG_RUNTIME_DIR="/tmp/runtime-root"

# Crear el directorio XDG_RUNTIME_DIR si no existe
mkdir -p $XDG_RUNTIME_DIR
chmod 0700 $XDG_RUNTIME_DIR

# Iniciar el servidor VNC con una resolución más grande
Xvfb :1 -screen 0 1280x1024x16 &
x11vnc -display :1 -nopw -forever -quiet &

# Esperar un poco para asegurar que el servidor VNC esté listo
sleep 5

# Imprimir información de depuración
echo "Contenido de /usr/local/lib/python3.8/dist-packages/wsdl:"
ls -l /usr/local/lib/python3.8/dist-packages/wsdl
echo "Contenido de /usr/local/lib/ver10/schema:"
ls -l /usr/local/lib/ver10/schema

# Comprobar conectividad con las cámaras
echo "Comprobando conectividad con las cámaras..."
ping -c 1 $CAMERA1_IP && echo "Cámara $CAMERA1_IP accesible" || echo "No se puede acceder a la cámara $CAMERA1_IP"
ping -c 1 $CAMERA2_IP && echo "Cámara $CAMERA2_IP accesible" || echo "No se puede acceder a la cámara $CAMERA2_IP"

# Verificar la existencia del archivo Python
echo "Verificando la existencia de rtsp_onvif_app.py..."
ls -l /app/rtsp_onvif_app.py

# Mostrar las primeras líneas del archivo Python
echo "Primeras líneas de rtsp_onvif_app.py:"
head -n 10 /app/rtsp_onvif_app.py

# Ejecutar la aplicación con salida detallada
echo "Iniciando la aplicación Python..."
python3 -v /app/rtsp_onvif_app.py
# Ejecutar la aplicación
python3 rtsp_onvif_app.py
#hecho un cambio
