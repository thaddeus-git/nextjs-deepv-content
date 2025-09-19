# 🔄 JSON to MDX Workflow Documentation

This document describes the new JSON-to-MDX conversion workflow for processing content from the upstream AI generator.

## 📋 Overview

The workflow has been updated to support JSON input from the upstream AI generator, which is then converted to MDX format for the website. This enables better separation of concerns and more flexible content processing.

### 🏗️ Architecture Flow

```
Upstream AI Generator → JSON Files → JSON-to-MDX Converter → MDX Files → Validation → Production
```

## 📁 Directory Structure

```
nextjs-deepv-content/
├── staging/
│   ├── json/                      # Input: JSON files from upstream
│   │   ├── processed/             # Successfully converted JSON files
│   │   └── errors/                # Failed conversion attempts
│   ├── guides/                    # Output: Generated MDX files  
│   └── config/
│       └── article-index-update.json  # Updated article index
├── config/
│   ├── upstream-ai-generator-schema.json  # Schema for upstream
│   ├── categories.json            # Valid categories/subcategories
│   └── article-index.json         # Production article index
└── json-to-mdx-converter.js      # Conversion script
```

## 🛠️ Usage

### **Quick Start**
```bash
# Convert JSON files to MDX
npm run convert

# Validate converted content
npm run validate

# Promote to production (validates + moves + commits)
npm run promote

# Full workflow (convert + validate + promote)
npm run workflow
```

### **Individual Commands**
```bash
# Convert only
node json-to-mdx-converter.js

# Validate only
node validate-content.js staging/guides content-schema.json

# Promote only
node promote.js
```

## 📋 Input JSON Format

The converter expects JSON files in `staging/json/` with this structure:

```json
{
  "metadata": {
    "title": "How to Parse JSON in JavaScript",
    "slug": "how-to-parse-json-in-javascript", 
    "uniqueId": "abc12345",
    "category": "web-frontend",
    "subcategory": "javascript",
    "description": "Complete guide to JSON parsing in JavaScript with examples",
    "tags": ["javascript", "json", "parsing"],
    "difficulty": "beginner",
    "readTime": 8,
    "publishedAt": "2025-09-19",
    "featured": false,
    "technology": "JavaScript",
    "votes": 150,
    "answersCount": 5,
    "sourceStackOverflowId": "12345",
    "generatedAt": "2025-09-19T10:30:00.000Z",
    "workflowVersion": "deepv_stackoverflow_v1.0",
    "qualityMetrics": {
      "wordCount": 2500,
      "codeBlocks": 12,
      "sections": 8,
      "personaIntegration": 25,
      "practicalFocusScore": 95
    }
  },
  "content": "# How to Parse JSON in JavaScript\\n\\nJSON (JavaScript Object Notation)...",
  "source_file": "/path/to/source.json",
  "generation_stats": {},
  "workflow_version": "deepv_stackoverflow_v1.0"
}
```

## 🔧 Conversion Features

### **Automatic Fixes**
- ✅ **Title Truncation**: Long titles automatically truncated to 70 characters
- ✅ **Slug Normalization**: Underscores converted to hyphens, kebab-case enforced
- ✅ **Category Mapping**: Auto-maps common category mistakes (e.g., "programming" → "programming-languages")
- ✅ **Subcategory Intelligence**: Smart subcategory mapping based on tags and content
- ✅ **Date Formatting**: Ensures proper ISO 8601 date format for lastUpdated
- ✅ **Filename Generation**: Creates proper MDX filenames: `{slug}-{uniqueId}.mdx`

### **Smart Category Mapping**
```javascript
// Auto-detected mappings based on tags:
"programming" + ["sql", "mysql"] → "databases" + "mysql"  
"programming" + ["javascript", "js"] → "web-frontend" + "javascript"
"programming" + ["python"] → "programming-languages" + "python"
"programming" + ["docker", "aws"] → "system-devops" + "cloud"
```

### **Validation Rules**
- ✅ Title: 5-70 characters
- ✅ Description: 20-200 characters  
- ✅ Category: Must exist in categories.json
- ✅ Subcategory: Must exist under selected category
- ✅ Difficulty: beginner, intermediate, or advanced
- ✅ ReadTime: 1-60 minutes
- ✅ Tags: 1-10 tags required
- ✅ UniqueId: 8-character hex string

## 📊 Output MDX Format

Converted files are saved to `staging/guides/` with this structure:

```markdown
---
title: "How to Parse JSON in JavaScript"
slug: "how-to-parse-json-in-javascript"
category: "web-frontend"
subcategory: "javascript" 
description: "Complete guide to JSON parsing in JavaScript with examples"
tags: ["javascript","json","parsing"]
difficulty: "beginner"
readTime: 8
lastUpdated: "2025-09-19T10:30:00.000Z"
featured: false
---

# How to Parse JSON in JavaScript

JSON (JavaScript Object Notation) is a lightweight...
```

## 🔍 Process Flow

### **1. Input Processing**
- Scans `staging/json/` for JSON files
- Excludes metadata files (`*.metadata.json`) and error logs (`*_errors.json`)
- Validates JSON structure and required fields

### **2. Auto-Correction**
- Maps categories using intelligent tag analysis
- Truncates long titles while preserving meaning
- Normalizes slugs for proper kebab-case format  
- Ensures valid ISO date formatting

### **3. Validation**
- Validates against content schema requirements
- Checks category/subcategory combinations
- Ensures all required fields are present and properly formatted

### **4. Output Generation**
- Creates MDX files with proper frontmatter
- Generates proper filenames: `{slug}-{uniqueId}.mdx`
- Updates article index with new content metadata

### **5. File Management**
- Moves successfully processed JSON files to `staging/json/processed/`
- Moves failed files to `staging/json/errors/` with error logs
- Maintains clean separation between processed and pending files

## 📈 Article Index Update

The converter automatically updates `staging/config/article-index-update.json`:

```json
{
  "articles": [
    {
      "title": "How to Parse JSON in JavaScript",
      "slug": "how-to-parse-json-in-javascript",
      "category": "web-frontend",
      "subcategory": "javascript",
      "description": "Complete guide to JSON parsing...",
      "tags": ["javascript", "json", "parsing"],
      "difficulty": "beginner", 
      "readTime": 8,
      "lastUpdated": "2025-09-19T10:30:00.000Z",
      "featured": false,
      "filename": "how-to-parse-json-in-javascript-abc12345.mdx",
      "sourceStackOverflowId": "12345",
      "qualityMetrics": { "wordCount": 2500, "codeBlocks": 12 }
    }
  ],
  "lastUpdated": "2025-09-19T08:45:22.123Z",
  "totalArticles": 1
}
```

## ⚠️ Error Handling

### **Common Issues and Solutions**

#### **Invalid Categories**
```bash
❌ Error: Invalid category: programming  
✅ Auto-fix: Maps to appropriate category based on tags
```

#### **Long Titles** 
```bash
❌ Error: title must be 5-70 characters (SEO optimized)
✅ Auto-fix: Truncates at natural word boundaries
```

#### **Malformed Slugs**
```bash  
❌ Error: slug contains underscores
✅ Auto-fix: Converts underscores to hyphens
```

#### **Missing Required Fields**
```bash
❌ Error: Missing required field: description
✅ Manual: Fix upstream JSON generation
```

### **Error Logs**
Failed conversions generate detailed error logs in `staging/json/errors/`:

```json
{
  "filename": "problematic-file.json",
  "errors": [
    "Missing required field: description",
    "Invalid category: unknown-category"
  ],
  "timestamp": "2025-09-19T08:30:15.123Z"
}
```

## 🚀 Integration with Existing Workflow

### **Before (Direct MDX)**
```
Upstream → MDX Files → Staging → Validation → Production
```

### **After (JSON Pipeline)**  
```
Upstream → JSON Files → MDX Conversion → Staging → Validation → Production
```

### **Benefits**
- ✅ **Separation of Concerns**: Content generation vs. formatting
- ✅ **Flexibility**: Easy to modify output format without changing upstream
- ✅ **Quality Control**: Automatic validation and correction
- ✅ **Debugging**: Better error tracking and recovery
- ✅ **Scalability**: Batch processing capabilities

## 📚 Schema Documentation

### **Upstream Generator Schema**
Location: `config/upstream-ai-generator-schema.json`

Defines the expected JSON structure and validation rules for upstream content generation, including:
- Required fields and data types
- Category/subcategory mappings
- Quality metrics expectations
- Error handling specifications

### **Content Validation Schema**  
Location: `content-schema.json`

Defines validation rules for final MDX content, ensuring compatibility with the main website requirements.

## 🔧 Customization

### **Adding New Categories**
1. Update `config/categories.json` with new category/subcategory
2. Update category mapping logic in converter if needed
3. Test with sample JSON files

### **Modifying Auto-Corrections**
Edit `json-to-mdx-converter.js` methods:
- `truncateTitle()` - Title length handling
- `normalizeSlug()` - Slug formatting rules  
- `mapCategory()` - Category intelligence
- `mapSubcategory()` - Subcategory intelligence

### **Custom Validation Rules**
Modify `validateJsonStructure()` method to add custom validation logic for specific content requirements.

## 🎯 Best Practices

### **For Upstream Generators**
- ✅ Always include all required metadata fields
- ✅ Use proper 8-character hex uniqueId values
- ✅ Include relevant tags for smart category mapping
- ✅ Ensure content meets minimum word count requirements
- ✅ Use proper ISO date formats

### **For Content Managers**
- ✅ Run conversion in small batches for easier debugging
- ✅ Always validate before promoting to production
- ✅ Check error logs for systematic issues
- ✅ Review auto-mapped categories for accuracy
- ✅ Monitor article index for duplicates

## 🆘 Troubleshooting

### **No Files Converted**
```bash
# Check if JSON files exist
ls -la staging/json/*.json

# Check file permissions
chmod +r staging/json/*.json

# Run with verbose logging
DEBUG=1 node json-to-mdx-converter.js
```

### **Validation Failures**
```bash
# Check specific file
node validate-content.js staging/guides/specific-file.mdx content-schema.json

# Review conversion logs
cat staging/json/errors/*_errors.json
```

### **Category Mapping Issues**
1. Check `config/categories.json` for available categories
2. Review tag-based mapping logic in converter
3. Manually specify category/subcategory in JSON if needed

---

**This JSON-to-MDX workflow enables scalable, reliable content processing with automatic quality improvements and comprehensive error handling.**