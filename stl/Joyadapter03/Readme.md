# Gear Disc — Circular Gear with Triangular Teeth, Boss & Arc Wedge

Parametric CAD script generating a **circular gear disc** with triangular teeth cut into the outer face, a rectangular alignment boss, a trimmed arc wedge, and a concentric outer ring. Built with [build123d](https://github.com/gumyr/build123d) and exported to STEP via a native file-save dialog.

---

## Overall Dimensions

| Dimension | Value | Notes |
|-----------|-------|-------|
| **Outer diameter (disc)** | 172.12 mm | Before teeth |
| **Tooth tip diameter** | ~180.34 mm | Disc OD + 2 × tooth height (~4.11 mm each side) |
| **Height** | 20 mm | Uniform across all features |
| **Through-hole diameter** | 63.92 mm | Centred at origin |
| **Tooth base** | 8.44 mm | Arc length per tooth on outer face |
| **Tooth side length** | 5.89 mm | Isosceles triangle leg |
| **Tooth height (radial depth)** | ~4.11 mm | Derived: `sqrt(5.89² − 4.22²)` |
| **Number of teeth** | 64 | `int(π × 172.12 / 8.44)` |
| **Angular step** | 5.625° | 360° / 64 teeth |
| **Boss length (X)** | 24 mm | Long axis |
| **Boss width (Y)** | 12 mm | Short axis |
| **Boss height** | 20 mm | Flush with disc faces |
| **Boss Y-centre offset** | ~21.06 mm | `HOLE_RADIUS + BOSS_WIDTH/2 − 10.9` |
| **Arc wedge span** | 16.875° | 3 × angular step |
| **Arc wedge radius** | ~90.17 mm | Tooth tip radius |
| **Arc inner cut diameter** | 88 mm | Cylinder subtracted from arc wedge |
| **Ring outer diameter** | 172.80 mm | Concentric with disc |
| **Ring inner diameter** | 160.00 mm | Ring wall = 6.4 mm |
| **Ring height** | 20 mm | Flush with disc faces |

---

## Geometry Overview

```
                    ┌── arc wedge (3-tooth span, −Y side)
                    │
  ┌─────────────────┼──────────────────┐
  │   outer ring    │    gear disc     │  ← 20 mm tall, all coplanar
  │  Ø172.8/Ø160   │   Ø172.12        │
  │                 │  + 64 teeth      │
  │           ┌─────┴─────┐           │
  │           │  Ø63.92   │           │
  │           │  through  │           │
  │           │   hole    │           │
  │           └─────┬─────┘           │
  │                 │                  │
  │            boss (24×9mm,          │
  │             +Y direction)         │
  └─────────────────┼──────────────────┘
```

---

## File Structure

```
gear_model.step             ← STEP export (saved via dialog, default ~/Desktop)
circle_with_cutout.py       ← this script
README.md
```

---

## Methodology

### 1. Base Disc

A solid `Cylinder` at radius 86.06 mm (Ø172.12 mm), 20 mm tall, is created. A coaxial `Cylinder` at radius 31.96 mm (Ø63.92 mm) is subtracted in `Mode.SUBTRACT` to produce the annular disc.

### 2. Tooth Geometry — Derived Values

Tooth dimensions are derived analytically from the isosceles triangle parameters:

```python
tooth_half_base = TOOTH_BASE / 2              # 4.22 mm
tooth_height    = sqrt(TOOTH_SIDE² − tooth_half_base²)   # ≈ 4.11 mm
circumference   = π × OUTER_DIAMETER         # ≈ 540.9 mm
num_teeth       = int(circumference / TOOTH_BASE)         # 64
angular_step    = 360° / num_teeth            # 5.625°
```

### 3. Single Tooth Template

One triangular prism is built in a separate `BuildPart` (`one_tooth`). The triangle profile is sketched at the outer radius in the XY plane:

```
Vertices:
  (OUTER_RADIUS,  +TOOTH_BASE/2)   ← base left
  (OUTER_RADIUS,  −TOOTH_BASE/2)   ← base right
  (OUTER_RADIUS + tooth_height, 0) ← tip (pointing outward)
```

The face is extruded 20 mm in +Z to create a full-height prism. This single solid is reused as a rotation template — no geometry is rebuilt per tooth.

### 4. Gear Assembly — Rotational Instancing

The tooth template is rotated about Z for each of the 64 tooth positions using a fixed `TOOTH_OFFSET_ANGLE` of −2.8° (clockwise phase shift). Each rotated tooth solid is added to a new `BuildPart` (`gear`) in `Mode.ADD`:

```python
for i in range(num_teeth):
    rotated = tooth_template.rotate(Axis.Z, i * angular_step + TOOTH_OFFSET_ANGLE)
    add(rotated, mode=Mode.ADD)
```

Teeth protrude **outward** from the disc face; no subtraction is performed.

### 5. Rectangular Boss

A 24 × 12 mm rectangle is sketched on a plane offset to `−BOSS_HEIGHT/2` in Z (so the boss is centred on the XY mid-plane, matching the disc). It is centred at X=0 and offset in Y by `HOLE_RADIUS + BOSS_WIDTH/2 − 10.9 ≈ 21.06 mm`, positioning it just inside the hole wall on the +Y side. The sketch is extruded 20 mm in +Z in a separate `BuildPart` (`boss`).

### 6. Arc Wedge

A pie-slice profile spanning exactly 3 tooth spacings (16.875°) is built at the tooth-tip radius (~90.17 mm):

- The profile is constructed symmetrically around +X using `Line` → `RadiusArc` → `Line` back to origin.
- The wedge is rotated −90° about Z to centre it on the −Y axis.
- A Ø88 mm cylinder is subtracted from the wedge in `Mode.SUBTRACT`, trimming the inner portion to produce a curved tab shape.

The resulting `arc_result` solid spans 3 tooth gaps on the −Y side of the gear.

### 7. Boolean Combine — Gear + Boss + Arc

All three bodies are unified in a single `BuildPart` (`final`):

```python
add(gear.part)
add(boss.part,   mode=Mode.ADD)
add(arc_result,  mode=Mode.ADD)
```

### 8. Outer Ring

A concentric annular ring (Ø172.80 mm outer, Ø160.00 mm inner, 20 mm tall) is built independently, then fused with the gear assembly:

```python
combined = gear_assembly + ring_result
```

The ring wall (6.4 mm) surrounds the tooth-tip circle, acting as a retaining flange.

### 9. Sanity Checks

Bounding box and volume are printed at two stages — after the initial gear+boss+arc combine, and after adding the ring — to catch geometry errors before export.

### 10. STEP Export

A native Tk file-save dialog (defaulting to `~/Desktop/gear_model.step`) prompts for the output path. `export_step()` writes the final combined solid, with success/failure reported via a message box and terminal print.

---

## Key Parameters

```python
OUTER_DIAMETER  = 172.12   # disc OD (mm)
HEIGHT          =  20.00   # part height (mm)
HOLE_DIAMETER   =  63.92   # central through-hole (mm)

TOOTH_BASE      =   8.44   # tooth base arc length (mm)
TOOTH_SIDE      =   5.89   # isosceles triangle leg (mm)

BOSS_LENGTH     =  24.00   # boss X-span (mm)
BOSS_WIDTH      =  12.00   # boss Y-span (mm)
BOSS_HEIGHT     =  20.00   # boss height (mm)

TOOTH_OFFSET_ANGLE = -2.8  # clockwise phase shift for teeth (°)

CUT_CIRCLE_DIAMETER = 88.00  # arc wedge inner cut (mm)

RING_OUTER_DIAMETER = 172.80  # outer ring OD (mm)
RING_INNER_DIAMETER = 160.00  # outer ring ID (mm)
```

---

## Console Output

On a successful run the script prints:

```
Tooth height (depth of cut) : 4.1121 mm
Num teeth                   : 64
Boss Y centre               : 21.06 mm  (inner edge at Y=31.960)
Bounding box : ...
Volume       : ... mm3
Combined bounding box : ...
Combined volume       : ... mm3
  ✓ Model exported to: /path/to/gear_model.step
```

---

## Dependencies

```
build123d
ocp_vscode   ≥ 3.4.0   (OCP CAD Viewer, port 3940)
tkinter                  (standard library — file dialog + message box)
```

Install build123d:
```bash
pip install build123d
```

---

## Usage

```bash
python circle_with_cutout.py
```

The script will:
1. Build disc, tooth template, gear assembly, boss, arc wedge, and ring
2. Print geometry diagnostics to the terminal
3. Open a file-save dialog — choose a destination for the `.step` file
4. Display the combined body in OCP CAD Viewer
