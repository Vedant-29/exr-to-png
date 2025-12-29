# EXR to PNG Converter for Three.js Matcaps

A professional-grade converter for transforming Blender EXR renders into optimized PNG matcap textures for use in Three.js applications.

## 📁 Project Structure

```
exr-to-png/
├── sample_inputs/          # 23 sample EXR matcap files (metals, ceramics, etc.)
├── sample_outputs/         # Pre-converted PNG examples at 2048x2048
├── example_configs/        # YAML configuration presets
│   ├── config.yaml         # Default configuration
│   ├── matcap_metallic.yaml
│   ├── matcap_glass.yaml
│   └── matcap_stylized.yaml
├── src/                    # Source code
├── cli.py                  # Command-line interface
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

### 🎨 Sample Files Included

**Input EXR Files** (`sample_inputs/`):
- 23 high-quality matcap samples covering various materials
- Metal: shiny, anisotropic, carpaint, lead
- Ceramic: dark, lightbulb
- Clay: brown, muddy, studio
- Organic: skin, pearl, jade, resin
- Stylized: toon
- Utility: reflection checks, rim lights, normals

**Output PNG Files** (`sample_outputs/`):
- Pre-converted examples at 2048x2048 resolution
- ACES Filmic tone mapping applied
- Quality 100, sRGB color space
- Ready to use in Three.js applications

## Features

- **Industry-Standard Tone Mapping**: ACES Filmic, Reinhard, Hable (Uncharted 2), and Exposure-based
- **HDR to LDR Conversion**: Proper handling of high dynamic range imagery
- **Matcap Optimization**: Automatic cropping, resizing, and power-of-2 sizing for Three.js
- **Color Space Management**: Linear to sRGB conversion with proper gamma handling
- **Batch Processing**: Process multiple files with parallel execution support
- **Configurable Presets**: Ready-made configurations for different material types
- **Enhancement Filters**: Optional sharpening, saturation, brightness, and contrast adjustments
- **Professional CLI**: User-friendly command-line interface with progress tracking

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Install Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Dependencies

- `numpy` - Array operations and image processing
- `Pillow` - Image I/O and basic operations
- `OpenEXR` - EXR file format support
- `scipy` - Enhancement filters (sharpening)
- `click` - CLI framework
- `tqdm` - Progress bars
- `PyYAML` - Configuration file support
- `colorama` - Colored terminal output

## Quick Start

### Try the Samples First!

The project includes 23 sample EXR files and their pre-converted PNG outputs:

```bash
# View sample inputs
ls sample_inputs/

# View sample outputs (ready-to-use PNG matcaps)
ls sample_outputs/
```

Use the sample outputs directly in your Three.js projects, or convert the inputs yourself with custom settings!

### Basic Conversion

Convert a single EXR file to PNG:

```bash
python cli.py convert input.exr output.png
```

### Batch Conversion

Convert all EXR files in a directory:

```bash
python cli.py convert renders/ output/ --recursive
```

### Try Converting the Samples

Re-convert the included samples with your own settings:

```bash
# Convert all samples with default settings
python cli.py convert sample_inputs/ my_output/ --preset matcap-metallic

# Convert with custom high-quality settings
python cli.py convert sample_inputs/ my_output/ \
  --tone-mapping aces \
  --size 2048 \
  --quality 100 \
  --parallel
```

### Using Presets

Use a preset configuration optimized for specific material types:

```bash
python cli.py convert input.exr output.png --preset matcap-metallic
```

Example with sample files:

```bash
# Convert metal samples with metallic preset
python cli.py convert sample_inputs/metal_shiny.exr output.png --preset matcap-metallic

# Convert ceramic samples with different preset
python cli.py convert sample_inputs/ceramic_lightbulb.exr output.png --preset matcap-ceramic
```

### Custom Settings

Fine-tune conversion parameters:

```bash
python cli.py convert input.exr output.png \
  --tone-mapping aces \
  --exposure 1.5 \
  --size 1024 \
  --quality 95
```

## Available Presets

View all presets:

```bash
python cli.py presets
```

### Preset Descriptions

- **blender-accurate**: Exact 1:1 Blender match, passthrough mode, max quality (2048px) - **Recommended**
- **matcap-metallic**: Optimized for metallic materials (1024px, passthrough)
- **matcap-matte**: Optimized for matte/diffuse materials (512px, passthrough)
- **matcap-glass**: High-res with alpha for transparent materials (2048px, passthrough)
- **matcap-stylized**: Stylized rendering with enhanced saturation (512px, passthrough)
- **matcap-ceramic**: Balanced for ceramic and smooth materials (1024px, passthrough)
- **high-quality**: Maximum quality settings (2048px, lossless, passthrough)
- **fast**: Fast processing with lower quality (512px, passthrough)

**All presets now use `passthrough` tone mapping for perfect Blender accuracy!**

## Command Reference

### Convert Command

```bash
python cli.py convert [OPTIONS] INPUT_PATH OUTPUT_PATH
```

#### Options

**Preset & Configuration**:
- `--preset, -p <name>` - Use a preset configuration
- `--config, -c <file>` - Load configuration from YAML file

**Tone Mapping**:
- `--tone-mapping, -t <method>` - Tone mapping method: `aces`, `reinhard`, `exposure`, `hable`
- `--exposure, -e <value>` - Exposure adjustment in EV stops (-10 to +10)
- `--gamma, -g <value>` - Gamma correction value (0.1 to 5.0)

**Output Settings**:
- `--size, -s <pixels>` - Output size (width/height for square matcap)
- `--quality, -q <0-100>` - PNG compression quality

**Batch Processing**:
- `--recursive, -r` - Process subdirectories recursively
- `--overwrite` - Overwrite existing output files
- `--workers, -w <n>` - Number of parallel workers (default: 4)
- `--parallel / --no-parallel` - Enable/disable parallel processing

**Matcap Options**:
- `--no-matcap` - Disable matcap-specific optimizations
- `--no-alpha` - Remove alpha channel from output

**Enhancement Filters**:
- `--sharpen <0.0-2.0>` - Sharpening amount
- `--saturation <0.0-3.0>` - Saturation multiplier
- `--brightness <0.1-3.0>` - Brightness multiplier
- `--contrast <0.1-3.0>` - Contrast multiplier

**Logging**:
- `--verbose, -v` - Enable verbose logging
- `--quiet` - Suppress all logging except errors

### Other Commands

**List Presets**:
```bash
python cli.py presets
```

**Export Preset to YAML**:
```bash
python cli.py export-preset matcap-metallic config.yaml
```

**Validate Configuration**:
```bash
python cli.py validate-config config.yaml
```

**Display EXR Info**:
```bash
python cli.py info input.exr
```

## Configuration Files

### YAML Configuration

Example configurations are provided in `example_configs/`:

- `config.yaml` - Default configuration template
- `matcap_metallic.yaml` - Optimized for metallic materials
- `matcap_glass.yaml` - High-res for glass/transparent materials
- `matcap_stylized.yaml` - Stylized/cartoon rendering

Use with:

```bash
python cli.py convert input.exr output.png --config example_configs/matcap_metallic.yaml
```

Or create your own:

```yaml
# my_config.yaml
tone_mapping: aces
exposure: 1.0
gamma: 2.2
output_size: 1024
quality: 95
matcap_mode: true
crop_method: center
resample_method: lanczos
ensure_power_of_2: true
preserve_alpha: true
sharpen: 0.1
saturation: 1.05
brightness: 1.0
contrast: 1.0
```

## Tone Mapping Methods

### ⭐ Passthrough (Recommended for Blender Matcaps)

**Pass-through mode preserves the exact appearance from Blender**.

Blender's matcap EXR files are **already tone-mapped** (LDR stored as EXR). The passthrough mode simply preserves this data with proper gamma correction, ensuring your PNG output looks **exactly** like it does in Blender.

- **Best for**: Blender matcap EXR files (recommended!)
- **Characteristics**: 1:1 visual match with Blender, no additional tone curve
- **Usage**: `--tone-mapping passthrough` (now the default)
- **When to use**: Always, unless you have true HDR EXR files

```bash
# Perfect Blender match
python cli.py convert matcap.exr matcap.png --tone-mapping passthrough
```

### ACES Filmic

Industry-standard tone mapping for **true HDR** content. Only use if your EXR has values > 1.0.

- **Best for**: True HDR EXR files with bright highlights
- **Characteristics**: Natural highlight rolloff, cinematic look
- **Usage**: `--tone-mapping aces`
- **When to use**: HDR renders with value range > 1.0

### Reinhard

Balanced tone mapping with configurable white point. For HDR content.

- **Best for**: HDR images needing highlight compression
- **Usage**: `--tone-mapping reinhard`

### Hable (Uncharted 2)

Filmic tone mapping from game development.

- **Best for**: HDR game assets, stylized looks
- **Usage**: `--tone-mapping hable`

### Exposure

Simple exposure adjustment.

- **Best for**: Quick brightness tweaks
- **Usage**: `--tone-mapping exposure --exposure 0.5`

### Important Note

**For Blender matcaps: Always use `passthrough`!**

Other tone mapping methods will darken and alter your matcaps because they apply tone curves designed for HDR → LDR conversion, but Blender matcaps are already in LDR format.

## Three.js Integration

### Using Generated Matcaps

```javascript
import * as THREE from 'three';

// Load matcap texture
const textureLoader = new THREE.TextureLoader();
const matcapTexture = textureLoader.load('matcap.png');

// Apply to material
const material = new THREE.MeshMatcapMaterial({
  matcap: matcapTexture
});

// Use with mesh
const geometry = new THREE.SphereGeometry(1, 64, 64);
const mesh = new THREE.Mesh(geometry, material);
scene.add(mesh);
```

### Matcap Requirements

- **Square Aspect Ratio**: Automatically handled by converter
- **Power-of-2 Dimensions**: Enabled by default for optimal GPU performance
- **sRGB Color Space**: Applied automatically
- **Recommended Sizes**: 512px (fast), 1024px (standard), 2048px (high-quality)

## Examples

### Example 1: Metallic Material

```bash
python cli.py convert metal_render.exr metal_matcap.png \
  --preset matcap-metallic \
  --exposure 0.5 \
  --sharpen 0.15
```

### Example 2: Glass Material with Alpha

```bash
python cli.py convert glass_render.exr glass_matcap.png \
  --preset matcap-glass \
  --exposure 1.0
```

### Example 3: Batch Convert Samples with Custom Settings

```bash
python cli.py convert sample_inputs/ my_matcaps/ \
  --tone-mapping aces \
  --size 1024 \
  --quality 95 \
  --workers 8 \
  --parallel
```

### Example 4: Compare Different Tone Mapping Methods

```bash
# Try different tone mapping on the same sample
python cli.py convert sample_inputs/metal_shiny.exr metal_aces.png --tone-mapping aces
python cli.py convert sample_inputs/metal_shiny.exr metal_reinhard.png --tone-mapping reinhard
python cli.py convert sample_inputs/metal_shiny.exr metal_hable.png --tone-mapping hable
```

### Example 5: Stylized Cartoon Material

```bash
python cli.py convert sample_inputs/toon.exr toon_custom.png \
  --preset matcap-stylized \
  --saturation 1.5 \
  --contrast 1.2
```

## Workflow with Blender

### 1. Render Matcap in Blender

```python
# Blender Python script for matcap rendering
import bpy

# Setup matcap sphere
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))
sphere = bpy.context.active_object

# Setup camera (orthographic, centered on sphere)
bpy.ops.object.camera_add(location=(0, -3, 0), rotation=(1.5708, 0, 0))
camera = bpy.context.active_object
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 2.2

# Setup lighting (three-point, HDRI, etc.)
# ... your lighting setup ...

# Render settings
scene = bpy.context.scene
scene.render.image_settings.file_format = 'OPEN_EXR'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.image_settings.color_depth = '32'
scene.render.resolution_x = 2048
scene.render.resolution_y = 2048

# Render
bpy.ops.render.render(write_still=True)
```

### 2. Convert to Matcap

```bash
python cli.py convert blender_output.exr final_matcap.png \
  --preset matcap-metallic \
  --size 1024
```

### 3. Use in Three.js

See "Three.js Integration" section above.

## Advanced Usage

### Custom Tone Mapping Pipeline

```python
from src import EXRConverter, ConversionConfig

# Create custom config
config = ConversionConfig(
    tone_mapping='aces',
    exposure=1.5,
    gamma=2.2,
    output_size=2048,
    quality=98,
    sharpen=0.2,
    saturation=1.1
)

# Convert
converter = EXRConverter(config)
stats = converter.convert('input.exr', 'output.png')

print(f"Converted: {stats['output_size']}")
```

### Parallel Batch Processing

```python
from src import EXRConverter, ConversionConfig, find_exr_files

config = ConversionConfig(workers=8)
converter = EXRConverter(config)

exr_files = find_exr_files('renders/', recursive=True)
summary = converter.convert_batch_parallel(exr_files, 'output/')

print(f"Processed {summary['successful']} files")
```

## Troubleshooting

### OpenEXR Installation Issues

If you encounter issues installing OpenEXR:

**On macOS**:
```bash
brew install openexr
pip install OpenEXR
```

**On Ubuntu/Debian**:
```bash
sudo apt-get install libopenexr-dev
pip install OpenEXR
```

**On Windows**:
Download pre-built wheels from https://www.lfd.uci.edu/~gohlke/pythonlibs/

### Memory Issues with Large Files

For very large EXR files (>4K), reduce the number of parallel workers:

```bash
python cli.py convert large.exr output.png --workers 1
```

### Performance Optimization

For maximum performance:

1. Use parallel processing: `--parallel`
2. Increase workers: `--workers 8`
3. Use faster tone mapping: `--tone-mapping exposure`
4. Reduce output size: `--size 512`
5. Disable filters: No `--sharpen`, `--saturation`, etc.

## Technical Details

### Tone Mapping Algorithms

**ACES Filmic (Narkowicz 2015)**:
```
f(x) = (x * (a * x + b)) / (x * (c * x + d) + e)
```

**Reinhard**:
```
f(x) = x * (1 + x / W²) / (1 + x)
```

**Exposure + Gamma**:
```
f(x) = (x * 2^EV)^(1/γ)
```

### Color Space Conversion

Linear to sRGB:
```
sRGB = { x * 12.92,                  if x ≤ 0.0031308
       { 1.055 * x^(1/2.4) - 0.055,  otherwise
```

### Performance Characteristics

- Single 1K image: ~1-2 seconds
- Batch processing: Linear scaling with workers
- Memory usage: ~3x input file size
- Parallel efficiency: ~80-90% on multi-core systems

## License

This project is provided as-is for educational and commercial use.

## Contributing

Contributions are welcome! Please ensure:

1. Code follows existing style
2. All tests pass
3. Documentation is updated
4. Commit messages are descriptive

## Changelog

### Version 1.0.0

- Initial release
- Support for ACES, Reinhard, Hable, and Exposure tone mapping
- Matcap-specific optimizations
- Batch processing with parallel execution
- Configurable presets
- Comprehensive CLI interface
- Enhancement filters
- Full documentation

## Support

For issues, questions, or contributions, please use the GitHub issue tracker.

---

**Made for converting Blender EXR renders to Three.js matcaps with professional quality.**
