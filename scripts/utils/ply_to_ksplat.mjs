// ply_to_ksplat.mjs
// Converts a Gaussian Splat .ply file to the compact .ksplat format
// used by the GaussianSplats3D three.js viewer.
//
// Usage: node scripts/utils/ply_to_ksplat.mjs input.ply output.ksplat
//
// What .ksplat is:
//   A compact binary format for Gaussian splats designed for web delivery.
//   Each Gaussian is stored as a fixed-size binary record (easier to stream).
//   Gaussians are pre-sorted by distance from the scene center, which speeds
//   up the depth-sort step in the WebGL renderer.

import pkg from '@mkkellogg/gaussian-splats-3d';
const { KSplatConverter } = pkg;
import * as fs from 'fs';

const [,, inputPath, outputPath] = process.argv;

if (!inputPath || !outputPath) {
  console.error('Usage: node ply_to_ksplat.mjs <input.ply> <output.ksplat>');
  process.exit(1);
}

if (!fs.existsSync(inputPath)) {
  console.error(`Input file not found: ${inputPath}`);
  process.exit(1);
}

console.log(`Converting: ${inputPath} → ${outputPath}`);

try {
  const plyData = fs.readFileSync(inputPath);
  const ksplatData = KSplatConverter.fromPLY(plyData.buffer);
  fs.writeFileSync(outputPath, Buffer.from(ksplatData));
  
  const inputMB  = (fs.statSync(inputPath).size  / 1024 / 1024).toFixed(1);
  const outputMB = (fs.statSync(outputPath).size / 1024 / 1024).toFixed(1);
  console.log(`✅ Done. ${inputMB} MB → ${outputMB} MB`);
} catch (err) {
  console.error('Conversion failed:', err.message);
  process.exit(1);
}
