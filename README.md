# exr-to-png

A CLI that turns Blender EXR matcap renders into Three.js-ready PNG
textures. Owns the full HDR-to-LDR pipeline — load the float EXR, apply
a tone-mapping curve, crop and resize to a square matcap, gamma-correct
to sRGB, compress, and write the PNG. Batchable, recursive, parallel.

## Table of contents

1. [What this builds](#what-this-builds)
2. [Pipeline](#pipeline)
3. [Key design decisions](#key-design-decisions)
4. [Setup](#setup)
5. [Usage](#usage)
6. [Presets](#presets)
7. [Repository tour](#repository-tour)

---

## What this builds

A single `exr-to-png` command that converts one EXR or a whole folder
of EXRs into matcap PNGs. Four properties distinguish it from a
two-line `imageio` script:

- **Six tone-mapping curves.** Passthrough (for EXRs already
  tone-mapped in Blender), ACES Filmic, Reinhard, exposure-only,
  Hable, and a Filmic curve approximating Blender's own. Picking the
  right curve is the difference between a matcap that looks correct
  and one that looks washed out.
- **Matcap-specific output stage.** Square center-crop, configurable
  power-of-two resize (256–2048), optional sharpen / saturation /
  brightness / contrast trims, and a strict gamma 2.2 → sRGB
  conversion so the PNG matches what Three.js's `MeshMatcapMaterial`
  expects.
- **YAML presets.** Four named presets (`blender-accurate`,
  `matcap-metallic`, `matcap-glass`, `matcap-stylized`) plus a `--config`
  flag for user YAML overrides. Re-running a known-good preset is one
  flag, not 12.
- **Batch with parallelism.** Point it at a directory; it walks
  recursively, dispatches a worker per EXR (configurable `--workers`),
  and skips files whose PNG already exists unless `--overwrite` is
  set.

23 sample EXR inputs (metals, ceramics, glass, jade, pearl, normal-map
debug spheres) and their pre-rendered 2048² PNGs ship in `sample_inputs/`
and `sample_outputs/` for quick verification.

## Pipeline

```
   .exr file
       │
       ▼
  ┌──────────────┐  OpenEXR + numpy → float32 (H,W,C) HDR array
  │  load_exr    │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐  one of: passthrough | aces | reinhard
  │ tone_mapping │           exposure | hable | filmic
  └──────┬───────┘  + exposure EV adjust + white-point
         │
         ▼
  ┌──────────────────┐  center-crop → resize to N×N
  │ matcap_optimizer │  + optional sharpen / saturation /
  └────────┬─────────┘    brightness / contrast filters
           │
           ▼
  ┌──────────────┐  linear → sRGB (gamma 2.2)
  │  gamma corr  │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐  Pillow PNG encode + optimize
  │  save_png    │  with alpha kept or stripped
  └──────┬───────┘
         │
         ▼
     .png file
```

The same pipeline runs serially for one file and in a worker pool for
a directory.

**Module responsibilities:**

| Module | Responsibility |
|---|---|
| `src/utils.py` | `load_exr` (OpenEXR → numpy float32), `save_png`, `validate_exr_file`, `find_exr_files` recursive walker, logging setup. |
| `src/tone_mapping.py` | Six HDR→LDR curves implemented as pure numpy functions. `apply_tone_mapping` dispatches on the config string. |
| `src/matcap_optimizer.py` | `crop_to_square`, `resize_image`, `apply_matcap_filters` (sharpen/saturation/brightness/contrast), and matcap PNG metadata tags. |
| `src/config.py` | `ConversionConfig` dataclass, `PRESETS` dict, YAML load/save, and `get_preset` / `list_presets` accessors. |
| `src/converter.py` | `EXRConverter` orchestrator. Owns the full pipeline for a single file. |
| `cli.py` | `click` entrypoint with `convert`, `presets`, and config-management subcommands. Handles batch parallelism. |

## Key design decisions

| Decision | Choice | Why |
|---|---|---|
| Default tone curve | `passthrough` | Most Blender EXRs are already tone-mapped on render. A non-passthrough default would silently double-process them and look wrong. |
| Output color space | sRGB with gamma 2.2 | What Three.js `MeshMatcapMaterial` samples in. Storing linear PNGs would force every consumer to gamma-correct themselves. |
| Square crop | Center, default | Matcap shaders sample a unit-circle within a square texture. Center-crop is the only crop that keeps the sphere centred. |
| Config surface | Six independent flags + YAML preset | A flag for each visual axis lets you iterate from the CLI; YAML presets let a stable look land in version control. |
| Batch model | Worker pool over directory walk | A single matcap takes ~1–3s; 23 of them in series is 30+s; a 4-worker pool gets it under 10s. Easy parallel gain. |
| Overwrite default | Skip existing | Idempotent batches. Re-running on a directory only touches new EXRs unless `--overwrite` is set. |

## Setup

### Prerequisites

- **Python 3.8+**
- The OpenEXR Python bindings require the libopenexr C++ libs:
  - macOS: `brew install openexr`
  - Debian/Ubuntu: `apt-get install libopenexr-dev`

### Install

```bash
git clone https://github.com/Vedant-29/exr-to-png.git
cd exr-to-png
pip install -r requirements.txt
pip install -e .         # installs the `exr-to-png` command
```

Verify:

```bash
exr-to-png --version
exr-to-png presets
```

## Usage

```bash
# Single file
exr-to-png convert input.exr output.png

# With a named preset
exr-to-png convert input.exr output.png --preset matcap-metallic

# Custom tone-map + size
exr-to-png convert input.exr output.png \
    --tone-mapping aces --exposure 1.5 --size 1024

# Batch convert a directory, recursive, 4 workers
exr-to-png convert renders/ output/ --recursive --workers 4

# Verify against the bundled samples
exr-to-png convert sample_inputs/ /tmp/matcaps/ --recursive \
    --preset matcap-metallic
```

All flags:

| Flag | What |
|---|---|
| `--preset, -p` | Use a named preset (`blender-accurate`, `matcap-metallic`, `matcap-glass`, `matcap-stylized`). |
| `--config, -c` | Load a YAML config file (overrides preset). |
| `--tone-mapping, -t` | `passthrough | aces | reinhard | exposure | hable | filmic`. |
| `--exposure, -e` | EV stops (-5 to +5). |
| `--gamma, -g` | Gamma correction (default 2.2). |
| `--size, -s` | Output side length. |
| `--quality, -q` | PNG compression quality 0–100. |
| `--sharpen` | 0.0–2.0. |
| `--saturation` | 0.0–3.0. |
| `--brightness` | 0.1–3.0. |
| `--contrast` | 0.1–3.0. |
| `--recursive, -r` | Walk subdirectories. |
| `--overwrite` | Re-encode files that already exist. |
| `--workers, -w` | Parallel worker count. |
| `--no-matcap` | Disable matcap-specific stage (square crop, etc.). |
| `--no-alpha` | Strip alpha channel. |
| `--parallel / --no-parallel` | Toggle batch parallelism. |
| `--verbose, -v` / `--quiet` | Logging. |

## Presets

| Preset | Tone curve | Size | Best for |
|---|---|---|---|
| `blender-accurate` | passthrough | 2048 | Faithful 1:1 of the Blender render. Highest quality, no extra processing. |
| `matcap-metallic` | passthrough + sharpen 0.1 | 1024 | Metals where micro-reflection contrast matters. |
| `matcap-glass` | configured per YAML | 1024 | Transparent / refractive looks. |
| `matcap-stylized` | configured per YAML | 1024 | Toon / non-photoreal matcaps where saturation is dialled up. |

YAML files live in `example_configs/`. To make your own, copy one and
pass it with `--config my_preset.yaml`.

## Repository tour

```
exr-to-png/
├── cli.py                  # click entrypoint (convert | presets | config)
├── setup.py                # pip-installable, exposes `exr-to-png` command
├── requirements.txt        # numpy, Pillow, OpenEXR, scipy, click, tqdm, PyYAML
├── src/
│   ├── __init__.py         # public re-exports
│   ├── config.py           # ConversionConfig dataclass + named PRESETS
│   ├── converter.py        # EXRConverter orchestrator
│   ├── tone_mapping.py     # 6 HDR→LDR curves (passthrough, aces, ...)
│   ├── matcap_optimizer.py # square crop, resize, sharpen, saturation
│   └── utils.py            # load_exr, save_png, find_exr_files, logging
├── example_configs/
│   ├── config.yaml         # default preset
│   ├── matcap_metallic.yaml
│   ├── matcap_glass.yaml
│   └── matcap_stylized.yaml
├── sample_inputs/          # 23 example EXR matcaps (metals, ceramics, ...)
└── sample_outputs/         # pre-rendered 2048² PNGs for verification
```

## License

MIT
