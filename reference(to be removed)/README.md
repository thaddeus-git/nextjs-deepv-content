# Reference Materials for Downstream Processing

This folder contains reference materials for the downstream JSON → MDX conversion process.

## 📁 Directory Structure

### `schemas/`
- **Downloaded schemas** from upstream requirements
- `content-schema.json` - Content validation requirements
- `categories.json` - Valid category/subcategory mappings
- `article-index-schema.json` - Article index structure
- `content-templates.json` - MDX templates and examples
- `upstream-schemas-index.json` - Master schema index

### `examples/`
- **Sample JSON outputs** from AI generation
- **Example MDX conversions**
- **Test data** for validation

### `tdd-tests/`
- **Complete TDD implementation** with 11/12 passing tests
- **Schema validation tests**
- **Pipeline integration tests**
- Use as reference for robust downstream implementation

### `mdx-conversion/`
- **Working MDX conversion pipeline** 
- `simplified_pipeline.py` - Schema-compliant conversion logic
- `run_simplified_workflow.py` - Production-ready pipeline
- **Code block language detection and mapping**
- **Frontmatter generation with schema compliance**

### `docs/`
- `example.prompt` - **AI prompt template** (protected from modification)
- `original-workflow/` - Complete original workflow for reference
- **Architecture documentation**

## 🎯 Key Components for Downstream

### **JSON → MDX Conversion Logic**
- Schema-compliant frontmatter generation
- Code block language mapping (js→javascript, py→python)
- Mermaid diagram detection and tagging
- Title length constraints (5-70 chars)
- ISO date format validation

### **Content Processing**
- Category/subcategory mapping using `categories.json`
- Technology extraction from tags
- Slug generation (kebab-case)
- Unique ID generation (SHA256-based)
- Read time calculation

### **Validation & Quality Control**
- Complete schema validation against `content-schema.json`
- Frontmatter validation
- Code block language validation
- URL pattern compliance (`/guides/{slug}-{id}`)

## 🚀 Usage for Downstream

1. **Study the TDD tests** to understand expected behavior
2. **Reference the schemas** for validation requirements
3. **Use the MDX conversion logic** as implementation guide
4. **Follow the examples** for proper output format

## ⚠️ Important Notes

- **Do not modify** `example.prompt` - it's the protected AI template
- **Always validate** against the latest schemas
- **Maintain** the unique ID generation algorithm for consistency
- **Follow** the file naming conventions for proper integration