"""
Build123d script
================
Shape : Circular gear disc with triangular teeth + central rectangular boss
Outer : Ø 172.12 mm  ×  20 mm tall
Inner : Ø  63.92 mm  through-hole (centred)
Teeth : Isosceles triangle — sides 5.89 mm, base 8.44 mm
        Cut INTO the outer curved face, full 20 mm deep
Boss  : 24 mm × 9 mm rectangle, extruded 20 mm tall
        Centred at origin, inner edge aligned with the hole wall (Ø 63.92 mm)

Run inside VS Code with the OCP CAD Viewer extension open:

    python circle_with_cutout.py
"""

import math
import os
from build123d import *
from ocp_vscode import show_object, set_defaults, Camera

# ── Parameters ────────────────────────────────────────────────────────────────
OUTER_DIAMETER  = 172.12   # mm
HEIGHT          =  20.00   # mm
HOLE_DIAMETER   =  63.92   # mm

TOOTH_BASE      =   8.44   # mm
TOOTH_SIDE      =   5.89   # mm

BOSS_LENGTH     =  24.00   # mm  — rectangle long side
BOSS_WIDTH      =  12.00   # mm  — rectangle short side
BOSS_HEIGHT     =  20.00   # mm  — extrusion height

# ── Derived values ────────────────────────────────────────────────────────────
OUTER_RADIUS    = OUTER_DIAMETER / 2
HOLE_RADIUS     = HOLE_DIAMETER  / 2          # 31.96 mm

tooth_half_base = TOOTH_BASE / 2
tooth_height    = math.sqrt(TOOTH_SIDE**2 - tooth_half_base**2)

circumference   = math.pi * OUTER_DIAMETER
num_teeth       = int(circumference / TOOTH_BASE)
angular_step    = 360.0 / num_teeth

# Boss: centred at X=0, inner edge (min-Y face) sits on the hole wall.
# So the rectangle occupies:
#   X: -BOSS_LENGTH/2  →  +BOSS_LENGTH/2
#   Y: HOLE_RADIUS     →  HOLE_RADIUS + BOSS_WIDTH
boss_x_offset = 0
boss_y_offset = HOLE_RADIUS + BOSS_WIDTH / 2 - 10.9   # shifted 10.9 mm toward origin

print(f"Tooth height (depth of cut) : {tooth_height:.4f} mm")
print(f"Num teeth                   : {num_teeth}")
print(f"Boss Y centre               : {boss_y_offset:.4f} mm  (inner edge at Y={HOLE_RADIUS:.3f})")

# ── Base disc ─────────────────────────────────────────────────────────────────
with BuildPart() as disc:
    Cylinder(radius=OUTER_RADIUS, height=HEIGHT)
    Cylinder(radius=HOLE_RADIUS, height=HEIGHT, mode=Mode.SUBTRACT)

# ── Single tooth prism (extruded OUTWARD from outer face) ────────────────────
with BuildPart() as one_tooth:
    with BuildSketch(Plane.XY.offset(-HEIGHT / 2)):
        with BuildLine():
            Polyline(
                (OUTER_RADIUS,                 tooth_half_base),
                (OUTER_RADIUS,                -tooth_half_base),
                (OUTER_RADIUS + tooth_height,  0),
                (OUTER_RADIUS,                 tooth_half_base),
            )
        make_face()
    extrude(amount=HEIGHT)

tooth_template = one_tooth.part

# ── Gear: disc with teeth added outward (rotated 2.8° clockwise) ─────────────
TOOTH_OFFSET_ANGLE = -2.8   # degrees — negative = clockwise
with BuildPart() as gear:
    add(disc.part)
    for i in range(num_teeth):
        rotated = tooth_template.rotate(Axis.Z, i * angular_step + TOOTH_OFFSET_ANGLE)
        add(rotated, mode=Mode.ADD)

# ── Rectangular boss: 24 × 9 mm, extruded 20 mm ──────────────────────────────
# Inner edge aligned with the hole wall, centred left-right (X=0).
with BuildPart() as boss:
    with BuildSketch(Plane.XY.offset(-BOSS_HEIGHT / 2)):
        with Locations((boss_x_offset, boss_y_offset)):
            Rectangle(BOSS_LENGTH, BOSS_WIDTH)
    extrude(amount=BOSS_HEIGHT)

# ── Arc wedge: spans exactly 3 teeth, curve touches tooth tips ───────────────
# Arc radius = tooth tip radius so the concave curve grazes each tooth tip
ARC_RADIUS    = OUTER_RADIUS + tooth_height   # tooth tip radius (~90.17 mm)
ARC_HEIGHT    =  20.00   # mm

# Arc angle = exactly 3 tooth spacings
ARC_ANGLE     = 3 * angular_step              # 3 × 5.625° = 16.875°

# The arc is built symmetrically around +X, then rotated so its two straight
# edges point exactly at tooth tip 0 and tooth tip 3 on the gear.
# Tooth tips sit at angles: 0, angular_step, 2*angular_step, 3*angular_step ...
# We align edge 1 → tooth 0 (angle=0) and edge 2 → tooth 3 (angle=3*angular_step)
# so the arc centre sits at 1.5 * angular_step from +X.
arc_rotation  = 1.5 * angular_step            # rotate arc to straddle teeth 0-3

half_angle_rad = math.radians(ARC_ANGLE / 2)
p_start = (ARC_RADIUS * math.cos(-half_angle_rad), ARC_RADIUS * math.sin(-half_angle_rad))
p_end   = (ARC_RADIUS * math.cos( half_angle_rad), ARC_RADIUS * math.sin( half_angle_rad))

with BuildPart() as arc_wedge:
    with BuildSketch(Plane.XY.offset(-ARC_HEIGHT / 2)):
        with BuildLine():
            Line((0, 0), p_start)
            RadiusArc(p_start, p_end, -ARC_RADIUS)
            Line(p_end, (0, 0))
        make_face()
    extrude(amount=ARC_HEIGHT)

# Rotate the arc so its midpoint passes exactly through the -Y axis
# Arc is built around +X, so rotate -90° to centre it on -Y
arc_wedge_rotated = arc_wedge.part.rotate(Axis.Z, -90)

# ── Cut the arc wedge with a Ø88mm cylinder (only affects the arc) ───────────
CUT_CIRCLE_DIAMETER = 88.00   # mm
with BuildPart() as arc_cut:
    add(arc_wedge_rotated)
    Cylinder(radius=CUT_CIRCLE_DIAMETER / 2, height=ARC_HEIGHT, mode=Mode.SUBTRACT)

arc_result = arc_cut.part

# ── Combine everything into one body ─────────────────────────────────────────
with BuildPart() as final:
    add(gear.part)
    add(boss.part, mode=Mode.ADD)
    add(arc_result, mode=Mode.ADD)

result = final.part

# ── Sanity check ──────────────────────────────────────────────────────────────
print(f"Bounding box : {result.bounding_box()}")
print(f"Volume       : {result.volume:.2f} mm3")

# ── Circular ring: Ø173.2mm outer, Ø160mm inner, 20mm tall ──────────────────
RING_OUTER_DIAMETER = 172.80   # mm
RING_INNER_DIAMETER = 160.00   # mm

with BuildPart() as ring:
    Cylinder(radius=RING_OUTER_DIAMETER / 2, height=HEIGHT)
    Cylinder(radius=RING_INNER_DIAMETER / 2, height=HEIGHT, mode=Mode.SUBTRACT)

ring_result = ring.part

# ── Combine gear + ring into one body ────────────────────────────────────────
with BuildPart() as combined:
    add(result)
    add(ring_result, mode=Mode.ADD)

final_result = combined.part

print(f"Combined bounding box : {final_result.bounding_box()}")
print(f"Combined volume       : {final_result.volume:.2f} mm3")

# ── Display as one combined body in OCP CAD Viewer ───────────────────────────
set_defaults(reset_camera=Camera.RESET)
show_object(final_result, name=f"Gear+Boss+Arc+Ring  Ø{OUTER_DIAMETER} x {HEIGHT} mm  |  {num_teeth} teeth")

# ── Export to STEP file via popup dialog ─────────────────────────────────────
import tkinter as tk
from tkinter import filedialog, messagebox

root = tk.Tk()
root.withdraw()  # Hide the root window
root.lift()
root.attributes("-topmost", True)

export_path = filedialog.asksaveasfilename(
    title="Export STEP File",
    defaultextension=".step",
    initialfile="gear_model.step",
    initialdir=os.path.expanduser("~/Desktop"),
    filetypes=[("STEP Files", "*.step *.stp"), ("All Files", "*.*")]
)

if export_path:
    try:
        os.makedirs(os.path.dirname(os.path.abspath(export_path)), exist_ok=True)
        export_step(final_result, export_path)
        messagebox.showinfo("Export Successful", f"Model exported to:\n{export_path}")
        print(f"\n  ✓ Model exported to: {export_path}")
    except Exception as e:
        messagebox.showerror("Export Failed", f"Error: {e}")
        print(f"\n  ✗ Export failed: {e}")
else:
    print("\n  Export cancelled.")

root.destroy()