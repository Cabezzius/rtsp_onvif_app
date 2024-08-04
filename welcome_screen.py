from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QTextEdit

class WelcomeScreen(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bienvenido a la App de Cámaras IP")
        self.setGeometry(100, 100, 600, 400)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        welcome_text = QLabel("Bienvenido a la Aplicación de Cámaras IP")
        welcome_text.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(welcome_text)

        description = QTextEdit()
        description.setReadOnly(True)
        description.setHtml("""
        <p>Esta aplicación te permite visualizar y controlar cámaras IP utilizando los protocolos RTSP y ONVIF.</p>
        <p><b>Funcionalidades principales:</b></p>
        <ul>
            <li>Visualización en tiempo real de múltiples cámaras IP</li>
            <li>Control de movimiento PTZ (Pan, Tilt, Zoom) para cámaras compatibles</li>
            <li>Grabación de video de alta calidad</li>
        </ul>
        <p><b>Datos necesarios para configurar una cámara:</b></p>
        <ul>
            <li>Dirección IP de la cámara</li>
            <li>Puerto RTSP (generalmente 554)</li>
            <li>Puerto ONVIF (generalmente 80 o 8080)</li>
            <li>Nombre de usuario</li>
            <li>Contraseña</li>
        </ul>
        <p>Estos datos los puedes encontrar en la documentación de tu cámara o en la interfaz de configuración del fabricante.</p>
        """)
        layout.addWidget(description)

        start_button = QPushButton("Comenzar")
        start_button.clicked.connect(self.accept)
        layout.addWidget(start_button)

        self.setLayout(layout)