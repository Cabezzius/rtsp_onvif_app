from PyQt5.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QLabel, QScrollArea, QWidget, QMessageBox, QHBoxLayout
from camera import Camera
import json
import logging

class ConfigDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Configuración de Cámaras")
        self.setGeometry(100, 100, 400, 300)
        self.cameras = []
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        self.form_layout = QFormLayout(scroll_content)
        
        self.load_existing_config()
        
        add_camera_btn = QPushButton("Añadir Cámara")
        add_camera_btn.clicked.connect(self.add_camera_form)
        
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Guardar Configuración")
        save_btn.clicked.connect(self.save_config)
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(close_btn)
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        layout.addWidget(add_camera_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

    def add_camera_form(self, camera=None):
        camera_number = len(self.cameras) + 1
        self.form_layout.addRow(QLabel(f"Cámara {camera_number}"))
        camera_form = {}
        fields = [
            ('IP', 'ip', ''),
            ('Puerto RTSP', 'rtsp_port', '554'),
            ('Puerto ONVIF', 'onvif_port', '80'),
            ('Usuario', 'user', ''),
            ('Contraseña', 'password', '')
        ]
        for label, attr, placeholder in fields:
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(placeholder)
            if camera:
                line_edit.setText(str(getattr(camera, attr)))
            self.form_layout.addRow(label, line_edit)
            camera_form[attr] = line_edit
        self.cameras.append(camera_form)

    def load_existing_config(self):
        try:
            with open('camera_config.json', 'r') as f:
                configs = json.load(f)
            for config in configs:
                camera = Camera.from_dict(config)
                self.add_camera_form(camera)
        except FileNotFoundError:
            # Si no hay configuración existente, añadir un formulario vacío
            self.add_camera_form()

    def save_config(self):
        configs = []
        for camera_form in self.cameras:
            config = {attr: widget.text() for attr, widget in camera_form.items()}
            if config['ip']:  # Solo guardar si al menos la IP está especificada
                camera = Camera.from_dict(config)
                configs.append(camera.to_dict())
        
        if configs:
            with open('camera_config.json', 'w') as f:
                json.dump(configs, f)
            self.accept()
        else:
            QMessageBox.warning(self, "Configuración inválida", "Por favor, especifica al menos una cámara con una dirección IP.")

def get_camera_config():
    try:
        dialog = ConfigDialog()
        result = dialog.exec_()
        if result == QDialog.Accepted:
            with open('camera_config.json', 'r') as f:
                configs = json.load(f)
            return [Camera.from_dict(config) for config in configs]
        else:
            logging.info("Configuración cancelada por el usuario")
            return None
    except Exception as e:
        logging.error(f"Error al obtener la configuración de las cámaras: {str(e)}")
        return None