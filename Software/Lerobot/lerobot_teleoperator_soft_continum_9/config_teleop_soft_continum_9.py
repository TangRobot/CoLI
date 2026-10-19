from dataclasses import dataclass, field
from lerobot.teleoperators.config import TeleoperatorConfig

@TeleoperatorConfig.register_subclass("teleop_soft_continum_9")
@dataclass
class ContinumTeleopConfig(TeleoperatorConfig):
    port: str = "COM11"
    baudrate: int = 2000000
    dxl_ids: list[int] = field(default_factory=lambda: [1,2,3,4,5,6,7,8,9])