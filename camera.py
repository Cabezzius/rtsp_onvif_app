class Camera:
    def __init__(self, ip="", rtsp_port=554, onvif_port=80, user="", password=""):
        self.ip = ip
        self.rtsp_port = rtsp_port
        self.onvif_port = onvif_port
        self.user = user
        self.password = password

    @property
    def rtsp_url(self):
        return f"rtsp://{self.user}:{self.password}@{self.ip}:{self.rtsp_port}/live/ch0"

    def to_dict(self):
        return {
            'ip': self.ip,
            'rtsp_port': self.rtsp_port,
            'onvif_port': self.onvif_port,
            'user': self.user,
            'password': self.password
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            ip=data.get('ip', ''),
            rtsp_port=int(data.get('rtsp_port', 554)),
            onvif_port=int(data.get('onvif_port', 80)),
            user=data.get('user', ''),
            password=data.get('password', '')
        )
    def __eq__(self, other):
        if not isinstance(other, Camera):
            return False
        return (self.ip == other.ip and
                self.rtsp_port == other.rtsp_port and
                self.onvif_port == other.onvif_port and
                self.user == other.user and
                self.password == other.password)