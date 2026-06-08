# Apple Joy — Top Mating Part

Parametric CAD script generating the **top mating/cover shell** for the Apple Joy joystick enclosure. Built with [build123d](https://github.com/gumyr/build123d) and exported to STEP via a native file-save dialog.

---

## Overall Dimensions

| Dimension | Value | Notes |
|-----------|-------|-------|
| **Width (X)** | 360.56 mm | P1 (X=0) → P8 (X=339.89) + 20.67 mm mirror offset after repositioning |
| **Height (Y)** | 120 mm | Base (Y=0) → top flange (Y=120) |
| **Depth (Z)** | 510 mm | Full extrusion depth |
| **Wall thickness** | ~20.67 mm (left), ~20 mm (right) | Slanted outer flanges |
| **Inner floor width** | 314 mm | Between inner walls at X=12.89 and X=326.89 |
| **Inner floor height (Y)** | 25 mm | `FLOOR_Y = 55 − 40 + 9.5 + 0.5` |
| **Tab protrusion** | 17 mm | `CUT_DEPTH`, left and right side tabs |
| **Tab length (Z span)** | 258 mm | `CUT_LEN`, centred at Z=225 |
| **Central cylinder OD** | 64.6 mm | Boss at X=169.33, Y=111, Z=310 |
| **Central cylinder height** | 86 mm | Extruded in −Y direction |
| **Through-hole diameter** | 35 mm | Passes through boss and rect body, 101 mm deep |
| **Side cutout diameter** | 200 mm | Large circular pockets at X=59.33 and X=279.33 |
| **Wedge width (X)** | 64 mm | Triangular stiffener at X=137.33–201.33 |
| **Lip thickness** | 10 mm | Left and right overhanging lips at Y=120 |
| **Lip span (Z)** | 250 mm | Centred at Z=225 |

---

## Cross-Section Profile

The primary cross-section (XY plane) is an 8-point closed polygon approximating a U-channel with inward-sloping outer walls:

```
P1  (  0.00,   0)   ← bottom-left corner
P2  (-20.67, 120)   ← top-left outer flange
P3  ( 12.89, 120)   ← top-left inner shoulder
P4  ( 12.89,  55)   ← inner left wall foot
P5  (326.89,  55)   ← inner right wall foot
P6  (326.89, 120)   ← top-right inner shoulder
P7  (359.89, 120)   ← top-right outer flange
P8  (339.89,   0)   ← bottom-right corner
```

The inner floor sits at Y=25 mm. The outer flanges splay outward by ~20.67 mm on each side.

---

## File Structure

```
Apple_Joy_top_mating.step   ← STEP export (saved via dialog)
master_script.py            ← this script
README.md
```

---

## Methodology

### 1. Primary Shell — U-Channel Extrusion

A closed 8-point `Polyline` in the XY plane defines the U-channel cross-section. `make_face()` fills it and `extrude(amount=510)` produces the full-depth shell in a single `BuildPart` context (`final_body`).

### 2. Side Tabs (Additive)

Left and right rectangular tabs (12 × 258 mm, 17 mm proud) are added with `Mode.ADD` extrusions from planes oriented with `z_dir=(0,−1,0)` so the sketch lies flush with the outer wall face.

### 3. Body Cuts (Subtractive)

Stepped rectangular pockets (11.39 × 331.76 mm, 9 mm deep) relieve material just inboard of each tab — creating a shelf geometry. Built as `Mode.SUBTRACT` extrusions from offset planes.

### 4. Floor Pocket

A 314 × 380 mm rectangle is subtracted from a plane at `FLOOR_Y` (Y=25), cutting 95 mm inward from the Z-midpoint to form the hollow inner floor region.

### 5. Edge Treatments (Chamfers & Fillets)

All edge operations are applied to `final_body` in sequence after the primary geometry is complete. Edges are selected by axis, Y/X position filters, and lambda predicates on centroid and length:

| Feature | Type | Size | Selection method |
|---------|------|------|-----------------|
| Inner floor edge (X-axis) | Chamfer | 25 mm | `filter_by(Axis.X)` + Y=FLOOR_Y |
| Inner floor corners (Z-axis) | Fillet | 16 mm | Z-edges at Y=FLOOR_Y, X=12.89–326.89 |
| Chamfer angled Z-edges | Fillet | 16 mm | Z-edges between Y=0 and Y=FLOOR_Y |
| Slant (diagonal) edges | Fillet | 16 mm | Lambda: length≈510, 0<Y<FLOOR_Y |
| Inner wall-to-floor junction | Fillet | 16 mm | Z-edges at Y=55 |
| Outer flange floor Z-edges | Fillet | 16 mm | Z-edges at Y=FLOOR_Y, X=0–339.89 |
| Left/right lower corners | Fillet | 20 mm | Z-edges at Y≈0, X<5 or X>335 |
| Bottom long edges (front/back) | Chamfer | 12 mm | X-edges at Y≈0, Z≈0 or Z≈510, length>300 |
| Top long edges (front/back) | Chamfer | 12 mm | X-edges at Y=120, Z≈0 or Z≈510, length>300 |
| Wedge hypotenuse | Fillet | 20 mm | Lambda: length≈121.622 mm |

### 6. Central Boss & Through-Hole

A Ø64.6 mm cylinder (86 mm tall) is added at X=169.33, Y=111, Z=310 facing −Y. A coaxial Ø35 mm through-hole is subtracted 101 mm deep through both the boss and the rectangular body.

### 7. Large Side Cutouts

Two Ø200 mm circular pockets are subtracted 26 mm deep from the inner base at X=59.33 and X=279.33 (symmetric about centre), at Y=23 facing +Y.

### 8. Wedge Stiffener

A right-triangle profile (vertices at (Y=278,Z=25), (Y=192,Z=25), (Y=278,Z=111)) is sketched on a YZ plane offset to X=137.33 and extruded 64 mm in +X as a `Mode.ADD` solid.

### 9. Rectangular Body (`rect_body`)

A separate 90 × 32 mm rectangle is extruded 64 mm from a plane at the boss base (Y=66, Z=293.9), centred on X=137.33. The same Ø35 mm hole is subtracted through it. Z-edges at Y=111 receive a 23 mm fillet. This body is later union-combined with `final_body`.

### 10. Lip Bodies (`left_lip_body`, `right_lip_body`)

Two independent 250 × 10 mm slabs are extruded 10 mm from Y=120 on left and right flanges. Each receives a 9 mm chamfer on the top outer X-axis edge (at Y=130), giving a bevel on the outermost lip face.

### 11. Engraved Text

Five text solids are created with `Text()` + `extrude(amount=6)` and subtracted from the combined body:

| Label | Face | Position |
|-------|------|----------|
| `Apple  II` | Bottom (Y=0) | Z=38, centred X |
| `Y` | Bottom (Y=0) | Z=130, X=+90 offset |
| `X` | Bottom (Y=0) | Z=130, X=−90 offset |
| `Joystick` | Front (Z=510) | Z=450, centred X |

All bottom-face text uses `x_dir=(−1,0,0)` so it reads correctly when the part is flipped upside-down.

### 12. Boolean Combine & Mirror

```python
combined = final_body.part + rect_body.part
         + left_lip_body.part + right_lip_body.part
         - text_body.part - text_y_body.part
         - text_x_body.part - text_joystick_body.part
```

The combined solid is mirrored about `Plane.XZ` (flipping Y → −Y) to produce the mating counterpart. The result is repositioned so the top-left corner (originally X=−20.67, Y=0, Z=510) becomes the origin:

```python
mating_part = mating_part.moved(Location(Vector(20.67, 0, -510)))
```

### 13. STEP Export

A native Tk file-save dialog prompts for the output path. The final compound is written with `export_step()`.

---

## Dependencies

```
build123d
ocp_vscode   ≥ 3.4.0   (OCP CAD Viewer, port 3940)
tkinter                  (standard library — file dialog)
```

Install build123d:
```bash
pip install build123d
```

---

## Usage

```bash
python master_script.py
```

The script will:
1. Build all geometry
2. Open a file-save dialog — choose a destination for the `.step` file
3. Display the mating part in OCP CAD Viewer

---

## Key Parameters

```python
DEPTH     = 510      # overall Z depth (mm)
CUT_DEPTH = 17       # side tab protrusion (mm)
CUT_Y     = 120      # tab Y-plane (mm)
CUT_LEN   = 258      # tab Z-span (mm)
CUT_Z     = 225      # tab Z-centre (mm)
FLOOR_Y   = 25       # inner floor Y-level (mm)
```
