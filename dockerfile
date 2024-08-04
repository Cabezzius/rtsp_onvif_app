# Usa una imagen base con soporte para GUI
FROM ubuntu:20.04

# Evita las preguntas interactivas durante la instalación de paquetes
ENV DEBIAN_FRONTEND=noninteractive

# Instala las dependencias necesarias
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-pyqt5 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    git \
    wget \
    xvfb \
    x11vnc \
    xauth \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libx265-dev \
    libavcodec-extra \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# Instalar las bibliotecas Python necesarias
RUN pip3 install --upgrade pip && \
    pip3 install opencv-python-headless numpy PyQt5 onvif-zeep==0.2.12 ffmpeg-python

RUN mkdir -p /usr/local/lib/python3.8/dist-packages/wsdl && \
    wget https://www.onvif.org/ver10/device/wsdl/devicemgmt.wsdl -O /usr/local/lib/python3.8/dist-packages/wsdl/devicemgmt.wsdl && \
    wget https://www.onvif.org/ver10/media/wsdl/media.wsdl -O /usr/local/lib/python3.8/dist-packages/wsdl/media.wsdl && \
    wget https://www.onvif.org/ver20/ptz/wsdl/ptz.wsdl -O /usr/local/lib/python3.8/dist-packages/wsdl/ptz.wsdl && \
    wget https://www.onvif.org/ver10/events/wsdl/event.wsdl -O /usr/local/lib/python3.8/dist-packages/wsdl/events.wsdl && \
    mkdir -p /usr/local/lib/ver10/schema && \
    wget https://www.onvif.org/ver10/schema/onvif.xsd -O /usr/local/lib/ver10/schema/onvif.xsd && \
    wget https://www.onvif.org/ver10/schema/common.xsd -O /usr/local/lib/ver10/schema/common.xsd && \
    wget https://www.w3.org/2003/05/soap-envelope/ -O /usr/local/lib/ver10/schema/soap-envelope.xsd && \
    wget https://www.w3.org/2004/08/xop/include -O /usr/local/lib/ver10/schema/xop-include.xsd && \
    wget https://www.w3.org/2005/05/xmlmime -O /usr/local/lib/ver10/schema/xmlmime.xsd

# Crear directorios necesarios
RUN mkdir -p /app /app/config /app/recordings

# Copiar todos los archivos Python y el script de ejecución
COPY *.py /app/
COPY run_app.sh /app/

# Dar permisos de ejecución al script
RUN chmod +x /app/run_app.sh

# Establecer el directorio de trabajo
WORKDIR /app

# Ejecutar el script
CMD ["/app/run_app.sh"]