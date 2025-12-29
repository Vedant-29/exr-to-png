"""
Main EXR to PNG conversion engine.
Orchestrates the complete conversion pipeline.
"""

import numpy as np
import logging
from typing import Optional, Dict, Any
from pathlib import Path

from .config import ConversionConfig
from .tone_mapping import apply_tone_mapping, linear_to_srgb
from .matcap_optimizer import optimize_for_matcap, apply_matcap_filters, add_matcap_metadata
from .utils import load_exr, save_png, validate_exr_file


logger = logging.getLogger(__name__)


class EXRConverter:
    """
    EXR to PNG converter with matcap optimization.
    """

    def __init__(self, config: Optional[ConversionConfig] = None):
        """
        Initialize converter with configuration.

        Args:
            config: ConversionConfig instance (uses defaults if None)
        """
        self.config = config or ConversionConfig()
        self.config.validate()

        logger.debug(f"Initialized EXR converter with config: {self.config.tone_mapping}")

    def convert(
        self,
        input_path: str,
        output_path: str,
        config_override: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Convert single EXR file to PNG.

        Args:
            input_path: Path to input EXR file
            output_path: Path for output PNG file
            config_override: Optional config overrides for this conversion

        Returns:
            Dictionary with conversion statistics and metadata

        Raises:
            ValueError: If input file is invalid
            IOError: If conversion fails
        """
        # Apply config overrides if provided
        if config_override:
            from .config import merge_configs
            config = merge_configs(self.config, config_override)
        else:
            config = self.config

        logger.info(f"Converting: {input_path} -> {output_path}")

        try:
            # Step 1: Load EXR file
            logger.debug("Loading EXR file...")
            hdr_image, metadata = load_exr(input_path)
            original_shape = hdr_image.shape

            logger.info(f"Loaded HDR image: {original_shape[1]}x{original_shape[0]}, "
                       f"{original_shape[2]} channels")

            # Step 2: Apply tone mapping
            logger.debug(f"Applying tone mapping: {config.tone_mapping}")
            ldr_image = apply_tone_mapping(
                hdr_image,
                method=config.tone_mapping,
                exposure=config.exposure,
                white_point=config.white_point
            )

            logger.info(f"Applied {config.tone_mapping} tone mapping "
                       f"(exposure: {config.exposure:+.2f} EV)")

            # Step 3: Color space conversion
            if config.apply_color_transform and config.color_space == 'srgb':
                logger.debug("Converting to sRGB color space...")
                ldr_image = linear_to_srgb(ldr_image)
                logger.info("Converted to sRGB color space")

            # Step 4: Matcap optimization
            if config.matcap_mode and config.output_size:
                logger.debug("Optimizing for matcap...")
                ldr_image = optimize_for_matcap(
                    ldr_image,
                    target_size=config.output_size,
                    crop_method=config.crop_method,
                    resample_method=config.resample_method,
                    ensure_pot=config.ensure_power_of_2
                )
                logger.info(f"Optimized for matcap: {config.output_size}x{config.output_size}")

            # Step 5: Apply enhancement filters
            if any([config.sharpen > 0, config.saturation != 1.0,
                   config.brightness != 1.0, config.contrast != 1.0]):
                logger.debug("Applying enhancement filters...")
                ldr_image = apply_matcap_filters(
                    ldr_image,
                    sharpen=config.sharpen,
                    saturation=config.saturation,
                    brightness=config.brightness,
                    contrast=config.contrast
                )
                logger.info("Applied enhancement filters")

            # Step 6: Handle alpha channel
            if not config.preserve_alpha and ldr_image.shape[2] == 4:
                logger.debug("Removing alpha channel...")
                ldr_image = ldr_image[:, :, :3]
                logger.info("Removed alpha channel")

            # Step 7: Save PNG
            logger.debug(f"Saving PNG (quality: {config.quality})...")
            save_png(
                ldr_image,
                output_path,
                quality=config.quality,
                optimize=config.optimize_png
            )

            # Gather statistics
            from .utils import get_file_size_mb, format_size

            input_size = get_file_size_mb(input_path)
            output_size = get_file_size_mb(output_path)

            stats = {
                'success': True,
                'input_path': input_path,
                'output_path': output_path,
                'input_size': format_size(input_size),
                'output_size': format_size(output_size),
                'compression_ratio': f"{input_size / output_size:.2f}x" if output_size > 0 else "N/A",
                'original_resolution': f"{original_shape[1]}x{original_shape[0]}",
                'output_resolution': f"{ldr_image.shape[1]}x{ldr_image.shape[0]}",
                'channels': ldr_image.shape[2],
                'tone_mapping': config.tone_mapping,
                'exposure': config.exposure,
                'metadata': add_matcap_metadata(ldr_image, metadata) if config.matcap_mode else metadata
            }

            logger.info(f"Conversion successful! Output: {stats['output_size']}, "
                       f"Compression: {stats['compression_ratio']}")

            return stats

        except Exception as e:
            logger.error(f"Conversion failed: {str(e)}")
            raise IOError(f"Failed to convert {input_path}: {str(e)}")

    def convert_batch(
        self,
        input_files: list[str],
        output_dir: str,
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """
        Convert multiple EXR files to PNG.

        Args:
            input_files: List of input EXR file paths
            output_dir: Output directory for PNG files
            show_progress: Show progress bar

        Returns:
            Dictionary with batch conversion statistics
        """
        from .utils import generate_output_path
        import os

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Progress bar
        if show_progress:
            try:
                from tqdm import tqdm
                iterator = tqdm(input_files, desc="Converting", unit="file")
            except ImportError:
                logger.warning("tqdm not available, progress bar disabled")
                iterator = input_files
        else:
            iterator = input_files

        # Process files
        results = []
        successful = 0
        failed = 0
        skipped = 0

        for input_path in iterator:
            try:
                # Generate output path
                output_path = generate_output_path(
                    input_path,
                    output_dir,
                    input_base_dir=None
                )

                # Check if output exists and overwrite is disabled
                if os.path.exists(output_path) and not self.config.overwrite:
                    logger.info(f"Skipping (exists): {output_path}")
                    skipped += 1
                    continue

                # Convert file
                stats = self.convert(input_path, output_path)
                results.append(stats)
                successful += 1

            except Exception as e:
                logger.error(f"Failed to convert {input_path}: {str(e)}")
                failed += 1
                results.append({
                    'success': False,
                    'input_path': input_path,
                    'error': str(e)
                })

        # Summary statistics
        summary = {
            'total_files': len(input_files),
            'successful': successful,
            'failed': failed,
            'skipped': skipped,
            'results': results,
            'config': self.config.to_dict()
        }

        logger.info(f"\nBatch conversion complete: {successful} successful, "
                   f"{failed} failed, {skipped} skipped")

        return summary

    def convert_batch_parallel(
        self,
        input_files: list[str],
        output_dir: str,
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """
        Convert multiple EXR files to PNG using parallel processing.

        Args:
            input_files: List of input EXR file paths
            output_dir: Output directory for PNG files
            show_progress: Show progress bar

        Returns:
            Dictionary with batch conversion statistics
        """
        from concurrent.futures import ProcessPoolExecutor, as_completed
        from .utils import generate_output_path
        import os

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Prepare conversion tasks
        tasks = []
        for input_path in input_files:
            output_path = generate_output_path(input_path, output_dir)

            # Check if output exists and overwrite is disabled
            if os.path.exists(output_path) and not self.config.overwrite:
                logger.info(f"Skipping (exists): {output_path}")
                continue

            tasks.append((input_path, output_path))

        if not tasks:
            logger.info("No files to convert")
            return {
                'total_files': len(input_files),
                'successful': 0,
                'failed': 0,
                'skipped': len(input_files),
                'results': [],
                'config': self.config.to_dict()
            }

        # Process in parallel
        results = []
        successful = 0
        failed = 0

        with ProcessPoolExecutor(max_workers=self.config.workers) as executor:
            # Submit all tasks
            futures = {
                executor.submit(self._convert_worker, input_path, output_path, self.config): (input_path, output_path)
                for input_path, output_path in tasks
            }

            # Progress bar
            if show_progress:
                try:
                    from tqdm import tqdm
                    iterator = tqdm(as_completed(futures), total=len(futures), desc="Converting", unit="file")
                except ImportError:
                    iterator = as_completed(futures)
            else:
                iterator = as_completed(futures)

            # Collect results
            for future in iterator:
                input_path, output_path = futures[future]
                try:
                    stats = future.result()
                    results.append(stats)
                    successful += 1
                except Exception as e:
                    logger.error(f"Failed to convert {input_path}: {str(e)}")
                    failed += 1
                    results.append({
                        'success': False,
                        'input_path': input_path,
                        'error': str(e)
                    })

        # Summary statistics
        summary = {
            'total_files': len(input_files),
            'successful': successful,
            'failed': failed,
            'skipped': len(input_files) - len(tasks),
            'results': results,
            'config': self.config.to_dict()
        }

        logger.info(f"\nParallel batch conversion complete: {successful} successful, "
                   f"{failed} failed, {len(input_files) - len(tasks)} skipped")

        return summary

    @staticmethod
    def _convert_worker(input_path: str, output_path: str, config: ConversionConfig) -> Dict[str, Any]:
        """
        Worker function for parallel processing.

        Args:
            input_path: Input EXR file path
            output_path: Output PNG file path
            config: Conversion configuration

        Returns:
            Conversion statistics
        """
        converter = EXRConverter(config)
        return converter.convert(input_path, output_path)
