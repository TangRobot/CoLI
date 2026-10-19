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
import time
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

def disable_all_torque():
    print("Disabling all Dynamixel torque...")
    for id in DXL_IDs:
        dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(
            portHandler, id, ADDR_TORQUE_ENABLE, TORQUE_DISABLE
        )
        if dxl_comm_result != COMM_SUCCESS:
            print(packetHandler.getTxRxResult(dxl_comm_result))
        elif dxl_error != 0:
            print(packetHandler.getRxPacketError(dxl_error))

def check(dxl_comm_result, dxl_error):
    if dxl_comm_result != COMM_SUCCESS:
        print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
    elif dxl_error != 0:
        print("%s" % packetHandler.getRxPacketError(dxl_error))


ADDR_TORQUE_ENABLE          = 64
ADDR_PRESENT_POSITION       = 132
ADDR_GOAL_PWM               = 100
ADDR_OPERATING_MODE         = 11
BAUDRATE                    = 2000000

PROTOCOL_VERSION            = 2.0

# Update these IDs and the device name for the connected hardware.
DXL_IDs                     = [1, 2, 3, 4, 5, 6, 7, 8, 9]
DEVICENAME                  = 'COM8'

TORQUE_ENABLE               = 1
TORQUE_DISABLE              = 0
OPERATING_MODE_PWM          = 16
LEN_PRESENT_POSITION        = 4

dxl_goal_pwm = 100
dxl_zero_points = [0] * len(DXL_IDs)
dxl_rest_pwm = 100
DT = 1.0 / 30


def uint32_to_int32(val):
    if val >= 2**31:
        val -= 2**32
    return val 


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

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(("127.0.0.1", 5005))
server_socket.listen(1)

print("Waiting for replay connection...")
conn, addr = server_socket.accept()
print(f"Connected by {addr}")

for id in DXL_IDs:
    dxl_comm_result, dxl_error = packetHandler.write2ByteTxRx(portHandler, id, ADDR_GOAL_PWM, dxl_rest_pwm)
    check(dxl_comm_result, dxl_error)

groupSyncRead = GroupSyncRead(
    portHandler,
    packetHandler,
    ADDR_PRESENT_POSITION,
    LEN_PRESENT_POSITION
)

for dxl_id in DXL_IDs:
    if not groupSyncRead.addParam(dxl_id):
        raise RuntimeError(f"Failed to add ID {dxl_id}")


t0 = time.perf_counter()
next_frame_time = t0
frame = 0

try:
    while True:
        dxl_comm_result = groupSyncRead.txRxPacket()
        if dxl_comm_result != COMM_SUCCESS:
            print(packetHandler.getTxRxResult(dxl_comm_result))
            continue

        positions = []
        for i, dxl_id in enumerate(DXL_IDs):
            if not groupSyncRead.isAvailable(dxl_id, ADDR_PRESENT_POSITION, LEN_PRESENT_POSITION):
                positions.append(0)
            else:
                raw_pos = groupSyncRead.getData(dxl_id, ADDR_PRESENT_POSITION, 4)
                pos = uint32_to_int32(raw_pos)
                delta = pos - dxl_zero_points[i]
                positions.append(delta)

        msg = ",".join(str(p) for p in positions) + "\n"

        conn.sendall(msg.encode("utf-8"))

        frame += 1
        next_frame_time += DT
        sleep_time = next_frame_time - time.perf_counter()

        if sleep_time > 0:
            time.sleep(sleep_time)
        else:
            print(f"Frame {frame} overrun: {-sleep_time*1000:.2f} ms")

except (KeyboardInterrupt, BrokenPipeError, ConnectionResetError) as e:
    print(f"\nSocket or keyboard interrupt detected: {e}")

except Exception as e:
    print(f"\nUnexpected error: {e}")

finally:
    print("\n=== Cleaning up resources ===")

    try:
        conn.close()
        server_socket.close()
    except (NameError, OSError):
        print("Failed to close the socket cleanly.")

    disable_all_torque()

    try:
        portHandler.closePort()
    except (NameError, OSError):
        print("Failed to close the serial port cleanly.")

    print("Cleanup finished. Program exited safely.")