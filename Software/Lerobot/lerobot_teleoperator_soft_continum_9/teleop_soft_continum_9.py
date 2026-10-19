#*******************************************************************************
# Copyright 2017 ROBOTIS CO., LTD.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#*******************************************************************************

# Some code is derived from Dynamixel SDK (by ROBOTIS CO., LTD.) and may have been modified.

import logging
import time
from lerobot.utils.errors import DeviceAlreadyConnectedError, DeviceNotConnectedError
from typing import Any
from lerobot.teleoperators.teleoperator import Teleoperator
from msvcrt import getch
from dynamixel_sdk import *

from .config_teleop_soft_continum_9 import ContinumTeleopConfig

logger = logging.getLogger(__name__)

def uint32_to_int32(val):
    if val >= 2**31:
        val -= 2**32
    return val 

class ContinumTeleop(Teleoperator):
    config_class = ContinumTeleopConfig
    name = "ContinumTeleop"

    def __init__(self, config: ContinumTeleopConfig):
        super().__init__(config)
        self.config = config
        self.port = config.port
        self.baudrate = config.baudrate
        self.dxl_ids = config.dxl_ids

        # ===== Dynamixel protocol constants =====
        self.ADDR_TORQUE_ENABLE = 64
        self.ADDR_OPERATING_MODE = 11
        self.ADDR_PROFILE_VELOCITY = 112
        self.ADDR_PROFILE_ACCELERATION = 108
        self.ADDR_GOAL_POSITION = 116
        self.ADDR_PRESENT_POSITION = 132
        self.ADDR_GOAL_PWM = 100

        self.LEN_GOAL_POSITION = 4
        self.LEN_PRESENT_POSITION = 4
        self.TORQUE_ENABLE = 1
        self.TORQUE_DISABLE = 0
        self.OPERATING_MODE_EXTENDED_POSITION = 4
        self.OPERATING_MODE_PWM = 16
        self.PROFILE_VELOCITY = 100
        self.PROFILE_ACCELERATION = 30

        # ===== shared state =====
        self._is_connected = False
        self._is_calibrated = False
        self.dxl_zero = [0] * len(self.dxl_ids)

        # ===== background threads =====
        self.prev_pose = {f"joint{dxl_id}.pos": 0 for dxl_id in self.dxl_ids}
    
    @property
    def action_features(self) -> dict[str, type]:
        return {f"joint{dxl_id}.pos": float for dxl_id in self.dxl_ids}
    @property
    def feedback_features(self) -> dict[str, type]:
        return {}

    @property
    def is_connected(self) -> bool:
        return self._is_connected
    
    @property
    def is_calibrated(self) -> bool:
        return self._is_calibrated
    
    def connect(self) -> None:
        if self.is_connected:
            raise DeviceAlreadyConnectedError(f"{self} already connected")
        
        self.portHandler = PortHandler(self.port)
        self.packetHandler = PacketHandler(2.0)
        
        if not self.portHandler.openPort():
            raise RuntimeError(f"Failed to open port {self.port}")

        if not self.portHandler.setBaudRate(self.baudrate):
            raise RuntimeError(f"Failed to set baud rate {self.baudrate}")

        logger.info(f"Dynamixel port opened: {self.port} @ {self.baudrate} bps")

        # Initialize GroupSyncRead for reading present positions
        self.groupSyncRead = GroupSyncRead(
            self.portHandler,
            self.packetHandler,
            self.ADDR_PRESENT_POSITION,
            self.LEN_PRESENT_POSITION
        )
        for dxl_id in self.dxl_ids:
            if not self.groupSyncRead.addParam(dxl_id):
                logger.error(f"Failed to add ID {dxl_id} to GroupSyncRead")
        
        logger.info("Robot connected.")

        self.calibrate()
        self.configure()

        logger.info("Robot initialized.")
        self._is_connected = True
        return
    
    def calibrate(self) -> None:
        # Disable torque and configure all motors
        for dxl_id in self.dxl_ids:
            self.packetHandler.write1ByteTxRx(self.portHandler, dxl_id, self.ADDR_TORQUE_ENABLE, self.TORQUE_DISABLE)
        
        # Set operating mode to PWM Control
        for dxl_id in self.dxl_ids:
            self.packetHandler.write1ByteTxRx(self.portHandler, dxl_id, self.ADDR_OPERATING_MODE, self.OPERATING_MODE_PWM)
        
        for dxl_id in self.dxl_ids:
            self.packetHandler.write1ByteTxRx(self.portHandler, dxl_id, self.ADDR_TORQUE_ENABLE, self.TORQUE_ENABLE)

        for dxl_id in self.dxl_ids:
            self.packetHandler.write2ByteTxRx(self.portHandler, dxl_id, self.ADDR_GOAL_PWM, 200)

        print("Press any key to set initial pose for teleoprator!")
        getch()
        
        for i, dxl_id in enumerate(self.dxl_ids):
            pos, dxl_comm_result, dxl_error = self.packetHandler.read4ByteTxRx(self.portHandler, dxl_id, self.ADDR_PRESENT_POSITION)
            if dxl_comm_result != COMM_SUCCESS:
                logger.error(f"Failed to read zero position from ID {dxl_id}")
                self.dxl_zero[i] = 0
            else:
                self.dxl_zero[i] = pos
            logger.info(f"Motor ID {dxl_id} zero position: {self.dxl_zero[i]}")
        
        self._is_calibrated = True
        logger.info("Robot calibrated.")
        self._is_calibrated = True
        return
    
    def configure(self) -> None:

        for dxl_id in self.dxl_ids:
            self.packetHandler.write1ByteTxRx(self.portHandler, dxl_id, self.ADDR_TORQUE_ENABLE, self.TORQUE_DISABLE)
            self.packetHandler.write1ByteTxRx(self.portHandler, dxl_id, self.ADDR_OPERATING_MODE, self.OPERATING_MODE_PWM)
            self.packetHandler.write1ByteTxRx(self.portHandler, dxl_id, self.ADDR_TORQUE_ENABLE, self.TORQUE_ENABLE)
            self.packetHandler.write2ByteTxRx(self.portHandler, dxl_id, self.ADDR_GOAL_PWM, 200)
        
        logger.info("Robot configured.")
        return
    
    def setup_motors(self) -> None:
        return

    def get_action(self) -> dict[str, float]:
        start = time.perf_counter()
        action = self._get_dynamixel_positions()
        dt_ms = (time.perf_counter() - start) * 1e3
        logger.debug(f"{self} read action: {dt_ms:.1f}ms")
        return action

    def send_feedback(self, feedback: dict[str, float]) -> None:
        # TODO(rcadene, aliberts): Implement force feedback
        raise NotImplementedError

    def disconnect(self) -> None:
        if not self.is_connected:
            DeviceNotConnectedError(f"{self} is not connected.")

        """Clean up resources and close hardware connections."""
        logger.info("Closing robot...")
        
        # Disable torque on all motors
        try:
            for dxl_id in self.dxl_ids:
                self.packetHandler.write1ByteTxRx(self.portHandler, dxl_id, self.ADDR_TORQUE_ENABLE, self.TORQUE_DISABLE)
        except Exception as e:
            logger.error(f"Error disabling torque: {e}")
        
        # Close port
        try:
            self.portHandler.closePort()
        except Exception as e:
            logger.error(f"Error closing port: {e}")
        
        self._is_connected = False
        logger.info("Robot closed")
        return

    # --------------------------------------------------
    # Internal helpers
    # --------------------------------------------------
    def _get_dynamixel_positions(self) -> list[int]:
        """Read present positions from all Dynamixel motors."""
        dxl_comm_result = self.groupSyncRead.txRxPacket()
        if dxl_comm_result != COMM_SUCCESS:
            logger.error(f"Failed to read positions of teleop: {self.packetHandler.getTxRxResult(dxl_comm_result)}")
            return [0] * len(self.dxl_ids)
        
        obs_dict = {}
        for i, dxl_id in enumerate(self.dxl_ids):
            raw_data = self.groupSyncRead.getData(dxl_id, self.ADDR_PRESENT_POSITION, self.LEN_PRESENT_POSITION)
            data = uint32_to_int32(raw_data)
            obs_dict[f"joint{dxl_id}.pos"] = data - self.dxl_zero[i]
        
        return obs_dict