from build123d import *
from ocp_vscode import show, set_defaults
import math

# ── Parameters ───────────────────────────────────────────────────────────────
DEPTH      = 510
CUT_DEPTH  = 17
CUT_Y      = 120
CUT_LEN    = 258
CUT_Z      = 96 + CUT_LEN / 2   # 225mm
FLOOR_Y    = 55 - 40 + 9.5 + 0.5  # 25mm

# Profile points
pts = [
    (0,       0),       # P1
    (-20.67,  120),     # P2
    (12.89,   120),     # P3
    (12.89,   55),      # P4
    (326.89,  55),      # P5
    (326.89,  120),     # P6
    (359.89,  120),     # P7
    (339.89,  0),       # P8
]

left_x_mid  = (-20.67 + 12.89) / 2
right_x_mid = (326.89 + 359.89) / 2

with BuildPart() as final_body:
    # ── Main U-channel ───────────────────────────────────────────────────────
    with BuildSketch(Plane.XY):
        with BuildLine():
            Polyline(*[Vector(x, y) for x, y in pts], close=True)
        make_face()
    extrude(amount=DEPTH)

    # Left/Right tabs (Mode.ADD)
    left_plane = Plane(origin=(left_x_mid, CUT_Y, CUT_Z), x_dir=(1,0,0), z_dir=(0,-1,0))
    with BuildSketch(left_plane):
        Rectangle(12, CUT_LEN)
    extrude(amount=CUT_DEPTH, mode=Mode.ADD)

    right_plane = Plane(origin=(right_x_mid, CUT_Y, CUT_Z), x_dir=(1,0,0), z_dir=(0,-1,0))
    with BuildSketch(right_plane):
        Rectangle(12, CUT_LEN)
    extrude(amount=CUT_DEPTH, mode=Mode.ADD)

    # Body cuts
    left_body_plane = Plane(origin=(left_x_mid + 6 + 11.39/2, CUT_Y, CUT_Z), x_dir=(1, 0, 0), z_dir=(0, -1, 0))
    with BuildSketch(left_body_plane):
        Rectangle(11.39, 331.76)
    extrude(amount=9, mode=Mode.SUBTRACT)

    right_body_plane = Plane(origin=(right_x_mid - 6 - 11.39/2, CUT_Y, CUT_Z), x_dir=(1, 0, 0), z_dir=(0, -1, 0))
    with BuildSketch(right_body_plane):
        Rectangle(11.39, 331.76)
    extrude(amount=9, mode=Mode.SUBTRACT)

    # Floor cut
    floor_plane = Plane(origin=((12.89 + 326.89) / 2, FLOOR_Y, DEPTH / 2 + 5), x_dir=(1, 0, 0), z_dir=(0, 1, 0))
    with BuildSketch(floor_plane):
        Rectangle(314, 380)
    extrude(amount=95, mode=Mode.SUBTRACT)

    # ── Floor cut inner edge chamfer (Maximized to 25mm) ─────────────────────
    floor_edges = final_body.edges().filter_by(Axis.X).filter_by_position(Axis.Y, FLOOR_Y, FLOOR_Y)
    if floor_edges:
        chamfer(floor_edges, length=25)

    # ── Fillet on inner floor cut edges along Z axis (16mm) ──────────────────
    floor_z_edges = final_body.edges().filter_by(Axis.Z).filter_by_position(Axis.Y, FLOOR_Y, FLOOR_Y).filter_by_position(
        Axis.X, 12.89, 326.89
    )
    if floor_z_edges:
        fillet(floor_z_edges, radius=16)

    # ── Fillet on chamfer angled face Z edges (between Y=0 and Y=FLOOR_Y) ────
    chamfer_z_edges = final_body.edges().filter_by(Axis.Z).filter_by_position(
        Axis.Y, 0, FLOOR_Y, inclusive=(False, False)
    ).filter_by_position(Axis.X, 12.89, 326.89)
    if chamfer_z_edges:
        fillet(chamfer_z_edges, radius=16)

    # ── Fillet on slant (diagonal) edges of chamfer face — full depth 510mm ──
    slant_edges = final_body.edges().filter_by(
        lambda e: abs(e.length - DEPTH) < 0.5 and
                  0 < e.center().Y < FLOOR_Y and
                  12.89 < e.center().X < 326.89
    )
    if slant_edges:
        fillet(slant_edges, radius=16)

    # ── Fillet on inner U-channel wall edges along Z at Y=55 (floor-to-wall junction) ──
    wall_z_edges = final_body.edges().filter_by(Axis.Z).filter_by_position(Axis.Y, 55, 55).filter_by_position(
        Axis.X, 12.89, 326.89
    )
    if wall_z_edges:
        fillet(wall_z_edges, radius=16)

    # ── Mirrored fillets on outer flanges at X=0 and X=339.89 ────────────────
    outer_floor_z_edges = final_body.edges().filter_by(Axis.Z).filter_by_position(Axis.Y, FLOOR_Y, FLOOR_Y).filter_by_position(
        Axis.X, 0, 339.89
    )
    if outer_floor_z_edges:
        fillet(outer_floor_z_edges, radius=16)

    # outer_wall_z_edges at Y=55 removed — no suitable edges on outer flange

    # ── Fillet on outer lower edges along Z at Y=0 — left corner (X~0) ───────
    left_lower_z_edges = final_body.edges().filter_by(Axis.Z).filter_by(
        lambda e: abs(e.center().Y) < 1.0 and e.center().X < 5
    )
    if left_lower_z_edges:
        fillet(left_lower_z_edges, radius=20)

    # ── Fillet on outer lower edges along Z at Y=0 — right corner (X~339.89) ─
    right_lower_z_edges = final_body.edges().filter_by(Axis.Z).filter_by(
        lambda e: abs(e.center().Y) < 1.0 and e.center().X > 335
    )
    if right_lower_z_edges:
        fillet(right_lower_z_edges, radius=20)

    # inner_lower_z_edges at Y=0 removed — edges consumed by the 25mm chamfer

    # ── Chamfer on front/back X-axis edges of bottom face (Y=0, Z=0 and Z=510) — long edges only ──
    bottom_x_edges = final_body.edges().filter_by(Axis.X).filter_by(
        lambda e: abs(e.center().Y) < 1.0 and
                  (abs(e.center().Z) < 1.0 or abs(e.center().Z - DEPTH) < 1.0) and
                  e.length > 300
    )
    if bottom_x_edges:
        chamfer(bottom_x_edges, length=12)

    # ── Chamfer on front/back X-axis edges of top face (Y=120, Z=0 and Z=510) — long edges only ──
    top_x_edges = final_body.edges().filter_by(Axis.X).filter_by(
        lambda e: abs(e.center().Y - CUT_Y) < 1.0 and
                  (abs(e.center().Z) < 1.0 or abs(e.center().Z - DEPTH) < 1.0) and
                  e.length > 300
    )
    if top_x_edges:
        chamfer(top_x_edges, length=12)



    # Cylinder — x=190 from new origin (build space x=169.33), z=310
    cyl_plane = Plane(origin=(169.33, 111, 310), x_dir=(1,0,0), z_dir=(0,-1,0))
    with BuildSketch(cyl_plane):
        Circle(64.6 / 2)
    extrude(amount=86, mode=Mode.ADD)

    # Through hole — Ø35mm from Y=111, -Y direction, 101mm depth
    hole_plane = Plane(origin=(169.33, 111, 310), x_dir=(1,0,0), z_dir=(0,-1,0))
    with BuildSketch(hole_plane):
        Circle(35 / 2)
    extrude(amount=101, mode=Mode.SUBTRACT)

    # Large cylinder cuts
    for x_pos in [59.33, 279.33]:
        large_cyl_plane = Plane(origin=(x_pos, 23, 112), x_dir=(1,0,0), z_dir=(0,1,0))
        with BuildSketch(large_cyl_plane):
            Circle(200 / 2)
        extrude(amount=26, mode=Mode.SUBTRACT)

    # Wedge
    with BuildSketch(Plane.YZ.offset(169.33 - 32)):
        with BuildLine():
            Polyline(Vector(25, 278), Vector(25, 192), Vector(111, 278), close=True)
        make_face()
    extrude(amount=64, mode=Mode.ADD)

    # ── Fillet on wedge hypotenuse edges — 20mm radius ───────────────────────
    wedge_hyp_edges = final_body.edges().filter_by(
        lambda e: abs(e.length - 121.622) < 1.0
    )
    if wedge_hyp_edges:
        fillet(wedge_hyp_edges, radius=20)

# ── Rectangle separate body ───────────────────────────────────────────────────
with BuildPart() as rect_body:
    rect_plane = Plane(origin=(169.33 - 32, 66, 293.9), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
    with BuildSketch(rect_plane):
        Rectangle(90, 32)
    extrude(amount=64)

    # Matching hole in rect body
    hole_plane_r = Plane(origin=(169.33, 111, 310), x_dir=(1,0,0), z_dir=(0,-1,0))
    with BuildSketch(hole_plane_r):
        Circle(35 / 2)
    extrude(amount=101, mode=Mode.SUBTRACT)

    # ── Fillet on rectangle body edges — 25mm radius ──────────────────────────
    rect_edges = rect_body.edges().filter_by(Axis.Z).filter_by(
        lambda e: abs(e.center().Y - 111) < 1.0
    )
    if rect_edges:
        fillet(rect_edges, radius=23)

# ── Lip bodies with 5mm chamfer on top outer 10mm edge ───────────────────────
with BuildPart() as left_lip_body:
    left_lip_plane = Plane(origin=(-3.67, 120, 225), x_dir=(0,0,1), z_dir=(0,1,0))
    with BuildSketch(left_lip_plane):
        Rectangle(250, 10)
    extrude(amount=10)

    # 9mm chamfer on top outer 10mm edge along X axis (Y=130)
    left_lip_chamfer_edges = left_lip_body.edges().filter_by(Axis.X).filter_by_position(Axis.Y, 130, 130)
    if left_lip_chamfer_edges:
        chamfer(left_lip_chamfer_edges, length=9)

with BuildPart() as right_lip_body:
    right_lip_plane = Plane(origin=(342.0, 120, 225), x_dir=(0,0,1), z_dir=(0,1,0))
    with BuildSketch(right_lip_plane):
        Rectangle(250, 10)
    extrude(amount=10)

    # 9mm chamfer on top outer 10mm edge along X axis (Y=130)
    right_lip_chamfer_edges = right_lip_body.edges().filter_by(Axis.X).filter_by_position(Axis.Y, 130, 130)
    if right_lip_chamfer_edges:
        chamfer(right_lip_chamfer_edges, length=9)

# ── Engraved text "Apple II" on bottom face (Y=0, parallel to XZ plane) ──────
# Rotated 180° and moved 150mm in -Z direction
with BuildPart() as text_body:
    text_plane = Plane(origin=(169.33, 0, 228 - 150 - 30 - 5 + 15), x_dir=(-1,0,0), z_dir=(0,1,0))
    with BuildSketch(text_plane):
        Text("Apple  II", font_size=60, align=(Align.CENTER, Align.CENTER))
    extrude(amount=6)

# ── Engraved "Y" above "A" (left side of Apple II) ───────────────────────────
with BuildPart() as text_y_body:
    text_y_plane = Plane(origin=(169.33 + 90, 0, 228 - 150 - 30 - 5 + 15 + 60 + 32), x_dir=(-1,0,0), z_dir=(0,1,0))
    with BuildSketch(text_y_plane):
        Text("Y", font_size=60, align=(Align.CENTER, Align.CENTER))
    extrude(amount=6)

# ── Engraved "X" above "II" (right side of Apple II) ─────────────────────────
with BuildPart() as text_x_body:
    text_x_plane = Plane(origin=(169.33 - 90, 0, 228 - 150 - 30 - 5 + 15 + 60 + 32), x_dir=(-1,0,0), z_dir=(0,1,0))
    with BuildSketch(text_x_plane):
        Text("X", font_size=60, align=(Align.CENTER, Align.CENTER))
    extrude(amount=6)

# ── Engraved text "Joystick" on front face (Z=0) ─────────────────────────────
with BuildPart() as text_joystick_body:
    text_joystick_plane = Plane(origin=(169.33, 0, 20 + 400 + 30), x_dir=(1,0,0), z_dir=(0,1,0))
    with BuildSketch(text_joystick_plane):
        Text("Joystick", font_size=60, align=(Align.CENTER, Align.CENTER))
    extrude(amount=6)
combined = final_body.part + rect_body.part + left_lip_body.part + right_lip_body.part - text_body.part - text_y_body.part - text_x_body.part - text_joystick_body.part

# ── Mirror and Final Positioning ─────────────────────────────────────────────
mating_part = mirror(combined, about=Plane.XZ)

# Shift origin: Top corner (originally X=-20.67, Y=0, Z=510) becomes (0,0,0)
mating_part = mating_part.moved(Location(Vector(20.67, 0, -510)))

# ── Export to STEP with file dialog ──────────────────────────────────────────
import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.withdraw()
root.attributes('-topmost', True)
export_path = filedialog.asksaveasfilename(
    title="Save STEP file",
    defaultextension=".step",
    filetypes=[("STEP files", "*.step *.stp"), ("All files", "*.*")],
    initialfile="Apple_Joy_top_mating.step"
)
root.destroy()

if export_path:
    export_step(mating_part, export_path)
    print(f"Mating part exported to: {export_path}")
else:
    print("Export cancelled.")

# ── Display ───────────────────────────────────────────────────────────────────
set_defaults(axes=True, axes0=True, grid=(True, True, True))
show(mating_part)
