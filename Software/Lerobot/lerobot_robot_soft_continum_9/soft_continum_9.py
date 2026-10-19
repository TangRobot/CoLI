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
from typing import Any
from dynamixel_sdk import *
from msvcrt import getch
from functools import cached_property

from lerobot.robots import robot
import numpy as np

from lerobot.cameras import make_cameras_from_configs
from lerobot.utils.errors import DeviceNotConnectedError, DeviceAlreadyConnectedError
from lerobot.robots.robot import Robot

from .config_soft_continum_9 import ContinumRobotConfig

logger = logging.getLogger(__name__)

def uint32_to_int32(val):
    if val >= 2**31:
        val -= 2**32
    return val 

class ContinumRobot(Robot):
    config_class = ContinumRobotConfig
    name = "ContinumRobot"

    def __init__(self, config: ContinumRobotConfig):
        super().__init__(config)
        self.cameras = make_cameras_from_configs(config.cameras)
        # ===== parameters =====
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

        self.LEN_GOAL_POSITION = 4
        self.TORQUE_ENABLE = 1
        self.TORQUE_DISABLE = 0
        self.OPERATING_MODE_EXTENDED_POSITION = 4
        self.OPERATING_MODE_PWM = 16
        self.PROFILE_VELOCITY = 100
        self.PROFILE_ACCELERATION = 30
        self.ADDR_GOAL_PWM = 100

        # ===== shared state =====
        self._is_connected = False
        self._is_calibrated = False
        self.dxl_zero = [0] * len(self.dxl_ids)

        # ===== background threads =====
        self.prev_pose = {f"joint{dxl_id}.pos": 0 for dxl_id in self.dxl_ids}
    

    # --------------------------------------------------
    # Specs required by LeRobot
    # --------------------------------------------------

    @property
    def _cameras_ft(self) -> dict[str, tuple]:
        return {
            cam: (self.config.cameras[cam].height, self.config.cameras[cam].width, 3) for cam in self.cameras
        }
    
    @property
    def _motors_ft(self) -> dict[str, type]:
        return {f"joint{dxl_id}.pos": float for dxl_id in self.dxl_ids}

    @cached_property
    def action_features(self) -> dict[str, type | tuple]:
        return self._motors_ft

    @cached_property
    def observation_features(self) -> dict[str, type]:
        return {**self._motors_ft, **self._cameras_ft}

    # --------------------------------------------------
    # LeRobot lifecycle
    # --------------------------------------------------
    @property
    def is_connected(self) -> bool:
        return self._is_connected
    
    @property
    def is_calibrated(self) -> bool:
        return self._is_calibrated
    
    def connect(self) -> None:
        for cam in self.cameras.values():
            cam.connect()
        
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
            self.LEN_GOAL_POSITION
        )

        for dxl_id in self.dxl_ids:
            if not self.groupSyncRead.addParam(dxl_id):
                logger.error(f"Failed to add ID {dxl_id} to GroupSyncRead")

        # Initialize GroupSyncWrite for sending goal positions
        self.groupSyncWrite = GroupSyncWrite(
            self.portHandler,
            self.packetHandler,
            self.ADDR_GOAL_POSITION,
            self.LEN_GOAL_POSITION
        )
        
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
            self.packetHandler.write1ByteTxRx(self.portHandler, dxl_id, self.ADDR_OPERATING_MODE, self.OPERATING_MODE_PWM)
            self.packetHandler.write1ByteTxRx(self.portHandler, dxl_id, self.ADDR_TORQUE_ENABLE, self.TORQUE_ENABLE)
            self.packetHandler.write2ByteTxRx(self.portHandler, dxl_id, self.ADDR_GOAL_PWM, 100)

        print("Press any key to set initial pose for robot!")
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
        for dxl_id in self.dxl_ids:
            self.packetHandler.write1ByteTxRx(self.portHandler, dxl_id, self.ADDR_OPERATING_MODE, self.OPERATING_MODE_EXTENDED_POSITION)
            self.packetHandler.write4ByteTxRx(self.portHandler, dxl_id, self.ADDR_PROFILE_VELOCITY, self.PROFILE_VELOCITY)
            self.packetHandler.write4ByteTxRx(self.portHandler, dxl_id, self.ADDR_PROFILE_ACCELERATION, self.PROFILE_ACCELERATION)
        for dxl_id in self.dxl_ids:
            self.packetHandler.write1ByteTxRx(self.portHandler, dxl_id, self.ADDR_TORQUE_ENABLE, self.TORQUE_ENABLE)
        
        logger.info("Robot configured.")
        return

    def reset(self):
        """Called at the beginning of each episode"""
        self.prev_pose[:] = 0
        return self.get_observation()
    
    def reboot(self):
        for dxl_id in self.dxl_ids:
            self.packetHandler.reboot(self.portHandler, dxl_id)
        time.sleep(5.0)
        logger.info("All motors rebooted.")
        self.configure()
        return

    def get_observation(self) -> dict[str, Any]:
        start = time.perf_counter()
        obs_dict = self._get_dynamixel_positions()
        dt_ms = (time.perf_counter() - start) * 1e3
        logger.debug(f"{self} read state: {dt_ms:.1f}ms")

        for cam_key, cam in self.cameras.items():
            start = time.perf_counter()
            obs_dict[cam_key] = cam.async_read()
            dt_ms = (time.perf_counter() - start) * 1e3
            logger.debug(f"{self} read {cam_key}: {dt_ms:.1f}ms")
        return obs_dict
    
    def send_action(self, action: dict[str, Any]) -> dict[str, Any]:
        pose = [0] * len(self.dxl_ids)
        for i, dxl_id in enumerate(self.dxl_ids):
            key = f"joint{dxl_id}.pos"
            if key in action:
                pose[i] = int(action[key])
        self.prev_pose = pose

        self.groupSyncWrite.clearParam()
        for i, dxl_id in enumerate(self.dxl_ids):
            pos = pose[i] + self.dxl_zero[i]
            param = [
                DXL_LOBYTE(DXL_LOWORD(pos)),
                DXL_HIBYTE(DXL_LOWORD(pos)),
                DXL_LOBYTE(DXL_HIWORD(pos)),
                DXL_HIBYTE(DXL_HIWORD(pos)),
            ]
            add_param_result = self.groupSyncWrite.addParam(dxl_id, param)
            if not add_param_result:
                raise RuntimeError(f"Failed to add param for Dynamixel ID {dxl_id}")

        dxl_comm_result = self.groupSyncWrite.txPacket()
        if dxl_comm_result != COMM_SUCCESS:
            raise RuntimeError(f"GroupSyncWrite failed: {self.packetHandler.getTxRxResult(dxl_comm_result)}")

        return action

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
        
        for cam in self.cameras.values():
            cam.disconnect()
        
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
            logger.error(f"Failed to read positions: {self.packetHandler.getTxRxResult(dxl_comm_result)}")
            return [0] * len(self.dxl_ids)
        
        obs_dict = {}
        for i, dxl_id in enumerate(self.dxl_ids):
            raw_data = self.groupSyncRead.getData(dxl_id, self.ADDR_PRESENT_POSITION, self.LEN_GOAL_POSITION)
            data = uint32_to_int32(raw_data)
            obs_dict[f"joint{dxl_id}.pos"] = data - self.dxl_zero[i]
        
        return obs_dict