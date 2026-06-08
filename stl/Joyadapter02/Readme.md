# Apple Joy — Top Body

Parametric CAD script generating the **primary top shell** of the Apple Joy joystick enclosure. Built with [build123d](https://github.com/gumyr/build123d) and exported to STEP via a native file-save dialog. The final body is translated so its bounding-box minimum corner sits at the world origin before export.

---

## Overall Dimensions

| Dimension | Value | Notes |
|-----------|-------|-------|
| **Width (X)** | ~380.56 mm | P1 (X=0) to P7 (X=359.89) + 20.67 mm left flange overhang |
| **Height (Y)** | 120 mm | Base (Y=0) → top flange (Y=120) |
| **Depth (Z)** | 510 mm | Full extrusion depth |
| **Left flange overhang** | 20.67 mm | Slant from X=0 to X=−20.67 |
| **Right flange overhang** | 20 mm | Slant from X=339.89 to X=359.89 |
| **Inner floor width** | 314 mm | Between inner walls at X=12.89 and X=326.89 |
| **Inner floor Y-level** | 25 mm | `FLOOR_Y = 55 − 40 + 9.5 + 0.5` |
| **Tab notch depth** | 17 mm | `CUT_DEPTH` — material removed from top face |
| **Tab notch bottom Y** | 103 mm | `BOTTOM_Y = CUT_Y − CUT_DEPTH` |
| **Tab notch width (X)** | 12 mm | Left and right slots |
| **Tab notch Z-span** | 258 mm | `CUT_LEN`, centred at Z=225 |
| **Body relief width (X)** | 11.39 mm | Stepped pocket inboard of each tab |
| **Body relief Z-span** | 331.76 mm | Centred at Z=225 |
| **Body relief depth** | 9 mm | Into top face |
| **Central cylinder OD** | 64.6 mm | Boss at X=169.03, Y=25, Z=310.45 |
| **Central cylinder height** | 86 mm | Extruded in +Y |
| **Through-hole diameter** | 35 mm | Full bilateral pass-through in Y |
| **Wedge base (Y-span)** | 86 mm | Triangular stiffener depth in Y |
| **Wedge X-width** | 64 mm | Extruded in +X from X=137.03 |
| **Rect body footprint** | 90 × 32 mm | YZ face, 64 mm in X |

> **Note:** Final exported geometry is translated so the bounding-box minimum corner is at (0, 0, 0). Stated coordinates above are pre-translation build-space values.

---

## Cross-Section Profile

The primary cross-section (XY plane) is an 8-point closed polygon:

```
P1  (  0.00,   0)   ← bottom-left corner
P2  (-20.67, 120)   ← top-left outer flange tip
P3  ( 12.89, 120)   ← top-left inner shoulder
P4  ( 12.89,  55)   ← inner left wall foot
P5  (326.89,  55)   ← inner right wall foot
P6  (326.89, 120)   ← top-right inner shoulder
P7  (359.89, 120)   ← top-right outer flange tip
P8  (339.89,   0)   ← bottom-right corner
```

The flanges splay outward ~20 mm on each side. The inner U-channel floor sits at Y=55; the secondary floor cut brings usable floor depth down to Y=25.

---

## File Structure

```
Apple_Joy_top.step      ← STEP export (saved via dialog)
master_script.py        ← this script
README.md
```

---

## Methodology

### 1. Primary Shell — U-Channel Extrusion

A closed 8-point `Polyline` in the XY plane is filled with `make_face()` and extruded 510 mm in +Z to produce the full-depth U-channel shell inside a single `BuildPart` context (`final_body`).

### 2. Tab Notch Cuts (Subtractive)

12 × 258 mm rectangular slots are subtracted from the top face (Y=120) at the left and right mid-flange positions, 17 mm deep, using planes oriented with `z_dir=(0,−1,0)`. These form the interlocking tab recesses.

### 3. Body Relief Cuts (Subtractive)

Stepped 11.39 × 331.76 mm pockets are subtracted 9 mm deep just inboard of each tab notch — widening the notch channel to accept the mating part's tab wall.

### 4. Floor Pocket

A 314 × 380 mm rectangle is subtracted 95 mm deep from a plane at `FLOOR_Y` (Y=25), hollowing out the inner base region between the two inner walls.

### 5. Edge Treatments

All chamfers and fillets are applied sequentially within `final_body` after primary geometry is stable. Edges are selected by lambda predicates on length, centroid Y, and centroid X/Z:

| Feature | Type | Size | Selection |
|---------|------|------|-----------|
| Tab notch bottom width edges | Chamfer | 5.9 × 5.9 mm (45°) | length≈12, Y=103 |
| Outer Z-edges at Y=0 (bottom corners) | Fillet | 20 mm | length≈510, Y≈0 |
| Front face (Z=0) edges | Chamfer | 12 mm | Z≈0, lengths: 104.713, 104.918, 33.0, 33.56 mm |
| Back face (Z=510) edges | Chamfer | 12 mm | Z≈510, same four lengths |
| Floor pocket opening edges (X-axis, 314 mm) | Chamfer | 27.38 × 27.38 mm (45°) | length≈314, Y=FLOOR_Y |
| Inner wall-to-ledge junctions (Z-axis at Y=55) | Fillet | 12 mm | Y≈55, X≈12.89 or X≈326.89 |
| Floor cut Z-edges (325.199 mm) and short edges | Fillet | 12 mm | lengths ≈325.199, 38.750, 14.600 mm |
| Circular hole edge at Y=0 | Chamfer | 5 mm | length≈109.956, Y≈0 |
| Wedge hypotenuse edges (~117.49 mm) | Fillet | 15 mm (fallback 10 mm) | length≈117.486 mm |

Front/back face chamfers are applied one length at a time in a `try/except` loop to handle cases where the OCC kernel cannot resolve multiple simultaneous chamfer operations on adjacent edges.

### 6. Central Boss & Through-Hole

A Ø64.6 mm cylinder (86 mm tall) is added at X=169.03, Y=25, Z=310.45 facing +Y. A coaxial Ø35 mm hole is subtracted bilaterally (`both=True`, 500 mm total) to pass fully through the shell in both Y directions.

### 7. Triangular Wedge Stiffener

A right-triangle profile is sketched on a YZ plane offset to X=137.03:

```
Vertices (Y, Z):
  (25,  342.45)   ← lower-left
  (25,  428.45)   ← upper-left
  (111, 342.45)   ← lower-right
```

Extruded 64 mm in +X as `Mode.ADD`. The hypotenuse edges (~117.49 mm) are then filleted at 15 mm radius (with automatic fallback to 10 mm on OCC failure).

### 8. Rectangular Body (`rect_body`)

A separate `BuildPart` builds a 90 × 32 mm slab (64 mm in X) flush with the boss base, positioned at Y≈66, Z≈326.55. Two Z-axis edges at Y=111 receive a 20 mm fillet. The same Ø35 mm bilateral hole is subtracted to maintain coaxial alignment with the boss.

### 9. Boolean Combine & Origin Normalisation

```python
combined = final_body.part + rect_body.part
```

The bounding box minimum corner is computed and the combined solid is translated to place that corner at the world origin:

```python
bb = combined.bounding_box()
combined = combined.moved(Location(Vector(-bb.min.X, -bb.min.Y, -bb.min.Z)))
```

### 10. STEP Export

A native Tk file-save dialog prompts for the output path. The combined solid is written with `export_step()`.

---

## Key Parameters

```python
DEPTH     = 510      # overall Z depth (mm)
CUT_DEPTH = 17       # tab notch depth from top face (mm)
CUT_Y     = 120      # top face Y-level (mm)
BOTTOM_Y  = 103      # tab notch floor Y = CUT_Y - CUT_DEPTH
CUT_LEN   = 258      # tab notch Z-span (mm)
CUT_Z     = 225      # tab notch Z-centre (mm)
FLOOR_Y   = 25       # inner floor Y-level (mm)

floor_chamfer_len = 38.75 / sqrt(2)  # ≈27.38 mm — 45° chamfer on 38.75 mm stock
```

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
2. Translate the combined body to origin
3. Open a file-save dialog — choose a destination for the `.step` file
4. Display the result in OCP CAD Viewer

---

## Relationship to Mating Part

This script produces the **top (main) body**. The companion `Apple_Joy_top_mating.py` script produces a mirrored counterpart with additive tabs where this part has subtractive notches. The two parts interlock along the tab/notch interface at Y=103–120 on both left and right flanges.
