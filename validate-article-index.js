#!/usr/bin/env node

/**
 * Article Index Validator for DeepV Code
 * Validates article-index.json structure and consistency
 * 
 * Usage: node validate-article-index.js <index-file> <index-schema> <categories-file>
 * Example: node validate-article-index.js ../nextjs-deepv-content/staging/config/article-index-update.json ./config/article-index-schema.json ./content/config/categories.json
 */

const fs = require('fs');
const path = require('path');

// Colors for console output
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m'
};

function log(color, message) {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

class ArticleIndexValidator {
  constructor(schemaPath, categoriesPath) {
    this.schema = this.loadJSON(schemaPath, 'index schema');
    this.categories = this.loadJSON(categoriesPath, 'categories');
    this.errors = [];
    this.warnings = [];
  }

  loadJSON(filePath, description) {
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      return JSON.parse(content);
    } catch (error) {
      log('red', `❌ Failed to load ${description} from ${filePath}: ${error.message}`);
      process.exit(1);
    }
  }

  isValidISODate(dateString) {
    const date = new Date(dateString);
    return date instanceof Date && !isNaN(date) && date.toISOString() === dateString;
  }

  validateStructure(index) {
    const required = this.schema.structure.required_fields;
    const errors = [];

    // Check required fields
    for (const field of required) {
      if (!(field in index)) {
        errors.push(`Missing required field: ${field}`);
      }
    }

    return errors;
  }

  validateLastUpdated(lastUpdated) {
    if (!this.isValidISODate(lastUpdated)) {
      return `lastUpdated must be valid ISO date string (got: ${lastUpdated})`;
    }
    return null;
  }

  validateTotalArticles(index) {
    if (typeof index.totalArticles !== 'number') {
      return 'totalArticles must be a number';
    }
    
    if (index.articles && index.totalArticles !== index.articles.length) {
      return `totalArticles (${index.totalArticles}) does not match articles.length (${index.articles.length})`;
    }

    return null;
  }

  validateCategories(index) {
    const errors = [];
    const validCategories = this.categories.categories.map(c => c.id);

    if (!Array.isArray(index.categories)) {
      errors.push('categories must be an array');
      return errors;
    }

    for (const category of index.categories) {
      if (!validCategories.includes(category)) {
        errors.push(`Invalid category: ${category}. Valid: ${validCategories.join(', ')}`);
      }
    }

    return errors;
  }

  validateTechnologies(index) {
    const errors = [];

    if (!Array.isArray(index.technologies)) {
      errors.push('technologies must be an array');
      return errors;
    }

    // Check for consistency with articles
    if (index.articles) {
      const indexTechnologies = new Set(index.technologies);
      const articleTechnologies = new Set(index.articles.map(a => a.technology));
      
      for (const tech of articleTechnologies) {
        if (!indexTechnologies.has(tech)) {
          errors.push(`Article technology '${tech}' not listed in technologies array`);
        }
      }
    }

    return errors;
  }

  validateArticle(article, index) {
    const errors = [];
    const required = this.schema.structure.validation_rules.articles.items.required_fields;

    // Check required fields
    for (const field of required) {
      if (!(field in article)) {
        errors.push(`Article ${article.id || 'unknown'}: Missing required field: ${field}`);
      }
    }

    // Validate specific fields
    if (article.id && !/^[a-f0-9]{8}$/.test(article.id)) {
      errors.push(`Article ${article.id}: ID must be 8-character hex string`);
    }

    if (article.title && article.title.length < 5) {
      errors.push(`Article ${article.id}: Title must be at least 5 characters (current: ${article.title.length})`);
    }

    if (article.slug && !/^[a-z0-9-]+$/.test(article.slug)) {
      errors.push(`Article ${article.id}: Slug must be kebab-case`);
    }

    if (article.difficulty && !['beginner', 'intermediate', 'advanced'].includes(article.difficulty)) {
      errors.push(`Article ${article.id}: Difficulty must be beginner, intermediate, or advanced`);
    }

    if (article.readTime && (typeof article.readTime !== 'number' || article.readTime < 1 || article.readTime > 60)) {
      errors.push(`Article ${article.id}: readTime must be number between 1-60`);
    }

    if (article.lastUpdated && !this.isValidISODate(article.lastUpdated)) {
      errors.push(`Article ${article.id}: lastUpdated must be valid ISO date string`);
    }

    if (article.filename && !/^[a-z0-9-]+-[a-f0-9]{8}\.mdx$/.test(article.filename)) {
      errors.push(`Article ${article.id}: filename must match pattern {title}-{id}.mdx`);
    }

    // Validate filename-ID consistency
    if (article.filename && article.id) {
      const filenameId = article.filename.match(/-([a-f0-9]{8})\.mdx$/);
      if (!filenameId || filenameId[1] !== article.id) {
        errors.push(`Article ${article.id}: ID does not match filename hex ID`);
      }
    }

    // Validate category exists
    if (article.category) {
      const validCategories = this.categories.categories.map(c => c.id);
      if (!validCategories.includes(article.category)) {
        errors.push(`Article ${article.id}: Invalid category ${article.category}`);
      }
    }

    // Validate subcategory exists for category
    if (article.category && article.subcategory) {
      const categoryObj = this.categories.categories.find(c => c.id === article.category);
      if (categoryObj) {
        const validSubcategories = categoryObj.subcategories.map(s => s.id);
        if (!validSubcategories.includes(article.subcategory)) {
          errors.push(`Article ${article.id}: Invalid subcategory ${article.subcategory} for category ${article.category}`);
        }
      }
    }

    return errors;
  }

  validateConsistency(index) {
    const errors = [];

    if (!index.articles) return errors;

    // Category consistency
    const indexCategories = new Set(index.categories || []);
    const articleCategories = new Set(index.articles.map(a => a.category));
    
    for (const category of articleCategories) {
      if (!indexCategories.has(category)) {
        errors.push(`Article category '${category}' not listed in categories array`);
      }
    }

    // Technology consistency  
    const indexTechnologies = new Set(index.technologies || []);
    const articleTechnologies = new Set(index.articles.map(a => a.technology));
    
    for (const tech of articleTechnologies) {
      if (!indexTechnologies.has(tech)) {
        errors.push(`Article technology '${tech}' not listed in technologies array`);
      }
    }

    return errors;
  }

  validateIndex(indexPath) {
    log('cyan', `\n🔍 Validating Article Index: ${path.basename(indexPath)}`);

    if (!fs.existsSync(indexPath)) {
      log('red', `❌ Index file not found: ${indexPath}`);
      return false;
    }

    try {
      const index = JSON.parse(fs.readFileSync(indexPath, 'utf8'));

      // Structure validation
      const structureErrors = this.validateStructure(index);
      structureErrors.forEach(error => {
        this.errors.push(error);
        log('red', `  ❌ ${error}`);
      });

      // Field validation
      if (index.lastUpdated) {
        const dateError = this.validateLastUpdated(index.lastUpdated);
        if (dateError) {
          this.errors.push(dateError);
          log('red', `  ❌ ${dateError}`);
        }
      }

      const totalError = this.validateTotalArticles(index);
      if (totalError) {
        this.errors.push(totalError);
        log('red', `  ❌ ${totalError}`);
      }

      const categoryErrors = this.validateCategories(index);
      categoryErrors.forEach(error => {
        this.errors.push(error);
        log('red', `  ❌ ${error}`);
      });

      const technologyErrors = this.validateTechnologies(index);
      technologyErrors.forEach(error => {
        this.errors.push(error);
        log('red', `  ❌ ${error}`);
      });

      // Article validation
      if (index.articles && Array.isArray(index.articles)) {
        log('blue', `  📄 Validating ${index.articles.length} articles...`);
        index.articles.forEach(article => {
          const articleErrors = this.validateArticle(article, index);
          articleErrors.forEach(error => {
            this.errors.push(error);
            log('red', `  ❌ ${error}`);
          });
        });
      }

      // Consistency validation
      const consistencyErrors = this.validateConsistency(index);
      consistencyErrors.forEach(error => {
        this.errors.push(error);
        log('red', `  ❌ ${error}`);
      });

      if (this.errors.length === 0) {
        log('green', `  ✅ Article index validation passed`);
        return true;
      }

      return false;

    } catch (error) {
      this.errors.push(`Failed to parse index JSON: ${error.message}`);
      log('red', `  ❌ Failed to parse: ${error.message}`);
      return false;
    }
  }

  printSummary() {
    log('cyan', '\n📊 Article Index Validation Summary:');
    
    if (this.errors.length === 0) {
      log('green', `✅ Article index is valid!`);
    } else {
      log('red', `❌ Found ${this.errors.length} error(s):`);
      this.errors.forEach(error => log('red', `   • ${error}`));
    }

    if (this.warnings.length > 0) {
      log('yellow', `⚠️  Found ${this.warnings.length} warning(s):`);
      this.warnings.forEach(warning => log('yellow', `   • ${warning}`));
    }

    return this.errors.length === 0;
  }
}

// Main execution
function main() {
  const args = process.argv.slice(2);
  
  if (args.length < 3) {
    log('red', 'Usage: node validate-article-index.js <index-file> <index-schema> <categories-file>');
    log('yellow', 'Example: node validate-article-index.js ../nextjs-deepv-content/staging/config/article-index-update.json ./config/article-index-schema.json ./content/config/categories.json');
    process.exit(1);
  }

  const [indexFile, schemaFile, categoriesFile] = args;

  log('cyan', '🚀 DeepV Code Article Index Validator');
  log('cyan', '====================================');

  const validator = new ArticleIndexValidator(schemaFile, categoriesFile);
  const isValid = validator.validateIndex(indexFile);
  const summary = validator.printSummary();

  if (!summary) {
    log('red', '\n❌ Article index validation failed!');
    process.exit(1);
  } else {
    log('green', '\n✅ Article index validation successful!');
    process.exit(0);
  }
}

if (require.main === module) {
  main();
}

module.exports = { ArticleIndexValidator };