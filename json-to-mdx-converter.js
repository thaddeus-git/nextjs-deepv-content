#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

/**
 * JSON to MDX Converter for DeepV Code Content Repository
 * Converts JSON files from upstream AI generator to MDX format
 * Updates article index and manages staging/production workflow
 */

class JsonToMdxConverter {
  constructor() {
    this.config = {
      jsonInputDir: './staging/json',
      mdxOutputDir: './staging/guides',
      articleIndexPath: './config/article-index.json',
      stagingIndexPath: './staging/config/article-index-update.json',
      categoriesPath: './config/categories.json',
      processedDir: './staging/json/processed',
      errorDir: './staging/json/errors',
      // GitHub URLs for latest schemas
      githubUrls: {
        contentSchema: 'https://raw.githubusercontent.com/thaddeus-git/nextjs-deepv-docs/main/config/content-schema.json',
        categories: 'https://raw.githubusercontent.com/thaddeus-git/nextjs-deepv-docs/main/content/config/categories.json'
      }
    };
    
    this.categories = null;
    this.contentSchema = null;
    this.articleIndex = this.loadArticleIndex();
    this.processedFiles = [];
    this.errorFiles = [];
    
    // Code block language mappings (matches upstream)
    this.languageMappings = {
      'js': 'javascript',
      'jsx': 'jsx', 
      'ts': 'typescript',
      'tsx': 'tsx',
      'py': 'python',
      'python3': 'python',
      'sh': 'bash',
      'shell': 'bash',
      'zsh': 'bash',
      'cmd': 'powershell',
      'yml': 'yaml',
      'yaml': 'yaml',
      'dockerfile': 'docker',
      'html': 'html',
      'css': 'css',
      'scss': 'scss',
      'sql': 'sql',
      'json': 'json',
      'xml': 'xml',
      'md': 'markdown',
      'markdown': 'markdown',
      'mermaid': 'mermaid',
      'text': 'text',
      'plain': 'text',
      'txt': 'text',
      'output': 'output',
      'console': 'output', 
      'config': 'config',
      'conf': 'config'
    };
  }

  async fetchFromGitHub(url, fallbackPath) {
    try {
      const https = require('https');
      return new Promise((resolve, reject) => {
        https.get(url, (response) => {
          let data = '';
          response.on('data', (chunk) => data += chunk);
          response.on('end', () => {
            try {
              resolve(JSON.parse(data));
            } catch (parseError) {
              reject(parseError);
            }
          });
        }).on('error', reject);
      });
    } catch (error) {
      console.log(`⚠️  Failed to fetch from GitHub: ${url}, using local fallback`);
      try {
        const localFile = fs.readFileSync(fallbackPath, 'utf8');
        return JSON.parse(localFile);
      } catch (localError) {
        console.error(`❌ Failed to load local fallback: ${fallbackPath}:`, localError.message);
        throw localError;
      }
    }
  }

  async loadCategories() {
    if (this.categories) return this.categories;
    
    try {
      console.log('🔄 Fetching latest categories from GitHub...');
      this.categories = await this.fetchFromGitHub(
        this.config.githubUrls.categories, 
        this.config.categoriesPath
      );
      console.log('✅ Categories loaded successfully');
      return this.categories;
    } catch (error) {
      console.error('❌ Failed to load categories:', error.message);
      process.exit(1);
    }
  }

  async loadContentSchema() {
    if (this.contentSchema) return this.contentSchema;
    
    try {
      console.log('🔄 Fetching latest content schema from GitHub...');
      this.contentSchema = await this.fetchFromGitHub(
        this.config.githubUrls.contentSchema,
        './content-schema.json'
      );
      console.log('✅ Content schema loaded successfully');
      return this.contentSchema;
    } catch (error) {
      console.error('❌ Failed to load content schema:', error.message);
      process.exit(1);
    }
  }

  loadArticleIndex() {
    try {
      if (fs.existsSync(this.config.articleIndexPath)) {
        const indexFile = fs.readFileSync(this.config.articleIndexPath, 'utf8');
        const index = JSON.parse(indexFile);
        
        // Ensure backward compatibility by filtering articles with required fields
        if (index.articles) {
          index.articles = index.articles.filter(article => 
            article.id && article.technology && article.publishedAt
          );
        }
        
        return index;
      }
      return { articles: [], lastUpdated: new Date().toISOString() };
    } catch (error) {
      console.error('⚠️  Failed to load article index, starting fresh:', error.message);
      return { articles: [], lastUpdated: new Date().toISOString() };
    }
  }

  ensureDirectories() {
    const dirs = [
      this.config.mdxOutputDir,
      this.config.processedDir,
      this.config.errorDir,
      path.dirname(this.config.stagingIndexPath)
    ];
    
    dirs.forEach(dir => {
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
        console.log(`📁 Created directory: ${dir}`);
      }
    });
  }

  mapCategory(category, subcategory, tags = []) {
    // Category mapping for common mismatches
    const categoryMappings = {
      'programming': 'programming-languages',
      'devops': 'system-devops', 
      'backend': 'web-backend',
      'frontend': 'web-frontend',
      'database': 'databases',
      'db': 'databases'
    };

    // Smart mapping based on tags and technology
    if (category === 'programming' || !this.categories.categories.some(cat => cat.id === category)) {
      const tagLower = tags.map(tag => tag.toLowerCase());
      
      // Database-related
      if (tagLower.some(tag => ['sql', 'mysql', 'postgresql', 'mongodb', 'database', 'sql-server', 'oracle', 'sqlite'].includes(tag))) {
        return 'databases';
      }
      
      // DevOps/System related
      if (tagLower.some(tag => ['docker', 'kubernetes', 'aws', 'azure', 'gcp', 'linux', 'bash', 'shell', 'devops', 'cloud'].includes(tag))) {
        return 'system-devops';
      }
      
      // Frontend related
      if (tagLower.some(tag => ['javascript', 'react', 'vue', 'angular', 'css', 'html', 'frontend', 'ui', 'web'].includes(tag))) {
        return 'web-frontend';
      }
      
      // Mobile related  
      if (tagLower.some(tag => ['android', 'ios', 'mobile', 'swift', 'kotlin'].includes(tag))) {
        return 'mobile';
      }
    }

    return categoryMappings[category] || category;
  }

  mapSubcategory(category, subcategory, tags = []) {
    // If subcategory is 'general', try to map to something more specific
    if (subcategory === 'general') {
      const tagLower = tags.map(tag => tag.toLowerCase());
      
      if (category === 'databases') {
        if (tagLower.includes('sql-server')) return 'sql';
        if (tagLower.includes('mysql')) return 'mysql'; 
        if (tagLower.includes('postgresql')) return 'postgresql';
        if (tagLower.includes('mongodb')) return 'mongodb';
        return 'sql'; // default for databases
      }
      
      if (category === 'programming-languages') {
        // Map based on tags
        if (tagLower.some(tag => ['java'].includes(tag))) return 'java';
        if (tagLower.some(tag => ['python'].includes(tag))) return 'python';
        if (tagLower.some(tag => ['javascript', 'js', 'npm', 'node'].includes(tag))) return 'javascript';
        if (tagLower.some(tag => ['c#', 'csharp'].includes(tag))) return 'csharp';
        if (tagLower.some(tag => ['cpp', 'c++'].includes(tag))) return 'cpp';
        if (tagLower.some(tag => ['c'].includes(tag))) return 'c';
        if (tagLower.some(tag => ['go', 'golang'].includes(tag))) return 'go';
        if (tagLower.some(tag => ['php'].includes(tag))) return 'php';
        if (tagLower.some(tag => ['ruby'].includes(tag))) return 'ruby';
        if (tagLower.some(tag => ['rust'].includes(tag))) return 'rust';
        
        // For miscellaneous programming that doesn't fit - default to python
        return 'python';
      }
      
      if (category === 'system-devops') {
        if (tagLower.some(tag => ['linux', 'bash', 'shell'].includes(tag))) return 'linux';
        if (tagLower.some(tag => ['docker', 'container'].includes(tag))) return 'containerization';
        if (tagLower.some(tag => ['aws', 'azure', 'gcp', 'cloud'].includes(tag))) return 'cloud';
        if (tagLower.some(tag => ['git', 'github', 'gitlab'].includes(tag))) return 'version-control';
        return 'shell'; // default
      }
      
      if (category === 'web-frontend') {
        if (tagLower.some(tag => ['css'].includes(tag))) return 'css';
        if (tagLower.some(tag => ['html'].includes(tag))) return 'html';
        return 'javascript'; // default
      }
    }
    
    return subcategory;
  }

  generateUniqueId(stackoverflowId) {
    // SHA256-based unique ID generation (matches upstream algorithm)
    const salt = "deepv-content-2025";
    const hashInput = `${salt}-${stackoverflowId}`;
    return crypto.createHash('sha256').update(hashInput).digest('hex').substring(0, 8);
  }

  processCodeBlocks(content) {
    // Apply language mappings to code blocks for better syntax highlighting
    let processedContent = content.replace(/```(\w+)/g, (match, language) => {
      const mappedLanguage = this.languageMappings[language.toLowerCase()] || language.toLowerCase();
      return '```' + mappedLanguage;
    });

    // Detect potential Mermaid diagrams (basic heuristic)
    processedContent = processedContent.replace(/```\n(graph|flowchart|sequenceDiagram|classDiagram|gitgraph)/g, '```mermaid\n$1');
    
    return processedContent;
  }

  processImagePlaceholders(content) {
    // Convert standard markdown images to PLACEHOLDER format for upstream compatibility
    // This helps maintain consistency with the expected schema format
    return content.replace(/!\[([^\]]+)\]\((?!PLACEHOLDER:)([^)]+)\)/g, '![$1](PLACEHOLDER: $1 - $2)');
  }

  validateJsonStructure(jsonData, filename) {
    const errors = [];
    
    // Check main structure
    if (!jsonData.metadata) {
      errors.push('Missing metadata object');
    }
    
    if (!jsonData.content) {
      errors.push('Missing content field');
    }

    if (jsonData.metadata) {
      let meta = jsonData.metadata;
      
      // Auto-fix categories using smart mapping
      if (meta.category && meta.tags) {
        const mappedCategory = this.mapCategory(meta.category, meta.subcategory, meta.tags);
        const mappedSubcategory = this.mapSubcategory(mappedCategory, meta.subcategory, meta.tags);
        
        if (mappedCategory !== meta.category) {
          console.log(`  🔄 Auto-mapping category: ${meta.category} → ${mappedCategory}`);
          meta.category = mappedCategory;
        }
        
        if (mappedSubcategory !== meta.subcategory) {
          console.log(`  🔄 Auto-mapping subcategory: ${meta.subcategory} → ${mappedSubcategory}`);
          meta.subcategory = mappedSubcategory;
        }
        
        // Update the jsonData reference
        jsonData.metadata = meta;
      }

      // Validate/generate unique ID using consistent algorithm
      if (meta.sourceStackOverflowId) {
        const expectedUniqueId = this.generateUniqueId(meta.sourceStackOverflowId);
        
        if (!meta.uniqueId) {
          console.log(`  🔧 Generated missing uniqueId: ${expectedUniqueId}`);
          meta.uniqueId = expectedUniqueId;
          jsonData.metadata = meta;
        } else if (meta.uniqueId !== expectedUniqueId) {
          console.log(`  🔧 Corrected uniqueId: ${meta.uniqueId} → ${expectedUniqueId}`);
          meta.uniqueId = expectedUniqueId;
          jsonData.metadata = meta;
        }
      }
      
      // Required fields validation
      const requiredFields = [
        'title', 'slug', 'uniqueId', 'category', 'subcategory', 
        'description', 'tags', 'difficulty', 'readTime'
      ];
      
      requiredFields.forEach(field => {
        if (!meta[field]) {
          errors.push(`Missing required metadata field: ${field}`);
        }
      });

      // Validate specific field formats
      if (meta.uniqueId && !/^[a-f0-9]{8}$/.test(meta.uniqueId)) {
        errors.push('uniqueId must be 8-character hex string');
      }

      if (meta.difficulty && !['beginner', 'intermediate', 'advanced'].includes(meta.difficulty)) {
        errors.push('difficulty must be: beginner, intermediate, or advanced');
      }

      if (meta.description && (meta.description.length < 20 || meta.description.length > 200)) {
        errors.push('description must be 20-200 characters');
      }

      // Validate category exists
      if (meta.category) {
        const categoryExists = this.categories.categories.some(cat => cat.id === meta.category);
        if (!categoryExists) {
          errors.push(`Invalid category: ${meta.category}`);
        }
        
        // Validate subcategory if category is valid
        if (categoryExists && meta.subcategory) {
          const category = this.categories.categories.find(cat => cat.id === meta.category);
          const subcategoryExists = category.subcategories.some(sub => sub.id === meta.subcategory);
          if (!subcategoryExists) {
            errors.push(`Invalid subcategory: ${meta.subcategory} for category: ${meta.category}`);
          }
        }
      }

      // Quality metrics validation (simple checks)
      if (meta.qualityMetrics) {
        const metrics = meta.qualityMetrics;
        
        if (metrics.wordCount && metrics.wordCount < 100) {
          errors.push('Content appears too short (< 100 words)');
        }
        
        if (metrics.codeBlocks && metrics.codeBlocks === 0) {
          console.log(`  ⚠️  No code blocks found - may not be technical content`);
        }
        
        if (metrics.wordCount && metrics.codeBlocks) {
          const codeToWordRatio = metrics.codeBlocks / (metrics.wordCount / 100);
          if (codeToWordRatio > 50) {
            console.log(`  ⚠️  Very high code-to-text ratio (${codeToWordRatio.toFixed(1)}%)`);
          }
        }
      } else {
        console.log(`  ⚠️  No quality metrics provided`);
      }
    }

    return errors;
  }

  truncateTitle(title, maxLength = null) {
    // Schema v3.2.0: No character limit for titles
    // Google indexes entire title. For optimal SERP display, consider ~50-60 chars
    // but longer titles still provide SEO value
    
    if (maxLength === null) {
      // No truncation needed - return as is
      return title;
    }
    
    if (title.length <= maxLength) return title;
    
    // Optional truncation if maxLength specified
    const truncated = title.substring(0, maxLength);
    const lastSpaceIndex = truncated.lastIndexOf(' ');
    
    if (lastSpaceIndex > maxLength * 0.7) {
      return truncated.substring(0, lastSpaceIndex);
    }
    
    return truncated;
  }

  normalizeSlug(slug) {
    // Replace underscores with hyphens and ensure kebab-case
    return slug
      .replace(/_/g, '-')
      .replace(/[^a-z0-9-]/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '');
  }

  formatISODate(dateString) {
    try {
      // Handle various date formats and ensure proper ISO string
      const date = new Date(dateString);
      if (isNaN(date.getTime())) {
        return new Date().toISOString();
      }
      return date.toISOString();
    } catch (error) {
      return new Date().toISOString();
    }
  }

  generateMdxFrontmatter(metadata) {
    // Clean and validate fields (v3.2.0: no title length limit)
    const title = this.truncateTitle(metadata.title);
    const slug = this.normalizeSlug(metadata.slug);
    const lastUpdated = this.formatISODate(metadata.generatedAt || metadata.publishedAt);
    
    return `---
title: "${title.replace(/"/g, '\\"')}"
slug: "${slug}"
category: "${metadata.category}"
subcategory: "${metadata.subcategory}"
description: "${metadata.description.replace(/"/g, '\\"')}"
tags: ${JSON.stringify(metadata.tags)}
difficulty: "${metadata.difficulty}"
readTime: ${metadata.readTime}
lastUpdated: "${lastUpdated}"
featured: ${metadata.featured || false}
---

`;
  }

  convertJsonToMdx(jsonData, filename) {
    let metadata = jsonData.metadata;
    let content = jsonData.content;
    
    // Process code blocks for proper language mapping
    content = this.processCodeBlocks(content);
    
    // Process images to use PLACEHOLDER format
    content = this.processImagePlaceholders(content);
    
    // Apply all transformations to metadata (v3.2.0: no title truncation)
    metadata.title = this.truncateTitle(metadata.title);
    metadata.slug = this.normalizeSlug(metadata.slug);
    
    // Generate MDX filename
    const mdxFilename = `${metadata.slug}-${metadata.uniqueId}.mdx`;
    const mdxPath = path.join(this.config.mdxOutputDir, mdxFilename);
    
    // Generate frontmatter
    const frontmatter = this.generateMdxFrontmatter(metadata);
    
    // Combine frontmatter and content
    const mdxContent = frontmatter + content;
    
    // Write MDX file
    fs.writeFileSync(mdxPath, mdxContent, 'utf8');
    
    return {
      mdxFilename,
      mdxPath,
      metadata: {
        title: metadata.title,
        slug: metadata.slug,
        uniqueId: metadata.uniqueId,
        category: metadata.category,
        subcategory: metadata.subcategory,
        description: metadata.description,
        tags: metadata.tags,
        difficulty: metadata.difficulty,
        readTime: metadata.readTime,
        lastUpdated: this.formatISODate(metadata.generatedAt || metadata.publishedAt),
        featured: metadata.featured || false,
        filename: mdxFilename,
        sourceStackOverflowId: metadata.sourceStackOverflowId,
        qualityMetrics: metadata.qualityMetrics,
        technology: metadata.technology,
        publishedAt: metadata.publishedAt,
        generatedAt: metadata.generatedAt
      }
    };
  }

  updateArticleIndex(newArticles) {
    // Remove any existing articles with same slug to avoid duplicates
    const existingArticles = this.articleIndex.articles.filter(article => 
      !newArticles.some(newArticle => newArticle.metadata.slug === article.slug)
    );
    
    // Add new articles with proper schema format
    const updatedArticles = [
      ...existingArticles,
      ...newArticles.map(article => ({
        id: article.metadata.uniqueId,
        title: article.metadata.title,
        slug: article.metadata.slug,
        category: article.metadata.category,
        subcategory: article.metadata.subcategory,
        difficulty: article.metadata.difficulty,
        technology: article.metadata.technology || this.getTechnologyFromTags(article.metadata.tags),
        readTime: article.metadata.readTime,
        publishedAt: article.metadata.publishedAt || article.metadata.generatedAt || new Date().toISOString(),
        featured: article.metadata.featured || false,
        description: article.metadata.description,
        tags: article.metadata.tags,
        filename: `${article.metadata.slug}-${article.metadata.uniqueId}.mdx`,
        lastUpdated: article.metadata.generatedAt || new Date().toISOString()
      }))
    ];

    // Extract unique categories and technologies
    const categories = [...new Set(updatedArticles.map(article => article.category))].sort();
    const technologies = [...new Set(updatedArticles.map(article => article.technology).filter(Boolean))].sort();
    
    const updatedIndex = {
      lastUpdated: new Date().toISOString(),
      totalArticles: updatedArticles.length,
      categories: categories,
      technologies: technologies,
      articles: updatedArticles
    };
    
    // Write staging index
    fs.writeFileSync(
      this.config.stagingIndexPath, 
      JSON.stringify(updatedIndex, null, 2),
      'utf8'
    );
    
    console.log(`📊 Updated article index: ${updatedArticles.length} total articles`);
    return updatedIndex;
  }

  getTechnologyFromTags(tags) {
    // Map tags to human-readable technology names
    const technologyMappings = {
      'javascript': 'JavaScript',
      'js': 'JavaScript',
      'python': 'Python',
      'py': 'Python',
      'java': 'Java',
      'sql': 'SQL',
      'sql-server': 'SQL Server',
      'mysql': 'MySQL',
      'postgresql': 'PostgreSQL',
      'mongodb': 'MongoDB',
      'bash': 'Bash',
      'shell': 'Shell',
      'linux': 'Linux',
      'windows': 'Windows',
      'docker': 'Docker',
      'aws': 'AWS',
      'html': 'HTML',
      'css': 'CSS',
      'react': 'React',
      'node': 'Node.js',
      'npm': 'npm'
    };

    for (const tag of tags) {
      const tech = technologyMappings[tag.toLowerCase()];
      if (tech) return tech;
    }
    
    // Default fallback
    return 'Programming';
  }

  moveProcessedFile(filename, success = true) {
    const sourcePath = path.join(this.config.jsonInputDir, filename);
    const targetDir = success ? this.config.processedDir : this.config.errorDir;
    const targetPath = path.join(targetDir, filename);
    
    try {
      fs.renameSync(sourcePath, targetPath);
      
      // Also move metadata file if it exists
      const metadataFilename = filename + '.metadata.json';
      const metadataSourcePath = path.join(this.config.jsonInputDir, metadataFilename);
      const metadataTargetPath = path.join(targetDir, metadataFilename);
      
      if (fs.existsSync(metadataSourcePath)) {
        fs.renameSync(metadataSourcePath, metadataTargetPath);
      }
    } catch (error) {
      console.error(`⚠️  Failed to move ${filename}:`, error.message);
    }
  }

  logError(filename, errors) {
    const errorLog = {
      filename,
      errors,
      timestamp: new Date().toISOString()
    };
    
    const errorLogPath = path.join(
      this.config.errorDir, 
      `${path.basename(filename, '.json')}_errors.json`
    );
    
    fs.writeFileSync(errorLogPath, JSON.stringify(errorLog, null, 2), 'utf8');
  }

  async processJsonFiles() {
    this.ensureDirectories();
    
    console.log('🚀 DeepV Code JSON to MDX Converter');
    console.log('=====================================');
    
    // Load latest schemas from GitHub
    await this.loadCategories();
    await this.loadContentSchema();
    
    // Get all JSON files (excluding metadata files and error files)
    const jsonFiles = fs.readdirSync(this.config.jsonInputDir)
      .filter(file => file.endsWith('.json') && 
                     !file.endsWith('.metadata.json') && 
                     !file.endsWith('_errors.json'));
    
    if (jsonFiles.length === 0) {
      console.log('📭 No JSON files found in staging/json directory');
      return;
    }
    
    console.log(`🔍 Found ${jsonFiles.length} JSON files to process\\n`);
    
    const successfulConversions = [];
    
    jsonFiles.forEach(filename => {
      console.log(`📄 Processing: ${filename}`);
      
      try {
        const filePath = path.join(this.config.jsonInputDir, filename);
        const fileContent = fs.readFileSync(filePath, 'utf8');
        const jsonData = JSON.parse(fileContent);
        
        // Validate JSON structure
        const validationErrors = this.validateJsonStructure(jsonData, filename);
        
        if (validationErrors.length > 0) {
          console.log(`  ❌ Validation failed:`);
          validationErrors.forEach(error => {
            console.log(`     • ${error}`);
          });
          
          this.logError(filename, validationErrors);
          this.moveProcessedFile(filename, false);
          this.errorFiles.push(filename);
          return;
        }
        
        // Convert to MDX
        const result = this.convertJsonToMdx(jsonData, filename);
        successfulConversions.push(result);
        
        console.log(`  ✅ Converted to: ${result.mdxFilename}`);
        
        // Move to processed directory
        this.moveProcessedFile(filename, true);
        this.processedFiles.push(filename);
        
      } catch (error) {
        console.log(`  ❌ Processing failed: ${error.message}`);
        this.logError(filename, [error.message]);
        this.moveProcessedFile(filename, false);
        this.errorFiles.push(filename);
      }
    });
    
    // Update article index if there were successful conversions
    if (successfulConversions.length > 0) {
      this.updateArticleIndex(successfulConversions);
    }
    
    this.printSummary(jsonFiles.length, successfulConversions.length);
  }

  printSummary(totalFiles, successCount) {
    console.log('\\n📊 Conversion Summary:');
    console.log('======================');
    console.log(`📁 Total files processed: ${totalFiles}`);
    console.log(`✅ Successful conversions: ${successCount}`);
    console.log(`❌ Failed conversions: ${this.errorFiles.length}`);
    
    if (successCount > 0) {
      console.log(`📝 MDX files created in: ${this.config.mdxOutputDir}`);
      console.log(`📊 Article index updated: ${this.config.stagingIndexPath}`);
    }
    
    if (this.processedFiles.length > 0) {
      console.log(`📦 Processed files moved to: ${this.config.processedDir}`);
    }
    
    if (this.errorFiles.length > 0) {
      console.log(`💥 Error files moved to: ${this.config.errorDir}`);
      console.log('\\n⚠️  Check error logs for details on failed conversions');
    }
    
    if (successCount === totalFiles && totalFiles > 0) {
      console.log('\\n🎉 All files converted successfully! Ready for validation and promotion.');
    }
  }

  // Static method for CLI usage
  static async run() {
    const converter = new JsonToMdxConverter();
    await converter.processJsonFiles();
  }
}

// CLI execution
if (require.main === module) {
  JsonToMdxConverter.run().catch(console.error);
}

module.exports = JsonToMdxConverter;