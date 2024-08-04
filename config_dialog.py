class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración de Cámaras")
        self.setGeometry(100, 100, 400, 300)
        self.camera_configs = []
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
        
        save_btn = QPushButton("Guardar Configuración")
        save_btn.clicked.connect(self.save_config)
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        layout.addWidget(add_camera_btn)
        layout.addWidget(save_btn)
        
        self.setLayout(layout)

    def add_camera_form(self):
        camera_number = len(self.camera_configs) + 1
        self.form_layout.addRow(QLabel(f"Cámara {camera_number}"))
        fields = ['IP', 'Puerto', 'Usuario', 'Contraseña']
        camera_config = {}
        for field in fields:
            line_edit = QLineEdit()
            self.form_layout.addRow(field, line_edit)
            camera_config[field.lower()] = line_edit
        self.camera_configs.append(camera_config)

    def load_existing_config(self):
        if os.path.exists('camera_config.json'):
            with open('camera_config.json', 'r') as f:
                configs = json.load(f)
            for config in configs:
                self.add_camera_form()
                for key, value in config.items():
                    self.camera_configs[-1][key].setText(str(value))

    def save_config(self):
        configs = []
        for camera_config in self.camera_configs:
            config = {key: widget.text() for key, widget in camera_config.items()}
            configs.append(config)
        
        with open('camera_config.json', 'w') as f:
            json.dump(configs, f)
        
        self.accept()

def get_camera_config():
    dialog = ConfigDialog()
    if dialog.exec_():
        with open('camera_config.json', 'r') as f:
            return json.load(f)
    return []