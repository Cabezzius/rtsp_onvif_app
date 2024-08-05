from typing import Dict, Any
import logging

class Camera:
    def __init__(self, ip: str = "", rtsp_port: int = 554, onvif_port: int = 80, user: str = "", password: str = "", rtsp_url: str = None):
        self.ip = ip
        self.rtsp_port = rtsp_port
        self.onvif_port = onvif_port
        self.user = user
        self.password = password
        self._rtsp_url = rtsp_url

    @property
    def rtsp_url(self) -> str:
        if self._rtsp_url:
            return self._rtsp_url
        return f"rtsp://{self.user}:{self.password}@{self.ip}:{self.rtsp_port}/live/ch0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'ip': self.ip,
            'rtsp_port': self.rtsp_port,
            'onvif_port': self.onvif_port,
            'user': self.user,
            'password': self.password,
            'rtsp_url': self._rtsp_url
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Camera':
        try:
            return cls(
                ip=data.get('ip', ''),
                rtsp_port=int(data.get('rtsp_port', 554)),
                onvif_port=int(data.get('onvif_port', 80)),
                user=data.get('user', ''),
                password=data.get('password', ''),
                rtsp_url=data.get('rtsp_url')
            )
        except ValueError as e:
            logging.error(f"Error creating Camera object from dict: {e}")
            raise

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Camera):
            return False
        return (self.ip == other.ip and
                self.rtsp_port == other.rtsp_port and
                self.onvif_port == other.onvif_port and
                self.user == other.user and
                self.password == other.password and
                self._rtsp_url == other._rtsp_url)

    def __str__(self) -> str:
        return f"Camera(ip={self.ip}, rtsp_port={self.rtsp_port}, onvif_port={self.onvif_port})"

    def __repr__(self) -> str:
        return self.__str__()