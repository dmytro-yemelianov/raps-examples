#!/usr/bin/env node
/**
 * Node.js Streaming JSON Benchmark
 *
 * Uses line-by-line streaming to process large JSON files.
 * Each element in our generated JSON is on a single line,
 * so we can parse line by line without loading everything into memory.
 */

const fs = require('fs');
const readline = require('readline');

const inputFile = process.argv[2];
if (!inputFile) {
    console.error('Usage: node nodejs-streaming.js <input-file>');
    process.exit(1);
}

const fileSize = fs.statSync(inputFile).size;
console.log(`Processing: ${inputFile}`);
console.log(`File size: ${(fileSize / 1024 / 1024).toFixed(2)} MB`);

const startTime = Date.now();
let peakMemory = process.memoryUsage().heapUsed;

let elementCount = 0;
let wallCount = 0;
let materialCount = 0;
let inElements = false;

const rl = readline.createInterface({
    input: fs.createReadStream(inputFile, { highWaterMark: 64 * 1024 }),
    crlfDelay: Infinity
});

rl.on('line', (line) => {
    // Track peak memory every 100 lines
    if (elementCount % 100 === 0) {
        const mem = process.memoryUsage().heapUsed;
        if (mem > peakMemory) peakMemory = mem;
    }

    const trimmed = line.trim();

    // Detect elements array
    if (trimmed.includes('"elements"')) {
        inElements = true;
        return;
    }

    if (!inElements) return;

    // End of elements array
    if (trimmed === '],' || trimmed === ']') {
        inElements = false;
        return;
    }

    // Skip non-element lines
    if (!trimmed.startsWith('{')) return;

    // Remove trailing comma
    let jsonStr = trimmed;
    if (jsonStr.endsWith(',')) {
        jsonStr = jsonStr.slice(0, -1);
    }

    try {
        const element = JSON.parse(jsonStr);
        elementCount++;

        if (element.category === 'Walls') {
            wallCount++;
        }

        if (element.materials) {
            materialCount += element.materials.length;
        }

        if (elementCount % 2000 === 0) {
            const mem = process.memoryUsage();
            console.log(`Processed ${elementCount} elements, heap=${(mem.heapUsed / 1024 / 1024).toFixed(0)}MB`);
        }
    } catch (e) {
        // Skip unparseable lines
    }
});

rl.on('close', () => {
    const endTime = Date.now();
    const duration = (endTime - startTime) / 1000;
    const finalMemory = process.memoryUsage().heapUsed;
    peakMemory = Math.max(peakMemory, finalMemory);

    console.log('\n=== Results ===');
    console.log(`Duration: ${duration.toFixed(2)}s`);
    console.log(`Elements processed: ${elementCount}`);
    console.log(`Walls found: ${wallCount}`);
    console.log(`Materials found: ${materialCount}`);
    console.log(`Peak heap: ${(peakMemory / 1024 / 1024).toFixed(0)}MB`);

    const result = {
        status: 'success',
        duration_seconds: duration,
        elements_processed: elementCount,
        memory_mb: Math.round(peakMemory / 1024 / 1024)
    };

    console.log('\n' + JSON.stringify(result));
});

rl.on('error', (error) => {
    console.error(`Error: ${error.message}`);

    const result = {
        status: 'crashed',
        error: error.message,
        duration_seconds: (Date.now() - startTime) / 1000,
        memory_mb: Math.round(process.memoryUsage().heapUsed / 1024 / 1024)
    };

    console.log('\n' + JSON.stringify(result));
    process.exit(1);
});
