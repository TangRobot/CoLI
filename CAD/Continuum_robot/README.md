### Required 3D Printer

We recommend using the **Bambu Lab H2D 3D printer with dual 0.4 mm nozzles** to print this model. The printing process has only been validated on this 3D printer. In principle, other dual-nozzle or multi-nozzle 3D printers may also be suitable, but printer-specific settings may be required.

**We strongly advise against using a single-nozzle printer with an automatic filament-switching system** to print this model, as this will significantly increase printing time and filament waste while making the printing process less reliable.

### Required Filaments

Printing this model requires:

- One spool of PLA filament (Bambu Lab PLA Basic recommended).
- One spool of TPU 95A filament (Bambu Lab TPU 95A HF recommended).

Before printing, ensure that both filaments are thoroughly dried. Calibrate the flow ratio using the method recommended for your printer.

### Preparing for Printing

Before starting the print, clean the build plate thoroughly to ensure optimal adhesion. If the printed parts detach from the build plate during printing, we recommend applying a glue stick or using another adhesion-enhancing method recommended by your printer manufacturer.

If possible, run your 3D printer's calibration routines.

### Recommended Printing Method: `.3mf` Files

We recommend printing the continuum robot using the provided `.3mf` file, which already contains the printing parameters.

1. Open the `.3mf` file in Bambu Studio.
2. Connect your printer and synchronize the printer settings.
3. Slice the model and send the print job to your printer.

### Alternative Printing Method: `.stl` Files

If you prefer to print using the `.stl` files, follow these steps:

1. Import all `.stl` files in the folder into your slicer simultaneously. Select the option to import them as a single assembly.
2. Select the bottom surface of a spacer disk with four mounting holes as the build-plate-facing surface.
3. Configure the printing parameters as follows:
   - **Spacer disks:** PLA, 8 wall loops, 25% infill.
   - **Flexible backbone:** TPU, 30 wall loops.
4. Enable **Tree Supports (Auto)** globally and set the support material to PLA.
5. Enable the prime tower.