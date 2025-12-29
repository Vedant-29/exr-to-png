"""
Setup script for EXR to PNG Converter
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / 'README.md'
long_description = readme_file.read_text(encoding='utf-8') if readme_file.exists() else ''

# Read requirements
requirements_file = Path(__file__).parent / 'requirements.txt'
requirements = []
if requirements_file.exists():
    requirements = requirements_file.read_text(encoding='utf-8').strip().split('\n')

setup(
    name='exr-to-png-matcap',
    version='1.0.0',
    description='Convert Blender EXR renders to PNG matcap textures optimized for Three.js',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='EXR to PNG Converter',
    author_email='',
    url='https://github.com/yourusername/exr-to-png',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'exr-to-png=cli:cli',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Multimedia :: Graphics :: Graphics Conversion',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',
    keywords='exr png matcap threejs blender hdr tone-mapping converter',
    project_urls={
        'Documentation': 'https://github.com/yourusername/exr-to-png#readme',
        'Source': 'https://github.com/yourusername/exr-to-png',
        'Tracker': 'https://github.com/yourusername/exr-to-png/issues',
    },
)
