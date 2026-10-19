Files here provide direct motion mapping from the leader robot to the follower robot.

To use this feature:

1. Configure the port, baud rate, and servo IDs in `leader_M288.py` and `Follower_T240.py`.
1. Run program `leader_M288.py` and complete the calibration procedure.
2. Run program `Follower_T240.py` and complete the calibration procedure.
3. Motion mapping between the leader and follower robots will begin automatically.

For the calibration procedure, you need to do the following steps:

1. Print the calibration sleeve model provided in `CAD/Calibrator`.
2. Before running the program, use the calibration sleeve to keep the robot in an upright position.
3. Run the program and wait for the tendons to tighten.
4. Remove the calibration sleeve and manually adjust any spacer disks that are not in their desired positions. Please ensure that all tendons are routed correctly, especially at the pulley.
5. Follow the command-line instructions and press the confirmation key when prompted.