# CoLI: A Reproducible Platform for Continuum Robot Learning via Monolithic 3D Printing and Isomorphic Teleoperation
This is the open source repository for <CoLI: A Reproducible Platform for Continuum Robot Learning via Monolithic 3D Printing and Isomorphic Teleoperation>.

CoLI is a reproducible, open-source platform for continuum robot learning, featuring a monolithic 3D-printable design and isomorphic leader–follower teleoperation. By combining accessible dual-material 3D printing, a tendon-driven continuum robot, and intuitive teleoperation without complex inverse-kinematics computation, CoLI lowers the barrier to building and condudting initation learning-driven tasks with continuum robots. The platform futher supports Lerobot ecosystem to offer an easier approach for learning-driven tasks.

To learn more about the paper, please visit:

[Paper: https://arxiv.org/abs/2606.20389](https://arxiv.org/abs/2606.20389)

[Website: https://tangrobot.github.io/CoLI-website/](https://tangrobot.github.io/CoLI-website/)


## Required Material

Here is the materials required of an leader robot or an follower robot.

| Category | Item | Quantity / Specification |
|---|---|---|
| 3D-Printed parts | `Continuum_robot` | 1 |
| 3D-Printed parts | `Base` | 1 |
| 3D-Printed parts | `Connection` | 1 |
| 3D-Printed parts | `Spool` | 9 |
| 3D-Printed parts | `End_effector` | 1 |
| Actuators | Dynamixel XC430-T240BB-T or XL330-M288-T servo | 9 |
| Actuators | Dynamixel U2D2 Hub | 1 |
| Actuators | Dynamixel PHB Set | 1 |
| Actuators | DC Power Supply | 1 (at least 5 A) |
| Tendons | Kevlar fiber tendon (1.5 mm diameter) | 3 × 30 cm, 3 × 45 cm, 3 × 60 cm |
| Pulleys | Pulley with bearing (U-shaped, Hole4 × 22 × 7 × 8 mm) | 9 |
| Screws | Double-ended screw and nut set (M3 × 14 mm, 4 mm outer diameter) | 9 |
| Screws | Flat-head screw (M4 × 18 mm) | 3 |
| Screws | Socket-head screw with lock nut (M2.5 × 10 mm) | 4 |
| Screws | Socket-head screw with lock nut (M2 × 10 mm) | 3 |

## 3D Printing Instruction

Please read the `README.md` file in each `CAD/XXX` fold and follow the instructions.

Overall, we recommend using the **Bambu Lab H2D 3D printer** (with dual 0.4 mm nozzles) to fabricate the continuum robot. We recommend using the provided `.3mf` files, which already include the printing profiles, to start your prints. Please follow the material types specified in each file.

You will need to prepare the following printing materials.

- One spool of PLA filament (Bambu Lab PLA Basic recommended).
- One spool of TPU 95A filament (Bambu Lab TPU 95A HF recommended).
- One spool of Bambu Lab PLA Tough+ (recommended for printing `Base` and `Connection`, substitutable with generic PLA).

## Assembly Instructions

Follow the steps below to assemble the continuum robot, including both the leader and follower robots.

1. **Install the pulleys.** Use double-ended screw and nut sets to mount the nine pulleys at the designated positions around the center of the base.

2. **Connect the base components.** Connect `base` and `connection` with M4 × 18 mm flat-head screw.

3. **Install the spools on the servos.** Use the screws supplied with the Dynamixel servos to attach one `spool` to each servo horn. Repeat this procedure for all nine servos.

4. **Mount the servos.** Use the screws supplied with the Dynamixel servos to secure all nine servos to `base`.

5. **Mount the continuum robot body.** Remove the support material from `continuum_robot`. Then, use M2.5 × 10 screws and lock nuts to attach the continuum robot body to the base through its four mounting holes.

6. **Route and secure the tendons.** Cut the tendons to suitable lengths. For each tendon, pass one end through the hole in the corresponding `spool` and secure it with a knot. Route the other end through the pulley and upward through the tendon-routing holes in the continuum robot. Finally, secure the tendon with a knot above the appropriate spacer disk.

   - The tendon routing configuration can be customized to suit your needs. However, **the tendon routing must be identical on the leader and follower robots**. Each corresponding tendon must also be connected to the same servo ID on both robots.

   - For the recommended tendon routing configuration, refer to **Sec. III-A** of the [paper](https://arxiv.org/abs/2606.20389).

7. Install `End_effector` at the tip of `Continuum_robot` with M2 × 10 screws and lock nuts.

8. **Connect the servos.** Use the cables supplied by Dynamixel to connect the servos in a daisy chain. Connect the chain to the power supply board and the U2D2 Hub. Ensure that the power supply is rated for a current of **more than 5 A**.

9. **Implement isomorphic teleoperation.** You can now implement isomorphic teleoperation based on the [Dynamixel SDK](https://docs.robotis.com/docs/software/dynamixel_sdk/) and the actuation principles described in **Sec. III-B** of the [paper](https://arxiv.org/abs/2606.20389). LeRobot-compatible code will be released soon.

## About This Project

If you encounter any issues during the fabrication or assembly process, feel free to raise them in the GitHub **Issues** section or contact us via email at [tangzy2026@shanghaitech.edu.cn](mailto:tangzy2026@shanghaitech.edu.cn).

If you successfully replicate our robot, we would love to hear from you and see your results!

This work was published at **IEEE/RSJ IROS 2026**. If you use our work in your research or publications, please cite:

```code
@misc{tang2026coli,
      title={CoLI: A Reproducible Platform for Continuum Robot Learning via Monolithic 3D Printing and Isomorphic Teleoperation}, 
      author={Ziyuan Tang and Chenxi Xiao},
      year={2026},
      eprint={2606.20389},
      archivePrefix={arXiv},
      primaryClass={cs.RO},
      url={https://arxiv.org/abs/2606.20389}, 
}
```
