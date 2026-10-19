from dataclasses import dataclass, field

from lerobot.cameras import CameraConfig
from lerobot.cameras.opencv import OpenCVCameraConfig
from lerobot.robots.config import RobotConfig

@RobotConfig.register_subclass("robot_soft_continum_9")
@dataclass
class ContinumRobotConfig(RobotConfig):
    port: str = "COM5"
    baudrate: int = 115200
    dxl_ids: list[int] = field(default_factory=lambda: [1,2,3,4,5,6,7,8,9])
    cameras: dict[str, CameraConfig] = None