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

import os
import socket

from dynamixel_sdk import *


if os.name == 'nt':
    import msvcrt

    def getch():
        return msvcrt.getch().decode()
else:
    import sys, tty, termios

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    def getch():
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


def check(dxl_comm_result, dxl_error):
    if dxl_comm_result != COMM_SUCCESS:
        print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
    elif dxl_error != 0:
        print("%s" % packetHandler.getRxPacketError(dxl_error))


ADDR_TORQUE_ENABLE          = 64
ADDR_GOAL_POSITION          = 116
ADDR_PRESENT_POSITION       = 132
ADDR_GOAL_PWM               = 100
ADDR_OPERATING_MODE         = 11
ADDR_PROFILE_VELOCITY       = 112
ADDR_PROFILE_ACCELERATION   = 108
BAUDRATE                    = 115200

PROTOCOL_VERSION            = 2.0

# Update these IDs and the device name for the connected hardware.
DXL_IDs                      = [1, 2, 3, 4, 5, 6, 7, 8, 9]
DEVICENAME                  = 'COM9'

TORQUE_ENABLE               = 1
TORQUE_DISABLE              = 0
OPERATING_MODE_PWM          = 16
OPERATING_MODE_EXTENDED_POSITION = 4
LEN_GOAL_POSITION           = 4

dxl_goal_pwm = 100
dxl_zero_points = [0] * len(DXL_IDs)
PROFILE_VELOCITY = 0
PROFILE_ACCELERATION = 0


portHandler = PortHandler(DEVICENAME)
packetHandler = PacketHandler(PROTOCOL_VERSION)

if portHandler.openPort():
    print("Succeeded to open the port")
else:
    print("Failed to open the port")
    print("Press any key to terminate...")
    getch()
    quit()


if portHandler.setBaudRate(BAUDRATE):
    print("Succeeded to change the baudrate")
else:
    print("Failed to change the baudrate")
    print("Press any key to terminate...")
    getch()
    quit()

for id in DXL_IDs:
    dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, id, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
    check(dxl_comm_result, dxl_error)
    dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, id, ADDR_OPERATING_MODE, OPERATING_MODE_PWM)
    check(dxl_comm_result, dxl_error)
    dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, id, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)
    check(dxl_comm_result, dxl_error)
    dxl_comm_result, dxl_error = packetHandler.write2ByteTxRx(portHandler, id, ADDR_GOAL_PWM, dxl_goal_pwm)
    check(dxl_comm_result, dxl_error)

print("Press any key to set initial pose!")
getch()

for id in DXL_IDs:
    present_position, dxl_comm_result, dxl_error = packetHandler.read4ByteTxRx(portHandler, id, ADDR_PRESENT_POSITION)
    check(dxl_comm_result, dxl_error)
    print("ID:", id, "Present Position:", present_position)
    dxl_zero_points[id-1] = present_position

for id in DXL_IDs:
    dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, id, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
    check(dxl_comm_result, dxl_error)
    dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, id, ADDR_OPERATING_MODE, OPERATING_MODE_EXTENDED_POSITION)
    check(dxl_comm_result, dxl_error)
    dxl_comm_result, dxl_error = packetHandler.write4ByteTxRx(portHandler, id, ADDR_PROFILE_VELOCITY, PROFILE_VELOCITY)
    check(dxl_comm_result, dxl_error)
    dxl_comm_result, dxl_error = packetHandler.write4ByteTxRx(portHandler, id, ADDR_PROFILE_ACCELERATION, PROFILE_ACCELERATION)
    check(dxl_comm_result, dxl_error)
    dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, id, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)
    check(dxl_comm_result, dxl_error)

groupSyncWrite = GroupSyncWrite(
    portHandler,
    packetHandler,
    ADDR_GOAL_POSITION,
    LEN_GOAL_POSITION
)


def int32_to_uint32(val):
    return val & 0xFFFFFFFF

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(("127.0.0.1", 5005))
client_socket.setblocking(True)

print("Connected to server")

buffer = ""

try:
    while True:
        data = client_socket.recv(1024).decode("utf-8")
        if not data:
            break

        buffer += data

        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            poses = [int(v) for v in line.split(",")]

            groupSyncWrite.clearParam()
            for idx, (dxl_id, delta_pos) in enumerate(zip(DXL_IDs, poses)):
                pos_u32 = dxl_zero_points[idx] + delta_pos
                param_goal = [
                    DXL_LOBYTE(DXL_LOWORD(pos_u32)),
                    DXL_HIBYTE(DXL_LOWORD(pos_u32)),
                    DXL_LOBYTE(DXL_HIWORD(pos_u32)),
                    DXL_HIBYTE(DXL_HIWORD(pos_u32)),
                ]
                if not groupSyncWrite.addParam(dxl_id, param_goal):
                    raise RuntimeError(f"Failed to add param for ID {dxl_id}")
            dxl_comm_result = groupSyncWrite.txPacket()
            if dxl_comm_result != COMM_SUCCESS:
                print(packetHandler.getTxRxResult(dxl_comm_result))
except KeyboardInterrupt:
    print("\nKeyboard interrupt received, stopping...")

for id in DXL_IDs:
    dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, id, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
    check(dxl_comm_result, dxl_error)

portHandler.closePort()