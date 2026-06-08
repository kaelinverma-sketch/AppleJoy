"""
U-Channel Profile - Final (single combined body)
"""

from build123d import *
from ocp_vscode import show, show_all, set_defaults
import math

DEPTH     = 510
CUT_DEPTH = 17
CUT_Y     = 120
BOTTOM_Y  = CUT_Y - CUT_DEPTH  # 103
CUT_LEN   = 258
CUT_Z     = 96 + CUT_LEN / 2   # 225mm
FLOOR_Y   = 55 - 40 + 9.5 + 0.5  # 25mm

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

floor_chamfer_len = 38.75 / math.sqrt(2)

with BuildPart() as final_body:
    # ── Main U-channel ────────────────────────────────────────────────────────
    with BuildSketch(Plane.XY):
        with BuildLine():
            Polyline(*[Vector(x, y) for x, y in pts], close=True)
        make_face()
    extrude(amount=DEPTH)

    # Left extrude cut
    left_plane = Plane(origin=(left_x_mid, CUT_Y, CUT_Z), x_dir=(1,0,0), z_dir=(0,-1,0))
    with BuildSketch(left_plane):
        Rectangle(12, CUT_LEN)
    extrude(amount=CUT_DEPTH, mode=Mode.SUBTRACT)

    # Right extrude cut
    right_plane = Plane(origin=(right_x_mid, CUT_Y, CUT_Z), x_dir=(1,0,0), z_dir=(0,-1,0))
    with BuildSketch(right_plane):
        Rectangle(12, CUT_LEN)
    extrude(amount=CUT_DEPTH, mode=Mode.SUBTRACT)

    # Left body extrude cut
    left_body_plane = Plane(
        origin=(left_x_mid + 6 + 11.39/2, CUT_Y, CUT_Z),
        x_dir=(1, 0, 0), z_dir=(0, -1, 0),
    )
    with BuildSketch(left_body_plane):
        Rectangle(11.39, 331.76)
    extrude(amount=9, mode=Mode.SUBTRACT)

    # Right body extrude cut
    right_body_plane = Plane(
        origin=(right_x_mid - 6 - 11.39/2, CUT_Y, CUT_Z),
        x_dir=(1, 0, 0), z_dir=(0, -1, 0),
    )
    with BuildSketch(right_body_plane):
        Rectangle(11.39, 331.76)
    extrude(amount=9, mode=Mode.SUBTRACT)

    # Floor extrude cut
    floor_plane = Plane(
        origin=((12.89 + 326.89) / 2, FLOOR_Y, DEPTH / 2 + 5),
        x_dir=(1, 0, 0), z_dir=(0, 1, 0),
    )
    with BuildSketch(floor_plane):
        Rectangle(314, 380)
    extrude(amount=95, mode=Mode.SUBTRACT)

    # Chamfer on bottom width edges of left/right cuts
    cut_bottom_edges = final_body.edges().filter_by(
        lambda e: abs(e.length - 12) < 0.5 and abs(e.center().Y - BOTTOM_Y) < 0.5
    )
    chamfer(cut_bottom_edges, length=5.9, length2=5.9)  # 45deg, slant=~8.34mm (near max for 12mm cut)

    # Fillet on 510mm edges along Z at XZ plane face (Y=0)
    z_edges_y0 = final_body.edges().filter_by(
        lambda e: abs(e.length - DEPTH) < 0.5 and abs(e.center().Y) < 0.5
    )
    fillet(z_edges_y0, radius=20)

    # Chamfer on outer front face edges (Z=0), one at a time
    front_edge_lengths = [104.713, 104.918, 33.0, 33.56]
    for edge_len in front_edge_lengths:
        edges = final_body.edges().filter_by(
            lambda e, l=edge_len: abs(e.center().Z) < 0.5 and abs(e.length - l) < 0.1
        )
        if len(edges) > 0:
            try:
                chamfer(edges, length=12)
            except Exception as ex:
                print(f"Front chamfer failed for length={edge_len}: {ex}")

    # Chamfer on outer back face edges (Z=510), one at a time
    for edge_len in front_edge_lengths:
        edges = final_body.edges().filter_by(
            lambda e, l=edge_len: abs(e.center().Z - DEPTH) < 0.5 and abs(e.length - l) < 0.1
        )
        if len(edges) > 0:
            try:
                chamfer(edges, length=12)
            except Exception as ex:
                print(f"Back chamfer failed for length={edge_len}: {ex}")

    # Chamfer on floor cut opening edges
    floor_open_edges = final_body.edges().filter_by(
        lambda e: abs(e.length - 314) < 0.5 and abs(e.center().Y - FLOOR_Y) < 0.5
    )
    chamfer(floor_open_edges, length=floor_chamfer_len, length2=floor_chamfer_len)

    # Solid cylinder
    cyl_plane = Plane(origin=(169.03, 25, 310.45), x_dir=(1,0,0), z_dir=(0,1,0))
    with BuildSketch(cyl_plane):
        Circle(64.6 / 2)
    extrude(amount=86, mode=Mode.ADD)

    # Through hole from cylinder center (dia=35mm, all through in both Y directions)
    hole_plane = Plane(origin=(169.03, 0, 310.45), x_dir=(1,0,0), z_dir=(0,1,0))
    with BuildSketch(hole_plane):
        Circle(35 / 2)
    extrude(amount=500, both=True, mode=Mode.SUBTRACT)

    # Fillet on all inner edges along Z of main U-channel (at Y=55)
    inner_z_edges = final_body.edges().filter_by(
        lambda e: abs(e.center().Y - 55) < 0.5 and
                  (abs(e.center().X - 12.89) < 0.5 or abs(e.center().X - 326.89) < 0.5)
    )
    fillet(inner_z_edges, radius=12)

    # Fillet on floor cut edges along Z axis (325.199mm) and Y axis (38.750mm, 14.600mm)
    floor_cut_edges = final_body.edges().filter_by(
        lambda e: (abs(e.length - 325.199) < 0.5 or
                   abs(e.length - 38.750) < 0.5 or
                   abs(e.length - 14.600) < 0.5)
    )
    fillet(floor_cut_edges, radius=12)

    # Chamfer on inner circular cut edge (at Y=0)
    circular_edge = final_body.edges().filter_by(
        lambda e: abs(e.length - 109.956) < 0.5 and abs(e.center().Y) < 0.5
    )
    chamfer(circular_edge, length=5)

    # Triangular wedge
    with BuildSketch(Plane.YZ.offset(137.03)):
        with BuildLine():
            Polyline(
                Vector(25,        310.45 - 43 + 75),
                Vector(25,        310.45 + 43 + 75),
                Vector(25 + 86,   310.45 - 43 + 75),
                close=True
            )
        make_face()
    extrude(amount=64, mode=Mode.ADD)

    # Fillet on slant (hypotenuse) edges of wedge (~117.49mm long)
    wedge_hyp_edges = final_body.edges().filter_by(
        lambda e: abs(e.length - 117.486) < 0.5
    )
    try:
        fillet(wedge_hyp_edges, radius=15)
    except Exception:
        try:
            fillet(wedge_hyp_edges, radius=10)
        except Exception as ex:
            print(f"Wedge fillet failed: {ex}")

# ── Rectangle separate body ───────────────────────────────────────────────────
with BuildPart() as rect_body:
    rect_plane = Plane(
        origin=(137.03, 27 + 42 - 3, 310.45 + 32.3 - 16.2),
        x_dir=(0, 1, 0),
        z_dir=(1, 0, 0),
    )
    with BuildSketch(rect_plane):
        Rectangle(90, 32)
    extrude(amount=64)

    # Fillet on top 2 edges along Z (32mm, at Y=111)
    rect_bottom_edges = rect_body.edges().filter_by(
        lambda e: abs(e.length - 32) < 0.5 and abs(e.center().Y - 111) < 0.5
    )
    fillet(rect_bottom_edges, radius=20)

    # Through hole (dia=35mm) matching the one in final_body
    hole_plane_r = Plane(origin=(169.03, 0, 310.45), x_dir=(1,0,0), z_dir=(0,1,0))
    with BuildSketch(hole_plane_r):
        Circle(35 / 2)
    extrude(amount=500, both=True, mode=Mode.SUBTRACT)

# ── Single combined body ──────────────────────────────────────────────────────
combined = final_body.part + rect_body.part

# ── Move origin to bounding box minimum corner ───────────────────────────────
bb = combined.bounding_box()
combined = combined.moved(Location(Vector(-bb.min.X, -bb.min.Y, -bb.min.Z)))

# ── Export to STEP with file dialog ──────────────────────────────────────────
import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.withdraw()  # hide the root window
root.attributes('-topmost', True)
export_path = filedialog.asksaveasfilename(
    title="Save STEP file",
    defaultextension=".step",
    filetypes=[("STEP files", "*.step *.stp"), ("All files", "*.*")],
    initialfile="Apple_Joy_top.step"
)
root.destroy()

if export_path:
    export_step(combined, export_path)
    print(f"Model exported to: {export_path}")
else:
    print("Export cancelled.")

# ── Display in OCP CAD Viewer ─────────────────────────────────────────────────
set_defaults(axes=True, axes0=True, grid=(True, True, True))
show(combined)