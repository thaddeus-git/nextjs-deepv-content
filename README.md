# 📝 DeepV Code Content Repository

[![Content Validation](https://img.shields.io/badge/Content-Validated-green)](https://github.com/thaddeus-git/nextjs-deepv-content)
[![MDX](https://img.shields.io/badge/Format-MDX-blue)](https://mdxjs.com/)
[![Schema](https://img.shields.io/badge/Schema-v1.0.0-orange)](./content-schema.json)

This repository contains all articles and content for the [DeepV Code](https://deepvcode.com) technical documentation website. It operates independently from the main application using a decoupled architecture.




## Repository Roles & Ownership

| Repository                            | Role                  | Authority                    | Responsibility                                  |
|---------------------------------------|-----------------------|------------------------------|-------------------------------------------------|
| `nextjs-deepv-docs`                   | 🏛️ Schema Authority   | Defines content requirements | Application needs, validation rules, categories |
| `nextjs-deepv-content`                | 📦 Content Storage    | Stores validated content     | Production content, article index               |
| `deepv-stackoverflow-workflow-complete` | 🤖 Content Generator | Follows schema requirements  | Generates compliant content                     |


## 🏗️ **Repository Structure**

```
nextjs-deepv-content/
├── config/
│   ├── article-index.json    # Production article metadata index
│   └── categories.json       # Category configuration
├── guides/
│   └── *.mdx                # Production article files
├── staging/
│   ├── guides/              # Staging area for new articles
│   └── config/              # Staging configuration updates
├── validate-content.js      # Content validation script
├── content-schema.json      # Validation schema (copy from main repo)
└── package.json            # Dependencies for validation
```

## ✅ **Content Validation**

### **Quick Validation**
```bash
# Install dependencies (first time only)
npm install

# Validate staging content
npm run validate

# Or run directly
node validate-content.js staging/guides content-schema.json
```

### **Validation Features**
The `validate-content.js` script performs comprehensive checks:

#### **Filename Validation:**
- ✅ Format: `{descriptive-title}-{uniqueId}.mdx`
- ✅ Kebab-case with 8-character hex ID
- ❌ Example of invalid: `My Article.mdx` or `article.mdx`
- ✅ Example of valid: `how-to-parse-json-in-javascript-abc12345.mdx`

#### **Frontmatter Validation:**
- ✅ **Required fields**: title, slug, category, subcategory, description, tags, difficulty, readTime, lastUpdated
- ✅ **Field types**: String, number, array, enum validation
- ✅ **SEO compliance**: Description length (20-200 characters)
- ✅ **Category validation**: Must exist in categories.json
- ✅ **Difficulty validation**: Must be 'beginner', 'intermediate', or 'advanced'

#### **Content Quality Checks:**
- ⚠️ **Content length**: Warns if content < 100 characters
- ⚠️ **Heading structure**: Checks for proper H1 headings
- ⚠️ **Code blocks**: Warns about missing language specifications


### **Validation Output Examples**

#### **✅ Success Example:**
```
🚀 DeepV Code Content Validator
================================
🔍 Validating 2 MDX files in staging/guides

📄 Validating: understanding-react-hooks-def67890.mdx
  ✅ Valid

📄 Validating: javascript-async-patterns-abc12345.mdx
  ✅ Valid

📊 Validation Summary:
✅ All files are valid!
✅ Validation successful! Content is ready for production.
```

#### **❌ Error Example:**
```
📄 Validating: bad-article.mdx
  ❌ Filename must match pattern: {descriptive-title}-{uniqueId}.mdx
  ❌ Missing required field: description
  ❌ difficulty must be one of: beginner, intermediate, advanced
  ⚠️  Content is very short (< 100 characters)

📊 Validation Summary:
❌ Found 3 error(s):
   • bad-article.mdx: Filename must match pattern
   • bad-article.mdx: Missing required field: description
   • bad-article.mdx: difficulty must be one of: beginner, intermediate, advanced
❌ Validation failed! Content cannot be promoted to production.
```

## 📋 **Article Format**

Each article must be an MDX file with proper YAML frontmatter:

```yaml
---
title: "Understanding React Hooks: A Complete Guide"
slug: "understanding-react-hooks-complete-guide"
category: "web-frontend"
subcategory: "react"
description: "Comprehensive guide to React Hooks including useState, useEffect, and custom hooks with practical examples and best practices."
tags: ["react", "hooks", "frontend", "javascript"]
difficulty: "intermediate"
readTime: 15
lastUpdated: "2024-09-18T10:30:00.000Z"
featured: false
---

# Understanding React Hooks: A Complete Guide

React Hooks revolutionized how we write React components...
```

### **Required Fields**
- **title**: String (5-100 characters)
- **slug**: String (kebab-case, unique identifier)
- **category**: Must match categories.json values
- **subcategory**: Must match categories.json subcategories
- **description**: String (20-200 characters, essential for SEO)
- **tags**: Array of strings or comma-separated string
- **difficulty**: "beginner", "intermediate", or "advanced"
- **readTime**: Number (1-60 minutes)
- **lastUpdated**: ISO date string

### **Optional Fields**
- **featured**: Boolean (highlights article)
- **filename**: String (auto-generated if not provided)

## 🔄 **Content Workflow**

### **NEW: JSON-to-MDX Pipeline (Recommended)**

#### **1. Content Generation (Upstream)**
The upstream AI workflow now generates JSON files:
```
staging/json/question_12345_article-title.json
staging/json/question_12345_article-title.json.metadata.json
```

#### **2. JSON to MDX Conversion**
Convert JSON files to validated MDX format:
```bash
npm run convert  # Converts JSON → MDX with auto-corrections
```

#### **3. Validation & Promotion**
```bash
# Full workflow (recommended)
npm run workflow  # convert + validate + promote

# Or step by step
npm run validate  # Validate converted MDX files
npm run promote   # Move to production + commit to GitHub
```

### **Legacy: Direct MDX Pipeline**

#### **1. Content Generation (Upstream)**
Articles are generated by the upstream AI workflow into staging:
```
staging/guides/new-article-abc12345.mdx
staging/config/article-index-update.json
```

#### **2. Validation (Optional)**
Before promoting to production, validate the content:
```bash
npm run validate
```

#### **3. Promotion to Production**

#### **Option A: Validate + Promote (Recommended)**
```bash
npm run promote  # Validates, promotes, and pushes to GitHub
```

#### **Option B: Manual Steps**
Move validated content from staging to production:
```bash
# Manual promotion
mv staging/guides/*.mdx guides/
mv staging/config/article-index-update.json config/article-index.json

# Commit and push
git add .
git commit -m "Add new articles: 2024-09-18"
git push
```

### **4. Automatic Updates**
The main website ([deepvcode.com](https://deepvcode.com)) automatically:
- ✅ **Detects changes** via ISR (Incremental Static Regeneration)
- ✅ **Revalidates content** every 5 minutes
- ✅ **Generates new pages** on-demand
- ✅ **Caches at edge** for fast global delivery

## 🛠️ **Available Scripts**

```bash
npm install          # Install validation dependencies

# JSON-to-MDX Workflow (NEW)
npm run convert      # Convert JSON files to MDX format
npm run workflow     # Full pipeline: convert + validate + promote

# Legacy/Direct Workflow  
npm run validate     # Validate staging content against schema
npm run promote      # Validate + promote + commit to GitHub
```

## 🔧 **Troubleshooting**

### **Common Validation Errors**

#### **Filename Issues:**
```bash
❌ my_article.mdx → ✅ my-article-abc12345.mdx
❌ Article Title.mdx → ✅ article-title-def67890.mdx  
❌ article.mdx → ✅ comprehensive-article-guide-123abc45.mdx
```

#### **Frontmatter Issues:**
```bash
❌ Missing description → ✅ Add 20-200 character description
❌ difficulty: "easy" → ✅ difficulty: "beginner"
❌ tags: "" → ✅ tags: ["javascript", "react"]
❌ readTime: "5 minutes" → ✅ readTime: 5
```

#### **SEO Issues:**
```bash
❌ description: "Too short" → ✅ "Comprehensive guide explaining..."
❌ Description > 200 chars → ✅ Keep under 200 characters
❌ No H1 heading → ✅ Add # Main Title
```

### **Validation Dependencies**
If validation fails with missing modules:
```bash
npm install  # Installs gray-matter for frontmatter parsing
```

## 📊 **Schema Information**

The validation schema (`content-schema.json`) is synchronized from the main repository:
- **Version**: 1.0.0
- **Source**: `nextjs-deepv-docs/config/content-schema.json`
- **Last Updated**: 2024-09-18
- **Update Method**: Manual sync when schema changes (rare)

## 🌐 **Integration**

This repository integrates with:
- **Main Application**: [nextjs-deepv-docs](https://github.com/thaddeus-git/nextjs-deepv-docs)
- **Live Website**: [https://deepvcode.com](https://deepvcode.com)
- **ISR System**: Automatic content updates every 5 minutes
- **CDN**: Global edge caching via Vercel

## 🚨 **Important Notes**

### **DO:**
- ✅ Always validate content before promotion
- ✅ Use proper filename format with unique IDs
- ✅ Include comprehensive descriptions for SEO
- ✅ Test articles locally before staging

### **DON'T:**
- ❌ Edit production files directly (use staging workflow)
- ❌ Skip validation (prevents broken pages)
- ❌ Use spaces or special characters in filenames
- ❌ Leave required frontmatter fields empty

## 📚 **Additional Resources**

- [MDX Documentation](https://mdxjs.com/docs/)
- [Main Repository](https://github.com/thaddeus-git/nextjs-deepv-docs)
- [Live Website](https://deepvcode.com)
- [Content Schema](./content-schema.json)

**This repository enables scalable content management for 100,000+ technical articles with quality validation and seamless ISR integration.** 🚀
