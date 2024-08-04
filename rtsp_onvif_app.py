import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QImage, QPixmap
from onvif import ONVIFCamera
import datetime
import os
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from config_dialog import get_camera_config, ConfigDialog
from ui_module import RTSPPlayerUI
from welcome_screen import WelcomeScreen
from camera import Camera
from utils import retry_with_timeout

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

    @retry_with_timeout(max_retries=3, delay=2, timeout=10)
    def connect_to_camera(self):
        cap = cv2.VideoCapture(self.rtsp_url)
        if not cap.isOpened():
            raise Exception(f"No se pudo abrir la conexión RTSP para {self.camera_ip}")
        return cap

    def run(self):
        while self._run_flag:
            try:
                cap = self.connect_to_camera()
                while self._run_flag:
                    ret, cv_img = cap.read()
                    if ret:
                        self.change_pixmap_signal.emit(cv_img, self.camera_ip)
                    else:
                        raise Exception(f"Failed to read frame from camera {self.camera_ip}")
            except Exception as e:
                self.error_signal.emit(self.camera_ip, str(e))
                time.sleep(5)  # Esperar antes de intentar nuevamente
            finally:
                if 'cap' in locals():
                    cap.release()

    def stop(self):
        self._run_flag = False
        self.wait()

class RTSPPlayer:
    def __init__(self, cameras):
        self.cameras = cameras
        self.recordings = {cam.ip: {'is_recording': False, 'process': None, 'start_time': None} for cam in cameras}
        self.recordings_dir = '/app/recordings'
        self.threads = {}
        self.onvif_cameras = {}

        callbacks = {
            'toggle_recording': self.toggle_recording,
            'start_move': self.start_move_camera,
            'stop_move': self.stop_move_camera,
            'update_cameras': self.update_cameras
        }
        self.ui = RTSPPlayerUI(cameras, callbacks)

        # Iniciar la configuración de cámaras de forma asíncrona
        self.setup_cameras_async()

    def setup_cameras_async(self):
        with ThreadPoolExecutor(max_workers=len(self.cameras)) as executor:
            future_to_camera = {executor.submit(self.setup_single_camera, cam): cam for cam in self.cameras}
            for future in as_completed(future_to_camera):
                camera = future_to_camera[future]
                try:
                    future.result()
                except Exception as e:
                    logging.error(f"Failed to setup camera {camera.ip}: {str(e)}")

    @retry_with_timeout(max_retries=3, delay=2, timeout=10)
    def setup_single_camera(self, camera):
        self.setup_onvif_camera(camera)
        self.start_camera_thread(camera)

    @retry_with_timeout(max_retries=3, delay=2, timeout=10)
    def setup_onvif_camera(self, camera):
        mycam = ONVIFCamera(camera.ip, camera.onvif_port, camera.user, camera.password, '/usr/local/lib/python3.8/dist-packages/wsdl/')
        media = mycam.create_media_service()
        ptz = mycam.create_ptz_service()
        media_profile = media.GetProfiles()[0]
        self.onvif_cameras[camera.ip] = {'camera': mycam, 'media': media, 'ptz': ptz, 'media_profile': media_profile}
        logging.info(f"ONVIF camera setup successful for {camera.ip}")

    def start_camera_thread(self, camera):
        thread = CameraThread(camera.rtsp_url, camera.ip)
        thread.change_pixmap_signal.connect(self.update_image)
        thread.error_signal.connect(self.handle_camera_error)
        self.threads[camera.ip] = thread
        thread.start()

    def update_cameras(self, new_cameras):
        logging.info("Iniciando actualización de cámaras")
        
        # Detener las conexiones existentes
        for thread in self.threads.values():
            thread.stop()
        
        # Esperar a que todos los hilos se detengan
        for thread in self.threads.values():
            thread.wait()
        
        # Limpiar las conexiones existentes
        self.threads.clear()
        self.onvif_cameras.clear()
        
        # Detener todas las grabaciones en curso
        for recording in self.recordings.values():
            if recording['is_recording']:
                recording['process'].terminate()
        
        # Actualizar la lista de cámaras
        self.cameras = new_cameras
        self.recordings = {cam.ip: {'is_recording': False, 'process': None, 'start_time': None} for cam in new_cameras}
        
        # Reiniciar las conexiones
        self.setup_cameras_async()
        
        # Actualizar la UI
        self.ui.update_cameras(self.cameras)
        
        logging.info("Actualización de cámaras completada")
        thread = CameraThread(camera.rtsp_url, camera.ip)
        thread.change_pixmap_signal.connect(self.update_image)
        thread.error_signal.connect(self.handle_camera_error)
        self.threads[camera.ip] = thread
        thread.start()

    def update_image(self, cv_img, camera_ip):
        qt_img = self.convert_cv_qt(cv_img)
        self.ui.update_image(qt_img, camera_ip)

    def convert_cv_qt(self, cv_img):
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
        
        camera = next(cam for cam in self.cameras if cam.ip == camera_ip)
        
        try:
            process = (
                ffmpeg
                .input(camera.rtsp_url, rtsp_transport='tcp')
                .output(filename, vcodec='libx264', crf='23', preset='medium', 
                        acodec='aac', audio_bitrate='128k',
                        f='mp4', movflags='faststart')
                .overwrite_output()
                .run_async(pipe_stdout=True, pipe_stderr=True)
            )

            self.recordings[camera_ip] = {
                'process': process,
                'is_recording': True,
                'start_time': time.time(),
                'filename': filename
            }
            self.ui.set_record_button_text(camera_ip, 'Detener Grabación')
            logging.info(f"Iniciando grabación para {camera_ip}: {filename}")

        except ffmpeg.Error as e:
            logging.error(f"Error al iniciar la grabación para {camera_ip}: {str(e)}")

    def stop_recording(self, camera_ip):
        if self.recordings[camera_ip]['is_recording']:
            process = self.recordings[camera_ip]['process']
            process.communicate()  # Espera a que el proceso termine
            self.recordings[camera_ip]['is_recording'] = False
            self.recordings[camera_ip]['process'] = None
            elapsed_time = time.time() - self.recordings[camera_ip]['start_time']
            file_size = os.path.getsize(self.recordings[camera_ip]['filename'])
            self.ui.set_record_button_text(camera_ip, 'Iniciar Grabación')
            logging.info(f"Grabación detenida para {camera_ip}. Duración: {elapsed_time:.2f} segundos. Tamaño del archivo: {file_size/1024/1024:.2f} MB")

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
        logging.error(f"Failed to stop moving camera {camera_ip}: {str(e)}")

    def handle_camera_error(self, camera_ip, error_message):
        logging.error(f"Camera error for {camera_ip}: {error_message}")
        # Aquí puedes implementar lógica adicional para manejar errores, como intentar reconectar la cámara

def main():
    app = QApplication(sys.argv)

    welcome = WelcomeScreen()
    if welcome.exec_() == QDialog.Rejected:
        sys.exit(0)

    # Obtener configuración
    cameras = get_camera_config()
    
    # Si no hay configuración, pedir al usuario que configure las cámaras
    if not cameras:
        config_dialog = ConfigDialog()
        if config_dialog.exec_() == QDialog.Rejected:
            sys.exit(0)
        cameras = get_camera_config()

    if not cameras:
        logging.error("No se pudo configurar ninguna cámara. Saliendo...")
        sys.exit(1)

    player = RTSPPlayer(cameras)
    player.ui.show()
    
    # Iniciar un temporizador para mostrar un mensaje de "Conectando..." después de un breve retraso
    QTimer.singleShot(100, lambda: player.ui.show_connecting_message())

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()