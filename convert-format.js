#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

/**
 * Format Adapter: Convert new upstream JSON format to converter-expected format
 */

function convertFormat(inputFile, outputFile) {
  const data = JSON.parse(fs.readFileSync(inputFile, 'utf8'));
  
  // Extract frontmatter fields from root level
  const metadata = {
    title: data.title,
    slug: data.slug,
    uniqueId: data.id, // map 'id' to 'uniqueId'
    category: data.category,
    subcategory: data.subcategory,
    description: data.description,
    tags: data.tags,
    difficulty: data.difficulty,
    readTime: data.readTime,
    lastUpdated: data.lastUpdated
  };

  // Optional fields that might exist
  if (data.stackoverflow_id) metadata.sourceStackOverflowId = data.stackoverflow_id;
  if (data.votes) metadata.votes = data.votes;
  if (data.featured) metadata.featured = data.featured;

  // Create the expected format
  const convertedData = {
    metadata: metadata,
    content: data.content,
    // Preserve other fields for reference
    originalFormat: {
      image_prompts: data.image_prompts,
      generated_images: data.generated_images,
      source_file: data.source_file,
      workflow_version: data.workflow_version,
      generated_at: data.generated_at,
      word_count: data.word_count,
      code_blocks: data.code_blocks
    }
  };

  fs.writeFileSync(outputFile, JSON.stringify(convertedData, null, 2));
  console.log(`✅ Converted: ${path.basename(inputFile)} → ${path.basename(outputFile)}`);
}

// Convert all files in staging/json
const inputDir = './staging/json';
const outputDir = './staging/json-converted';

// Create output directory
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
}

// Process all JSON files
const files = fs.readdirSync(inputDir).filter(file => file.endsWith('.json'));

console.log(`🔄 Converting ${files.length} files from new format to converter format...`);

files.forEach(file => {
  const inputPath = path.join(inputDir, file);
  const outputPath = path.join(outputDir, file);
  
  try {
    convertFormat(inputPath, outputPath);
  } catch (error) {
    console.error(`❌ Failed to convert ${file}:`, error.message);
  }
});

console.log(`\n✅ Conversion complete! Converted files are in: ${outputDir}`);
console.log(`\nNext steps:`);
console.log(`1. Move converted files: mv ${outputDir}/* ${inputDir}/`);
console.log(`2. Run converter: npm run convert`);