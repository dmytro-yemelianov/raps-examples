#!/usr/bin/env python3
"""
Test Data Generator for RAPS Examples

Generates synthetic AEC metadata JSON files that mimic real Revit/BIM model exports.
These files are used to benchmark RAPS vs Node.js performance claims.

Usage:
    python generate-test-data.py --output ./data/generated --size 500mb
    python generate-test-data.py --output ./data/generated --size 3.4gb
    python generate-test-data.py --output ./data/generated --size 100mb --name batch-file-1
"""

import argparse
import json
import os
import random
import string
import sys
from typing import Generator, TextIO

# Element categories typical in AEC models
CATEGORIES = [
    "Walls", "Floors", "Ceilings", "Roofs", "Doors", "Windows",
    "Stairs", "Railings", "Columns", "Beams", "Foundations",
    "Pipes", "Ducts", "Electrical", "Plumbing", "HVAC",
    "Furniture", "Casework", "Specialty Equipment", "Generic Models"
]

# Material types
MATERIALS = [
    "Concrete", "Steel", "Wood", "Glass", "Aluminum", "Brick",
    "Gypsum", "Insulation", "Paint", "Ceramic", "Plastic",
    "Copper", "PVC", "Cast Iron", "Stainless Steel"
]

# Property types for realistic metadata
PROPERTY_NAMES = [
    "Mark", "Comments", "Type Name", "Family", "Category",
    "Level", "Phase Created", "Phase Demolished", "Design Option",
    "Workset", "Assembly Code", "Assembly Description",
    "Fire Rating", "Structural Usage", "Thermal Resistance",
    "Cost", "Manufacturer", "Model", "URL"
]


def random_string(length: int) -> str:
    """Generate a random string of specified length."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def random_guid() -> str:
    """Generate a random GUID-like string."""
    return f"{random_string(8)}-{random_string(4)}-{random_string(4)}-{random_string(4)}-{random_string(12)}"


def generate_material() -> dict:
    """Generate a synthetic material entry."""
    return {
        "id": random.randint(100000, 999999),
        "name": random.choice(MATERIALS),
        "color": [random.randint(0, 255) for _ in range(3)],
        "transparency": random.uniform(0, 1),
        "shininess": random.randint(0, 100),
        "properties": {
            f"prop_{i}": random_string(20) for i in range(random.randint(3, 10))
        }
    }


def generate_geometry() -> dict:
    """Generate synthetic geometry data."""
    vertex_count = random.randint(10, 500)
    return {
        "vertices": [[random.uniform(-100, 100) for _ in range(3)] for _ in range(vertex_count)],
        "normals": [[random.uniform(-1, 1) for _ in range(3)] for _ in range(vertex_count)],
        "faces": [[random.randint(0, vertex_count-1) for _ in range(3)]
                  for _ in range(vertex_count // 3)],
        "bounds": {
            "min": [random.uniform(-100, 0) for _ in range(3)],
            "max": [random.uniform(0, 100) for _ in range(3)]
        }
    }


def generate_element(element_id: int) -> dict:
    """Generate a synthetic BIM element."""
    category = random.choice(CATEGORIES)
    material_count = random.randint(1, 5)

    return {
        "id": element_id,
        "externalId": random_guid(),
        "category": category,
        "family": f"{category} Family {random.randint(1, 100)}",
        "type": f"Type {random.randint(1, 50)}",
        "name": f"{category}-{element_id}",
        "level": f"Level {random.randint(1, 20)}",
        "materials": [generate_material() for _ in range(material_count)],
        "properties": {
            prop: random_string(random.randint(10, 100))
            for prop in random.sample(PROPERTY_NAMES, random.randint(5, len(PROPERTY_NAMES)))
        },
        "geometry": generate_geometry() if random.random() > 0.3 else None,
        "relationships": {
            "parent": random.randint(1, element_id) if element_id > 1 and random.random() > 0.5 else None,
            "children": [random.randint(element_id, element_id + 100)
                        for _ in range(random.randint(0, 5))],
            "hosted": [random.randint(1, element_id)
                      for _ in range(random.randint(0, 3))] if element_id > 10 else []
        },
        "parameters": {
            f"param_{i}": {
                "value": random_string(30) if random.random() > 0.5 else random.uniform(-1000, 1000),
                "type": random.choice(["string", "double", "integer", "boolean"]),
                "unit": random.choice(["mm", "m", "ft", "in", None])
            }
            for i in range(random.randint(10, 30))
        }
    }


def parse_size(size_str: str) -> int:
    """Parse size string (e.g., '500mb', '3.4gb') to bytes."""
    size_str = size_str.lower().strip()

    multipliers = {
        'b': 1,
        'kb': 1024,
        'mb': 1024 ** 2,
        'gb': 1024 ** 3
    }

    for suffix, multiplier in multipliers.items():
        if size_str.endswith(suffix):
            number = float(size_str[:-len(suffix)])
            return int(number * multiplier)

    # Assume bytes if no suffix
    return int(float(size_str))


def generate_streaming(output_file: TextIO, target_size: int) -> int:
    """
    Generate JSON data in a streaming fashion to avoid memory issues.
    Returns the number of elements generated.
    """
    current_size = 0
    element_count = 0

    # Write opening
    output_file.write('{\n')
    output_file.write('  "metadata": {\n')
    output_file.write(f'    "generator": "raps-examples",\n')
    output_file.write(f'    "version": "1.0",\n')
    output_file.write(f'    "target_size_bytes": {target_size}\n')
    output_file.write('  },\n')
    output_file.write('  "elements": [\n')

    current_size = output_file.tell()

    # Generate elements until we reach target size
    while current_size < target_size * 0.95:  # Leave room for closing
        element = generate_element(element_count + 1)
        element_json = json.dumps(element, indent=None)

        # Add comma separator for all but first element
        if element_count > 0:
            output_file.write(',\n')

        output_file.write('    ')
        output_file.write(element_json)

        element_count += 1
        current_size = output_file.tell()

        # Progress indicator every 10000 elements
        if element_count % 10000 == 0:
            progress = min(100, (current_size / target_size) * 100)
            print(f"  Generated {element_count} elements ({progress:.1f}%)", end='\r')

    # Write closing
    output_file.write('\n  ],\n')
    output_file.write(f'  "summary": {{\n')
    output_file.write(f'    "element_count": {element_count},\n')
    output_file.write(f'    "categories": {json.dumps(CATEGORIES)}\n')
    output_file.write('  }\n')
    output_file.write('}\n')

    print(f"  Generated {element_count} elements (100%)     ")
    return element_count


def main():
    parser = argparse.ArgumentParser(description='Generate synthetic AEC metadata for benchmarking')
    parser.add_argument('--output', '-o', required=True, help='Output directory')
    parser.add_argument('--size', '-s', default='500mb', help='Target file size (e.g., 500mb, 3.4gb)')
    parser.add_argument('--name', '-n', default='large-metadata', help='Output file name (without extension)')

    args = parser.parse_args()

    # Create output directory
    os.makedirs(args.output, exist_ok=True)

    # Parse target size
    target_size = parse_size(args.size)

    output_path = os.path.join(args.output, f'{args.name}.json')

    print(f"Generating test data:")
    print(f"  Output: {output_path}")
    print(f"  Target size: {target_size / (1024**2):.1f} MB")
    print()

    # Generate data
    with open(output_path, 'w') as f:
        element_count = generate_streaming(f, target_size)

    # Get actual file size
    actual_size = os.path.getsize(output_path)

    print()
    print(f"Generation complete:")
    print(f"  Elements: {element_count:,}")
    print(f"  File size: {actual_size / (1024**2):.1f} MB")
    print(f"  Output: {output_path}")

    # Write metadata file
    metadata_path = os.path.join(args.output, f'{args.name}.meta.json')
    with open(metadata_path, 'w') as f:
        json.dump({
            'file': output_path,
            'size_bytes': actual_size,
            'size_mb': round(actual_size / (1024**2), 2),
            'element_count': element_count,
            'generator': 'raps-examples',
            'target_size': args.size
        }, f, indent=2)

    print(f"  Metadata: {metadata_path}")


if __name__ == '__main__':
    main()
