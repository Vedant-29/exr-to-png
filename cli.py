#!/usr/bin/env python3
"""
EXR to PNG Converter - Command Line Interface

Convert Blender EXR renders to PNG matcap textures optimized for Three.js
"""

import click
import sys
import logging
from pathlib import Path

from src import (
    EXRConverter,
    ConversionConfig,
    get_preset,
    list_presets,
    find_exr_files,
    setup_logging
)
from src.config import load_config_file, save_config_file


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(version='1.0.0', prog_name='exr-to-png')
def cli(ctx):
    """
    EXR to PNG Converter for Three.js Matcaps

    Convert Blender EXR renders to optimized PNG matcap textures.

    Examples:

        # Basic conversion
        python cli.py convert input.exr output.png

        # Batch convert directory
        python cli.py convert renders/ output/ --recursive

        # Use preset
        python cli.py convert input.exr output.png --preset matcap-metallic

        # Custom settings
        python cli.py convert input.exr output.png --tone-mapping aces --exposure 1.5 --size 1024

        # List available presets
        python cli.py presets
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.argument('output_path', type=click.Path())
@click.option('--preset', '-p', type=str, help='Use a preset configuration (see "presets" command)')
@click.option('--config', '-c', type=click.Path(exists=True), help='Load configuration from YAML file')
@click.option('--tone-mapping', '-t', type=click.Choice(['passthrough', 'aces', 'reinhard', 'exposure', 'hable', 'filmic']), help='Tone mapping method')
@click.option('--exposure', '-e', type=float, help='Exposure adjustment in EV stops')
@click.option('--gamma', '-g', type=float, help='Gamma correction value')
@click.option('--size', '-s', type=int, help='Output size (width/height for square matcap)')
@click.option('--quality', '-q', type=int, help='PNG compression quality (0-100)')
@click.option('--recursive', '-r', is_flag=True, help='Process subdirectories recursively')
@click.option('--overwrite', is_flag=True, help='Overwrite existing output files')
@click.option('--workers', '-w', type=int, help='Number of parallel workers for batch processing')
@click.option('--no-matcap', is_flag=True, help='Disable matcap-specific optimizations')
@click.option('--no-alpha', is_flag=True, help='Remove alpha channel from output')
@click.option('--sharpen', type=float, help='Sharpening amount (0.0-2.0)')
@click.option('--saturation', type=float, help='Saturation multiplier (0.0-3.0)')
@click.option('--brightness', type=float, help='Brightness multiplier (0.1-3.0)')
@click.option('--contrast', type=float, help='Contrast multiplier (0.1-3.0)')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--quiet', is_flag=True, help='Suppress all logging except errors')
@click.option('--parallel/--no-parallel', default=True, help='Enable/disable parallel processing for batch operations')
def convert(
    input_path, output_path, preset, config, tone_mapping, exposure, gamma,
    size, quality, recursive, overwrite, workers, no_matcap, no_alpha,
    sharpen, saturation, brightness, contrast, verbose, quiet, parallel
):
    """
    Convert EXR file(s) to PNG.

    INPUT_PATH: Path to EXR file or directory
    OUTPUT_PATH: Path for output PNG file or directory
    """
    # Setup logging
    setup_logging(verbose=verbose, quiet=quiet)
    logger = logging.getLogger(__name__)

    try:
        # Load base configuration
        if config:
            base_config = load_config_file(config)
            logger.info(f"Loaded configuration from: {config}")
        elif preset:
            base_config = get_preset(preset)
            logger.info(f"Using preset: {preset}")
        else:
            base_config = ConversionConfig()
            logger.debug("Using default configuration")

        # Apply CLI overrides
        overrides = {}
        if tone_mapping:
            overrides['tone_mapping'] = tone_mapping
        if exposure is not None:
            overrides['exposure'] = exposure
        if gamma is not None:
            overrides['gamma'] = gamma
        if size is not None:
            overrides['output_size'] = size
        if quality is not None:
            overrides['quality'] = quality
        if workers is not None:
            overrides['workers'] = workers
        if no_matcap:
            overrides['matcap_mode'] = False
        if no_alpha:
            overrides['preserve_alpha'] = False
        if sharpen is not None:
            overrides['sharpen'] = sharpen
        if saturation is not None:
            overrides['saturation'] = saturation
        if brightness is not None:
            overrides['brightness'] = brightness
        if contrast is not None:
            overrides['contrast'] = contrast
        if overwrite:
            overrides['overwrite'] = True
        if recursive:
            overrides['recursive'] = True

        # Merge configurations
        if overrides:
            from src.config import merge_configs
            final_config = merge_configs(base_config, overrides)
        else:
            final_config = base_config

        # Create converter
        converter = EXRConverter(final_config)

        # Determine if batch or single file conversion
        input_path_obj = Path(input_path)

        if input_path_obj.is_file():
            # Single file conversion
            logger.info("Starting single file conversion...")
            stats = converter.convert(input_path, output_path)

            # Display results
            click.echo(f"\n✓ Conversion successful!")
            click.echo(f"  Input:  {stats['input_size']} ({stats['original_resolution']})")
            click.echo(f"  Output: {stats['output_size']} ({stats['output_resolution']})")
            click.echo(f"  Compression: {stats['compression_ratio']}")
            click.echo(f"  Tone mapping: {stats['tone_mapping']} (exposure: {stats['exposure']:+.2f} EV)")

        else:
            # Batch conversion
            logger.info("Starting batch conversion...")

            # Find EXR files
            exr_files = find_exr_files(input_path, recursive=final_config.recursive)
            click.echo(f"Found {len(exr_files)} EXR file(s)")

            # Convert
            if parallel and len(exr_files) > 1:
                summary = converter.convert_batch_parallel(
                    exr_files,
                    output_path,
                    show_progress=not quiet
                )
            else:
                summary = converter.convert_batch(
                    exr_files,
                    output_path,
                    show_progress=not quiet
                )

            # Display summary
            click.echo(f"\n{'='*50}")
            click.echo(f"Batch Conversion Summary")
            click.echo(f"{'='*50}")
            click.echo(f"Total files:  {summary['total_files']}")
            click.echo(f"Successful:   {summary['successful']} ✓")
            if summary['failed'] > 0:
                click.echo(f"Failed:       {summary['failed']} ✗")
            if summary['skipped'] > 0:
                click.echo(f"Skipped:      {summary['skipped']}")
            click.echo(f"{'='*50}")

            if summary['failed'] > 0:
                sys.exit(1)

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
def presets():
    """List all available presets with descriptions."""
    preset_descriptions = list_presets()

    click.echo("\nAvailable Presets:\n")
    click.echo("=" * 80)

    for name, description in preset_descriptions.items():
        click.echo(f"\n{name}")
        click.echo(f"  {description}")

    click.echo("\n" + "=" * 80)
    click.echo("\nUsage: python cli.py convert input.exr output.png --preset <preset-name>\n")


@cli.command()
@click.argument('preset_name', type=str)
@click.argument('output_file', type=click.Path())
def export_preset(preset_name, output_file):
    """
    Export a preset configuration to YAML file.

    PRESET_NAME: Name of the preset to export
    OUTPUT_FILE: Path for output YAML file
    """
    try:
        preset_config = get_preset(preset_name)
        save_config_file(preset_config, output_file)
        click.echo(f"✓ Exported preset '{preset_name}' to: {output_file}")
    except ValueError as e:
        click.echo(f"✗ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('config_file', type=click.Path(exists=True))
def validate_config(config_file):
    """
    Validate a configuration file.

    CONFIG_FILE: Path to YAML configuration file
    """
    try:
        config = load_config_file(config_file)
        config.validate()
        click.echo(f"✓ Configuration file is valid: {config_file}")

        # Display configuration
        click.echo("\nConfiguration:")
        click.echo("-" * 40)
        click.echo(f"Tone mapping:  {config.tone_mapping}")
        click.echo(f"Exposure:      {config.exposure:+.2f} EV")
        click.echo(f"Output size:   {config.output_size}x{config.output_size}")
        click.echo(f"Quality:       {config.quality}")
        click.echo(f"Matcap mode:   {config.matcap_mode}")
        click.echo("-" * 40)

    except Exception as e:
        click.echo(f"✗ Configuration file is invalid: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('exr_file', type=click.Path(exists=True))
def info(exr_file):
    """
    Display information about an EXR file.

    EXR_FILE: Path to EXR file
    """
    from src.utils import load_exr, get_file_size_mb, format_size

    try:
        # Load EXR
        image, metadata = load_exr(exr_file)

        # Display info
        click.echo(f"\nEXR File Information: {exr_file}")
        click.echo("=" * 60)
        click.echo(f"Resolution:    {metadata['width']}x{metadata['height']}")
        click.echo(f"Channels:      {metadata['channels']} ({'RGBA' if metadata['has_alpha'] else 'RGB'})")
        click.echo(f"Data window:   {metadata['data_window']}")
        click.echo(f"File size:     {format_size(get_file_size_mb(exr_file))}")
        click.echo(f"Data type:     {image.dtype}")
        click.echo(f"Value range:   [{image.min():.4f}, {image.max():.4f}]")

        # HDR statistics
        click.echo(f"\nHDR Statistics:")
        click.echo(f"  Mean:        {image.mean():.4f}")
        click.echo(f"  Std dev:     {image.std():.4f}")
        click.echo(f"  Median:      {float(import_numpy().median(image)):.4f}")

        # Check if square
        is_square = metadata['width'] == metadata['height']
        click.echo(f"\nMatcap compatibility:")
        click.echo(f"  Square aspect: {'Yes ✓' if is_square else 'No (will be cropped)'}")
        click.echo(f"  Recommended sizes: 512, 1024, 2048")

        click.echo("=" * 60)

    except Exception as e:
        click.echo(f"✗ Error reading EXR file: {str(e)}", err=True)
        sys.exit(1)


def import_numpy():
    """Lazy import of numpy for info command."""
    import numpy as np
    return np


if __name__ == '__main__':
    cli()
