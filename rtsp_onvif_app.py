import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QLabel, QScrollArea, QWidget
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt
from onvif import ONVIFCamera
import datetime
import json
import os
import logging
import time
from ui_module import RTSPPlayerUI

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

MAX_RECORDING_TIME = 3600 * 3  # 3 horas

class CameraThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray, str)
    error_signal = pyqtSignal(str, str)

    def __init__(self, rtsp_url, camera_ip):
        super().__init__()
        self.rtsp_url = rtsp_url
        self.camera_ip = camera_ip
        self._run_flag = True

    def run(self):
        cap = cv2.VideoCapture(self.rtsp_url)
        if not cap.isOpened():
            self.error_signal.emit(self.camera_ip, f"No se pudo abrir la conexión RTSP para {self.camera_ip}")
            return

        while self._run_flag:
            ret, cv_img = cap.read()
            if ret:
                self.change_pixmap_signal.emit(cv_img, self.camera_ip)
            else:
                self.error_signal.emit(self.camera_ip, f"Failed to read frame from camera {self.camera_ip}")
                time.sleep(5)  # Wait a bit longer before trying again
                cap.release()
                cap = cv2.VideoCapture(self.rtsp_url)  # Try to reconnect
        cap.release()

    def stop(self):
        self._run_flag = False
        self.wait()

class RTSPPlayer:
    def __init__(self, cameras):
        self.cameras = cameras
        self.recordings = {cam['ip']: {'is_recording': False, 'out': None, 'start_time': None, 'frame_count': 0} for cam in cameras}
        self.recordings_dir = '/app/recordings'
        self.threads = {}
        self.onvif_cameras = {}

        callbacks = {
            'toggle_recording': self.toggle_recording,
            'start_move': self.start_move_camera,
            'stop_move': self.stop_move_camera
        }
        self.ui = RTSPPlayerUI(cameras, callbacks)

        self.setup_onvif_cameras()
        self.start_camera_threads()
    def update_cameras(self, new_cameras):
        # Detener las conexiones existentes
        for thread in self.threads.values():
            thread.stop()    

    def setup_onvif_cameras(self):
        for cam in self.cameras:
            try:
                mycam = ONVIFCamera(cam['ip'], cam['port'], cam['user'], cam['pass'], '/usr/local/lib/python3.8/dist-packages/wsdl/')
                media = mycam.create_media_service()
                ptz = mycam.create_ptz_service()
                media_profile = media.GetProfiles()[0]
                self.onvif_cameras[cam['ip']] = {'camera': mycam, 'media': media, 'ptz': ptz, 'media_profile': media_profile}
                logging.info(f"ONVIF camera setup successful for {cam['ip']}")
            except Exception as e:
                logging.error(f"Failed to setup ONVIF camera for {cam['ip']}: {str(e)}")

    def start_camera_threads(self):
        for cam in self.cameras:
            thread = CameraThread(cam['rtsp_url'], cam['ip'])
            thread.change_pixmap_signal.connect(self.update_image)
            thread.error_signal.connect(self.handle_camera_error)
            self.threads[cam['ip']] = thread
            thread.start()

    def update_image(self, cv_img, camera_ip):
        qt_img = self.convert_cv_qt(cv_img, camera_ip)
        self.ui.update_image(qt_img, camera_ip)

        if self.recordings[camera_ip]['is_recording']:
            self.record_frame(camera_ip, cv_img)

    def convert_cv_qt(self, cv_img, camera_ip):
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(400, 300, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)

    def toggle_recording(self, camera_ip):
        if not self.recordings[camera_ip]['is_recording']:
            self.start_recording(camera_ip)
        else:
            self.stop_recording(camera_ip)

    def start_recording(self, camera_ip):
        now = datetime.datetime.now()
        filename = os.path.join(self.recordings_dir, f"{camera_ip}_{now.strftime('%Y%m%d_%H%M%S')}.mp4")
        
        cap = cv2.VideoCapture(self.cameras[self.cameras.index(next(cam for cam in self.cameras if cam['ip'] == camera_ip))]['rtsp_url'])
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        cap.release()

        # Aumentar el bitrate (por ejemplo, a 5Mbps)
        bitrate = 5000000

        # Usar el códec H.264 para mejor calidad y compatibilidad
        fourcc = cv2.VideoWriter_fourcc(*'avc1')
        
        self.recordings[camera_ip]['out'] = cv2.VideoWriter(filename, fourcc, fps, (width, height))
        
        # Configurar el bitrate
        self.recordings[camera_ip]['out'].set(cv2.VIDEOWRITER_PROP_QUALITY, 1)  # Mejor calidad
        self.recordings[camera_ip]['out'].set(cv2.VIDEOWRITER_PROP_BITRATE, bitrate)

        self.recordings[camera_ip]['is_recording'] = True
        self.recordings[camera_ip]['start_time'] = time.time()
        self.recordings[camera_ip]['frame_count'] = 0
        self.ui.set_record_button_text(camera_ip, 'Detener Grabación')
        logging.info(f"Iniciando grabación para {camera_ip}: {filename} con resolución {width}x{height} a {fps} FPS y bitrate {bitrate/1000000}Mbps")

    def stop_recording(self, camera_ip):
        self.recordings[camera_ip]['is_recording'] = False
        if self.recordings[camera_ip]['out']:
            self.recordings[camera_ip]['out'].release()
            self.recordings[camera_ip]['out'] = None
        self.ui.set_record_button_text(camera_ip, 'Iniciar Grabación')
        logging.info(f"Grabación detenida para {camera_ip}")

    def record_frame(self, camera_ip, frame):
        if self.recordings[camera_ip]['is_recording']:
            self.recordings[camera_ip]['out'].write(frame)
            self.recordings[camera_ip]['frame_count'] += 1
            
            elapsed_time = time.time() - self.recordings[camera_ip]['start_time']
            if elapsed_time >= MAX_RECORDING_TIME:
                self.stop_recording(camera_ip)
                self.start_recording(camera_ip)

    def start_move_camera(self, camera_ip, direction):
        if camera_ip not in self.onvif_cameras:
            logging.error(f"ONVIF camera not set up for {camera_ip}")
            return

        try:
            ptz = self.onvif_cameras[camera_ip]['ptz']
            media_profile = self.onvif_cameras[camera_ip]['media_profile']
            request = ptz.create_type('ContinuousMove')
            request.ProfileToken = media_profile.token

            speed = 0.1

            if direction == 'Izquierda':
                request.Velocity = {'PanTilt': {'x': -speed, 'y': 0}}
            elif direction == 'Derecha':
                request.Velocity = {'PanTilt': {'x': speed, 'y': 0}}
            elif direction == 'Arriba':
                request.Velocity = {'PanTilt': {'x': 0, 'y': speed}}
            elif direction == 'Abajo':
                request.Velocity = {'PanTilt': {'x': 0, 'y': -speed}}

            ptz.ContinuousMove(request)
            logging.info(f"Started moving camera {camera_ip} {direction}")
        except Exception as e:
            logging.error(f"Failed to start moving camera {camera_ip} {direction}: {str(e)}")

    def stop_move_camera(self, camera_ip):
        if camera_ip not in self.onvif_cameras:
            logging.error(f"ONVIF camera not set up for {camera_ip}")
            return

        try:
            ptz = self.onvif_cameras[camera_ip]['ptz']
            media_profile = self.onvif_cameras[camera_ip]['media_profile']
            request = ptz.create_type('Stop')
            request.ProfileToken = media_profile.token
            request.PanTilt = True
            request.Zoom = True
            ptz.Stop(request)
            logging.info(f"Stopped moving camera {camera_ip}")
        except Exception as e:
            logging.error(f"Failed to stop moving camera {camera_ip}: {str(e)}")

    def handle_camera_error(self, camera_ip, error_message):
        logging.error(f"Camera error for {camera_ip}: {error_message}")

def main():
    app = QApplication(sys.argv)
    
    # Obtener configuración
    camera_configs = get_camera_config()
    
    # Si no hay configuración, usar variables de entorno
    if not camera_configs:
        camera_configs = [
            {
                'ip': os.environ.get('CAMERA1_IP'),
                'puerto': os.environ.get('CAMERA1_PORT'),
                'usuario': os.environ.get('CAMERA1_USER'),
                'contraseña': os.environ.get('CAMERA1_PASS'),
            },
            {
                'ip': os.environ.get('CAMERA2_IP'),
                'puerto': os.environ.get('CAMERA2_PORT'),
                'usuario': os.environ.get('CAMERA2_USER'),
                'contraseña': os.environ.get('CAMERA2_PASS'),
            }
        ]
    
    cameras = []
    for config in camera_configs:
        camera = {
            'ip': config['ip'],
            'port': int(config['puerto']),
            'user': config['usuario'],
            'pass': config['contraseña'],
            'rtsp_url': f"rtsp://{config['usuario']}:{config['contraseña']}@{config['ip']}:{config['puerto']}/live/ch0"
        }
        cameras.append(camera)

    player = RTSPPlayer(cameras)
    player.ui.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()