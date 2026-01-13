#!/usr/bin/env python3
"""
Python Baseline Benchmark

Processes large JSON files using Python's standard library.
This serves as a baseline comparison for Node.js and RAPS.

Python's json module loads the entire file into memory, similar to
Node.js's JSON.parse(). This demonstrates the memory pressure that
both languages face with large files.
"""

import json
import sys
import time
import tracemalloc

def main():
    if len(sys.argv) < 2:
        print("Usage: python python-baseline.py <input-file>", file=sys.stderr)
        sys.exit(1)

    input_file = sys.argv[1]

    # Get file size
    import os
    file_size = os.path.getsize(input_file)
    file_size_mb = file_size / (1024 * 1024)

    print(f"Processing: {input_file}")
    print(f"File size: {file_size_mb:.2f} MB")

    # Start memory tracking
    tracemalloc.start()

    start_time = time.time()
    peak_memory = 0

    try:
        # Load entire file into memory (standard approach)
        print("Loading JSON into memory...")
        with open(input_file, 'r') as f:
            content = f.read()

        current, peak = tracemalloc.get_traced_memory()
        print(f"File loaded, current memory: {current / 1024 / 1024:.0f}MB")

        print("Parsing JSON...")
        data = json.loads(content)

        # Free the string content
        del content

        current, peak = tracemalloc.get_traced_memory()
        print(f"JSON parsed, current memory: {current / 1024 / 1024:.0f}MB, peak: {peak / 1024 / 1024:.0f}MB")

        print("Processing elements...")
        element_count = 0
        wall_count = 0
        material_count = 0

        # Simulate typical AEC metadata extraction
        if 'elements' in data:
            for element in data['elements']:
                element_count += 1

                if element.get('category') == 'Walls':
                    wall_count += 1

                if 'materials' in element:
                    material_count += len(element['materials'])

                # Check memory periodically
                if element_count % 1000 == 0:
                    current, peak = tracemalloc.get_traced_memory()
                    if peak > peak_memory:
                        peak_memory = peak
                    print(f"  Processed {element_count} elements, peak memory: {peak / 1024 / 1024:.0f}MB")

        end_time = time.time()
        duration = end_time - start_time

        current, final_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_memory_mb = max(peak_memory, final_peak) / (1024 * 1024)

        print("\n=== Results ===")
        print(f"Duration: {duration:.2f}s")
        print(f"Elements processed: {element_count}")
        print(f"Walls found: {wall_count}")
        print(f"Materials found: {material_count}")
        print(f"Peak memory: {peak_memory_mb:.0f}MB")

        # Output JSON for benchmark collection
        result = {
            "status": "success",
            "duration_seconds": duration,
            "elements_processed": element_count,
            "memory_mb": int(peak_memory_mb)
        }

        print("\n" + json.dumps(result))

    except MemoryError as e:
        tracemalloc.stop()
        duration = time.time() - start_time

        print("\n=== CRASHED (MemoryError) ===")
        print(f"Error: {str(e)}")
        print("\nThis demonstrates why large files are problematic.")

        result = {
            "status": "crashed",
            "error": "MemoryError",
            "duration_seconds": duration,
            "memory_mb": 0
        }

        print("\n" + json.dumps(result))
        sys.exit(1)

    except Exception as e:
        tracemalloc.stop()
        duration = time.time() - start_time

        print(f"\n=== ERROR ===")
        print(f"Error: {str(e)}")

        result = {
            "status": "crashed",
            "error": str(e),
            "duration_seconds": duration,
            "memory_mb": 0
        }

        print("\n" + json.dumps(result))
        sys.exit(1)


if __name__ == '__main__':
    main()
