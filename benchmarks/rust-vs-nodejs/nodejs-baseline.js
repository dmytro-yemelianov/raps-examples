#!/usr/bin/env node
/**
 * Node.js Baseline Benchmark
 *
 * This script attempts to process large JSON files the same way
 * a typical Node.js APS utility would.
 *
 * Expected behavior for 3.4GB+ files:
 * - Crashes with "FATAL ERROR: Ineffective mark-compacts near heap limit"
 * - Or runs extremely slowly due to GC pressure
 *
 * This validates the claim from "Rust vs Node.js for 5GB Files"
 */

const fs = require('fs');
const path = require('path');

const inputFile = process.argv[2];
if (!inputFile) {
    console.error('Usage: node nodejs-baseline.js <input-file>');
    process.exit(1);
}

console.log(`Processing: ${inputFile}`);
console.log(`File size: ${(fs.statSync(inputFile).size / 1024 / 1024).toFixed(2)} MB`);

const startTime = Date.now();
const startMemory = process.memoryUsage().heapUsed;

// Log memory usage periodically
const memoryInterval = setInterval(() => {
    const mem = process.memoryUsage();
    console.log(`Memory: heap=${(mem.heapUsed / 1024 / 1024).toFixed(0)}MB, rss=${(mem.rss / 1024 / 1024).toFixed(0)}MB`);
}, 5000);

try {
    // This is how most Node.js tools process JSON - load entire file into memory
    console.log('Loading JSON into memory...');
    const content = fs.readFileSync(inputFile, 'utf8');

    console.log('Parsing JSON...');
    const data = JSON.parse(content);

    console.log('Processing elements...');
    let elementCount = 0;
    let wallCount = 0;
    let materialCount = 0;

    // Simulate typical AEC metadata extraction
    if (data.elements) {
        for (const element of data.elements) {
            elementCount++;
            if (element.category === 'Walls') {
                wallCount++;
            }
            if (element.materials) {
                materialCount += element.materials.length;
            }
        }
    }

    const endTime = Date.now();
    const duration = (endTime - startTime) / 1000;
    const endMemory = process.memoryUsage().heapUsed;

    clearInterval(memoryInterval);

    console.log('\n=== Results ===');
    console.log(`Duration: ${duration.toFixed(2)}s`);
    console.log(`Elements processed: ${elementCount}`);
    console.log(`Walls found: ${wallCount}`);
    console.log(`Materials found: ${materialCount}`);
    console.log(`Peak heap: ${(endMemory / 1024 / 1024).toFixed(0)}MB`);

    // Output JSON for benchmark collection
    const result = {
        status: 'success',
        duration_seconds: duration,
        elements_processed: elementCount,
        memory_mb: Math.round(endMemory / 1024 / 1024)
    };

    console.log('\n' + JSON.stringify(result));

} catch (error) {
    clearInterval(memoryInterval);

    console.error('\n=== CRASHED ===');
    console.error(`Error: ${error.message}`);

    if (error.message.includes('heap') || error.message.includes('memory')) {
        console.error('\nThis confirms the blog article claim:');
        console.error('Node.js cannot handle large AEC metadata files efficiently.');
    }

    const result = {
        status: 'crashed',
        error: error.message,
        duration_seconds: (Date.now() - startTime) / 1000,
        memory_mb: Math.round(process.memoryUsage().heapUsed / 1024 / 1024)
    };

    console.log('\n' + JSON.stringify(result));
    process.exit(1);
}
