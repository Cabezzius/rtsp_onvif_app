from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSizePolicy, QGridLayout
from PyQt5.QtCore import Qt
from functools import partial
from config_dialog import get_camera_config
from camera import Camera

class RTSPPlayerUI(QMainWindow):
    def __init__(self, cameras, callbacks):
        super().__init__()
        self.cameras = cameras
        self.callbacks = callbacks
        self.video_labels = {}
        self.record_buttons = {}
        self.initUI()

    def initUI(self):
        self.setWindowTitle('RTSP Player')
        self.setGeometry(100, 100, 1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)

        self.update_cameras(self.cameras)

    def update_cameras(self, cameras):
        # Limpiar la UI existente
        for i in reversed(range(self.main_layout.count())): 
            widget = self.main_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        self.cameras = cameras
        self.video_labels = {}
        self.record_buttons = {}
        
        grid_layout = QGridLayout()
        for i, cam in enumerate(self.cameras):
            video_label = QLabel(self)
            video_label.setAlignment(Qt.AlignCenter)
            video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            video_label.setMinimumSize(400, 300)
            self.video_labels[cam.ip] = video_label
            grid_layout.addWidget(video_label, i // 2, i % 2)

        self.main_layout.addLayout(grid_layout, 3)

        controls_layout = QHBoxLayout()
        for cam in self.cameras:
            cam_layout = QVBoxLayout()
            ip_label = QLabel(cam.ip)
            cam_layout.addWidget(ip_label)

            record_btn = self.create_button('Iniciar Grabación', partial(self.callbacks['toggle_recording'], cam.ip))
            cam_layout.addWidget(record_btn)
            self.record_buttons[cam.ip] = record_btn

            movement_layout = QGridLayout()
            directions = [('▲', 'Arriba', 0, 1), ('◄', 'Izquierda', 1, 0), ('►', 'Derecha', 1, 2), ('▼', 'Abajo', 2, 1)]
            for symbol, direction, row, col in directions:
                btn = self.create_button(symbol, partial(self.callbacks['start_move'], cam.ip, direction), partial(self.callbacks['stop_move'], cam.ip))
                movement_layout.addWidget(btn, row, col)

            cam_layout.addLayout(movement_layout)
            controls_layout.addLayout(cam_layout)

        self.main_layout.addLayout(controls_layout, 1)

        # Añadir botón de configuración
        config_btn = QPushButton("Configurar Cámaras")
        config_btn.clicked.connect(self.open_config_dialog)
        self.main_layout.addWidget(config_btn)

    def create_button(self, text, pressed_callback, released_callback=None):
        btn = QPushButton(text)
        btn.setMaximumSize(50, 50)  # Hacer los botones más pequeños
        btn.pressed.connect(pressed_callback)
        if released_callback:
            btn.released.connect(released_callback)
        return btn

    def update_image(self, pixmap, camera_ip):
        if camera_ip in self.video_labels:
            self.video_labels[camera_ip].setPixmap(pixmap)
        else:
            logging.warning(f"No label found for camera {camera_ip}")

    def set_record_button_text(self, camera_ip, text):
        if camera_ip in self.record_buttons:
            self.record_buttons[camera_ip].setText(text)
        else:
            logging.warning(f"No record button found for camera {camera_ip}")

    def open_config_dialog(self):
        try:
            new_config = get_camera_config()
            if new_config:
                if 'update_cameras' in self.callbacks:
                    self.callbacks['update_cameras'](new_config)
                else:
                    logging.error("update_cameras callback not found")
        except Exception as e:
            logging.error(f"Error in open_config_dialog: {str(e)}")
            QMessageBox.critical(self, "Error", f"Se produjo un error al configurar las cámaras: {str(e)}")

    def show_connecting_message(self):
        for label in self.video_labels.values():
            label.setText("Conectando...")
            label.setAlignment(Qt.AlignCenter)