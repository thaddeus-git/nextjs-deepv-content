"""
Simplified Pipeline Implementation - Schema Compliant
====================================================

TDD Implementation with full schema compliance:
- Content schema validation
- Categories.json compliance  
- Code block language requirements
- ISO date format compliance
- Next.js syntax highlighting
"""

import json
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timezone
import urllib.request


class ProcessingTracker:
    """Handles text file tracking for article deduplication"""
    
    def __init__(self, tracker_dir: Path):
        self.tracker_dir = Path(tracker_dir)
        self.processed_file = self.tracker_dir / "processed_ids.txt"
        
    def mark_as_processed(self, stackoverflow_id: str):
        """Mark an article as processed"""
        self.tracker_dir.mkdir(exist_ok=True)
        
        # Read existing IDs
        existing_ids = set()
        if self.processed_file.exists():
            existing_ids = set(line.strip() for line in self.processed_file.read_text().splitlines() if line.strip())
        
        # Add new ID if not already present
        if stackoverflow_id not in existing_ids:
            with open(self.processed_file, 'a') as f:
                f.write(f"{stackoverflow_id}\n")
    
    def is_processed(self, stackoverflow_id: str) -> bool:
        """Check if article was already processed"""
        if not self.processed_file.exists():
            return False
            
        processed_ids = set(line.strip() for line in self.processed_file.read_text().splitlines() if line.strip())
        return stackoverflow_id in processed_ids
    
    def should_process(self, stackoverflow_id: str) -> bool:
        """Check if article should be processed (opposite of is_processed)"""
        return not self.is_processed(stackoverflow_id)


class SchemaValidator:
    """Validates content against the official content schema"""
    
    def __init__(self, schema_file: Optional[Path] = None, categories_file: Optional[Path] = None):
        """Initialize with schema files or download them"""
        self.schema = self._load_schema(schema_file)
        self.categories = self._load_categories(categories_file)
        
    def _load_schema(self, schema_file: Optional[Path]) -> Dict[str, Any]:
        """Load content schema from file or download"""
        if schema_file and schema_file.exists():
            return json.loads(schema_file.read_text())
        
        # Download from upstream
        schema_url = "https://raw.githubusercontent.com/thaddeus-git/nextjs-deepv-docs/main/config/content-schema.json"
        try:
            with urllib.request.urlopen(schema_url) as response:
                return json.loads(response.read().decode())
        except Exception:
            return self._get_fallback_schema()
    
    def _load_categories(self, categories_file: Optional[Path]) -> Dict[str, Any]:
        """Load categories from file or download"""
        if categories_file and categories_file.exists():
            return json.loads(categories_file.read_text())
        
        # Download from upstream
        categories_url = "https://raw.githubusercontent.com/thaddeus-git/nextjs-deepv-docs/main/content/config/categories.json"
        try:
            with urllib.request.urlopen(categories_url) as response:
                return json.loads(response.read().decode())
        except Exception:
            return self._get_fallback_categories()
    
    def _get_fallback_schema(self) -> Dict[str, Any]:
        """Fallback schema if download fails"""
        return {
            "article_schema": {
                "frontmatter_required": [
                    "title", "slug", "category", "subcategory", 
                    "description", "tags", "difficulty", "readTime", "lastUpdated"
                ]
            },
            "requirements": {
                "frontmatter": {
                    "validation_rules": {
                        "title": {"min_length": 5, "max_length": 70},
                        "category": {"values": ["programming-languages", "web-frontend", "databases", "system-devops", "mobile"]},
                        "difficulty": {"values": ["beginner", "intermediate", "advanced"]},
                        "lastUpdated": {"format": "ISO 8601"}
                    }
                }
            }
        }
    
    def _get_fallback_categories(self) -> Dict[str, Any]:
        """Fallback categories if download fails"""
        return {
            "categories": [
                {
                    "id": "programming-languages",
                    "title": "Programming Languages",
                    "subcategories": [
                        {"id": "python", "title": "Python"},
                        {"id": "javascript", "title": "JavaScript"},
                        {"id": "java", "title": "Java"}
                    ]
                },
                {
                    "id": "web-frontend",
                    "title": "Web Frontend",
                    "subcategories": [
                        {"id": "javascript", "title": "JavaScript"},
                        {"id": "css", "title": "CSS"},
                        {"id": "html", "title": "HTML"}
                    ]
                }
            ]
        }
    
    def validate_frontmatter(self, frontmatter: Dict[str, Any]) -> Dict[str, Any]:
        """Validate frontmatter against schema"""
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = self.schema.get("article_schema", {}).get("frontmatter_required", [])
        for field in required_fields:
            if field not in frontmatter:
                errors.append(f"Missing required field: {field}")
        
        # Validate specific fields
        validation_rules = self.schema.get("requirements", {}).get("frontmatter", {}).get("validation_rules", {})
        
        # Title validation
        if "title" in frontmatter:
            title = frontmatter["title"]
            title_rules = validation_rules.get("title", {})
            if len(title) < title_rules.get("min_length", 5):
                errors.append("Title too short (minimum 5 characters)")
            if len(title) > title_rules.get("max_length", 70):
                errors.append("Title too long (maximum 70 characters)")
        
        # Category validation
        if "category" in frontmatter:
            category = frontmatter["category"]
            valid_categories = [cat["id"] for cat in self.categories.get("categories", [])]
            if category not in valid_categories:
                errors.append(f"Invalid category: {category}. Valid categories: {valid_categories}")
        
        # Difficulty validation
        if "difficulty" in frontmatter:
            difficulty = frontmatter["difficulty"]
            valid_difficulties = validation_rules.get("difficulty", {}).get("values", [])
            if difficulty not in valid_difficulties:
                errors.append(f"Invalid difficulty: {difficulty}")
        
        # Date format validation
        if "lastUpdated" in frontmatter:
            date_str = frontmatter["lastUpdated"]
            if not self._validate_iso_date(date_str):
                errors.append("lastUpdated must be in ISO 8601 format with .000Z")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _validate_iso_date(self, date_str: str) -> bool:
        """Validate ISO date format matches JavaScript new Date().toISOString()"""
        # Must match format: 2024-09-18T12:30:00.000Z
        iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$'
        return bool(re.match(iso_pattern, date_str))
    
    def validate_code_blocks(self, content: str) -> Dict[str, Any]:
        """Validate code blocks have required language specifications"""
        errors = []
        warnings = []
        
        # Find all code blocks
        code_blocks = re.findall(r'```([^\n]*)\n(.*?)\n```', content, re.DOTALL)
        
        for i, (language_line, code_content) in enumerate(code_blocks):
            language = language_line.strip()
            
            # Critical: NEVER allow empty language
            if not language:
                errors.append(f"Code block {i+1} missing language specification (CRITICAL: schema requirement)")
            
            # Check if language is supported
            elif not self._is_valid_language(language):
                warnings.append(f"Code block {i+1} uses uncommon language: {language}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "code_blocks_found": len(code_blocks)
        }
    
    def _is_valid_language(self, language: str) -> bool:
        """Check if language is in supported list"""
        supported_languages = {
            # Web frontend
            'javascript', 'typescript', 'html', 'css', 'scss', 'less', 'jsx', 'tsx',
            'vue', 'svelte', 'json', 'xml',
            # Backend
            'python', 'java', 'csharp', 'php', 'ruby', 'go', 'rust', 'kotlin',
            'scala', 'nodejs', 'express', 'fastapi', 'spring', 'django', 'flask',
            # Mobile
            'swift', 'kotlin', 'dart', 'flutter', 'react-native', 'objective-c',
            # Databases
            'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'cassandra', 'sqlite',
            # System/DevOps
            'bash', 'shell', 'powershell', 'dockerfile', 'docker-compose',
            'yaml', 'yml', 'terraform', 'ansible', 'kubernetes',
            # Other
            'c', 'cpp', 'mermaid', 'markdown', 'text', 'plain'
        }
        return language.lower() in supported_languages


class StagingConverter:
    """Handles direct conversion to staging directory with full schema compliance"""
    
    def __init__(self, staging_dir: Path, schema_validator: Optional[SchemaValidator] = None):
        self.staging_dir = Path(staging_dir)
        self.validator = schema_validator or SchemaValidator()
        
        # Schema-compliant language mappings
        self.language_mappings = {
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
            'html': 'html',
            'css': 'css',
            'scss': 'scss',
            'sass': 'scss',
            'sql': 'sql',
            'mysql': 'sql',
            'postgresql': 'sql',
            'java': 'java',
            'c': 'c',
            'cpp': 'cpp',
            'c++': 'cpp',
            'csharp': 'csharp',
            'c#': 'csharp',
            'php': 'php',
            'go': 'go',
            'rust': 'rust',
            'yaml': 'yaml',
            'yml': 'yaml',
            'json': 'json',
            'xml': 'xml',
            'dockerfile': 'dockerfile',
            'docker': 'dockerfile',
            'mermaid': 'mermaid',
            'md': 'markdown',
            'markdown': 'markdown',
            'text': 'text',
            'plain': 'text',
            'txt': 'text'
        }
    
    def convert_to_staging(self, article_data: Dict[str, Any]) -> Path:
        """Convert article data to MDX and write directly to staging"""
        self.staging_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename (schema compliant)
        title = article_data.get("title", "untitled")
        slug = self._generate_slug(title)
        stackoverflow_id = str(article_data.get("metadata", {}).get("stackoverflow_id", "unknown"))
        unique_id = self._generate_unique_id(stackoverflow_id)
        filename = f"{slug}-{unique_id}.mdx"
        
        # Generate MDX content
        mdx_content = self._generate_mdx_content(article_data)
        
        # Validate against schema
        validation_result = self._validate_content(mdx_content)
        if not validation_result["valid"]:
            raise ValueError(f"Schema validation failed: {validation_result['errors']}")
        
        # Write to staging
        staging_path = self.staging_dir / filename
        staging_path.write_text(mdx_content)
        
        return staging_path
    
    def _generate_slug(self, title: str) -> str:
        """Generate schema-compliant kebab-case slug"""
        slug = title.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        slug = slug.strip('-')
        # Ensure it's not too long for filename
        return slug[:50]
    
    def _generate_unique_id(self, stackoverflow_id: str) -> str:
        """Generate unique ID using SHA256 (schema compliant)"""
        salt = "deepv-content-2025"
        hash_input = f"{salt}-{stackoverflow_id}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:8]
    
    def _generate_mdx_content(self, article_data: Dict[str, Any]) -> str:
        """Generate complete MDX content with schema-compliant frontmatter"""
        # Generate frontmatter
        frontmatter = self._generate_frontmatter(article_data)
        
        # Process content for schema compliance
        content = article_data.get("content", "")
        content = self._fix_code_blocks_schema_compliant(content)
        
        return f"{frontmatter}\n\n{content}"
    
    def _generate_frontmatter(self, article_data: Dict[str, Any]) -> str:
        """Generate schema-compliant YAML frontmatter"""
        metadata = article_data.get("metadata", {})
        title = article_data.get("title", "Untitled")
        
        # Ensure title is within schema limits
        if len(title) > 70:
            title = title[:67] + "..."
        elif len(title) < 5:
            title = f"{title} - Programming Guide"
        
        # Map to valid category (simplified for now)
        category = self._map_to_valid_category(metadata.get("tags", []))
        subcategory = self._map_to_valid_subcategory(category, metadata.get("tags", []))
        
        # Generate description (schema compliant)
        description = self._generate_description(title, metadata)
        
        frontmatter = [
            "---",
            f'title: "{title}"',
            f'slug: "{self._generate_slug(title)}"',
            f'category: "{category}"',
            f'subcategory: "{subcategory}"',
            f'description: "{description}"',
            f'tags: {json.dumps(metadata.get("tags", ["programming"]))}',
            f'difficulty: "{metadata.get("difficulty", "intermediate")}"',
            f'readTime: {self._calculate_read_time(article_data.get("content", ""))}',
            f'lastUpdated: "{datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")}"',
            "---"
        ]
        
        return "\n".join(frontmatter)
    
    def _map_to_valid_category(self, tags: List[str]) -> str:
        """Map tags to valid schema category"""
        # Simple mapping logic
        for tag in tags:
            tag_lower = tag.lower()
            if tag_lower in ['javascript', 'typescript', 'html', 'css', 'react', 'vue']:
                return 'web-frontend'
            elif tag_lower in ['python', 'java', 'c++', 'c#', 'ruby', 'go']:
                return 'programming-languages'
            elif tag_lower in ['sql', 'mysql', 'postgresql', 'mongodb']:
                return 'databases'
            elif tag_lower in ['linux', 'docker', 'kubernetes', 'bash']:
                return 'system-devops'
            elif tag_lower in ['ios', 'android', 'swift', 'kotlin']:
                return 'mobile'
        
        return 'programming-languages'  # Default fallback
    
    def _map_to_valid_subcategory(self, category: str, tags: List[str]) -> str:
        """Map to valid subcategory for the given category"""
        # Find the category in the categories list
        categories = self.validator.categories.get("categories", [])
        category_data = None
        for cat in categories:
            if cat["id"] == category:
                category_data = cat
                break
        
        if not category_data:
            return "general"
            
        subcategories = [sub["id"] for sub in category_data.get("subcategories", [])]
        
        # Simple mapping
        for tag in tags:
            tag_lower = tag.lower()
            if tag_lower in subcategories:
                return tag_lower
        
        return subcategories[0] if subcategories else "general"
    
    def _generate_description(self, title: str, metadata: Dict[str, Any]) -> str:
        """Generate schema-compliant description (20-200 chars)"""
        base_desc = f"Learn {title.lower()} with practical examples and best practices."
        
        # Ensure length compliance
        if len(base_desc) < 20:
            base_desc += " Complete programming guide with code examples."
        elif len(base_desc) > 200:
            base_desc = base_desc[:197] + "..."
        
        return base_desc
    
    def _calculate_read_time(self, content: str) -> int:
        """Calculate reading time in minutes (1-60 as per schema)"""
        words = len(content.split())
        # Average reading speed: 200 words per minute
        minutes = max(1, min(60, words // 200))
        return minutes
    
    def _fix_code_blocks_schema_compliant(self, content: str) -> str:
        """Fix code blocks to be 100% schema compliant"""
        def replace_code_block(match):
            language_line = match.group(1).strip()
            code_content = match.group(2)
            
            # CRITICAL: Never allow empty language (schema requirement)
            if not language_line:
                # Smart language detection
                language = self._detect_language_from_content(code_content)
            else:
                # Apply language mappings
                language = self.language_mappings.get(language_line.lower(), language_line.lower())
            
            return f"```{language}\n{code_content}\n```"
        
        # Fix all code blocks
        content = re.sub(r'```([^\n]*)\n(.*?)\n```', replace_code_block, content, flags=re.DOTALL)
        
        # Detect potential Mermaid diagrams and tag them
        content = self._detect_and_tag_mermaid(content)
        
        return content
    
    def _detect_language_from_content(self, code_content: str) -> str:
        """Detect programming language from code content"""
        code_lower = code_content.lower()
        
        # Python detection (more comprehensive)
        if any(keyword in code_lower for keyword in ['def ', 'import ', 'print(', 'if __name__', '= [', 'for ', 'in range(', '.append(', 'len(']):
            return 'python'
        # JavaScript/TypeScript detection
        elif any(keyword in code_lower for keyword in ['function', 'const ', 'let ', '=>', 'console.log', 'var ']):
            return 'javascript'
        # HTML detection
        elif any(keyword in code_lower for keyword in ['<html', '<div', '<span', '<!doctype']):
            return 'html'
        # CSS detection
        elif any(keyword in code_lower for keyword in ['{', '}']) and ':' in code_lower and any(prop in code_lower for prop in ['color', 'margin', 'padding', 'font']):
            return 'css'
        # SQL detection
        elif any(keyword in code_lower for keyword in ['select ', 'insert ', 'update ', 'create table', 'from ', 'where ']):
            return 'sql'
        # Bash detection
        elif any(keyword in code_lower for keyword in ['#!/bin/', '
    
    def _detect_and_tag_mermaid(self, content: str) -> str:
        """Detect potential Mermaid diagrams and tag them properly"""
        # Look for flowchart indicators
        mermaid_indicators = [
            'flowchart td', 'flowchart lr', 'graph td', 'graph lr',
            'sequencediagram', 'classdiagram', 'erdiagram', 'pie title'
        ]
        
        def check_for_mermaid(match):
            language_line = match.group(1).strip()
            code_content = match.group(2).lower()
            
            # If no language specified and looks like mermaid
            if not language_line:
                for indicator in mermaid_indicators:
                    if indicator in code_content:
                        return f"```mermaid\n{match.group(2)}\n```"
            
            return match.group(0)  # Return unchanged
        
        content = re.sub(r'```([^\n]*)\n(.*?)\n```', check_for_mermaid, content, flags=re.DOTALL)
        return content
    
    def _validate_content(self, mdx_content: str) -> Dict[str, Any]:
        """Validate complete MDX content against schema"""
        errors = []
        
        # Extract frontmatter
        frontmatter_match = re.match(r'^---\n(.*?)\n---\n', mdx_content, re.DOTALL)
        if not frontmatter_match:
            errors.append("Missing frontmatter")
            return {"valid": False, "errors": errors}
        
        # Parse frontmatter as YAML (simplified)
        frontmatter_yaml = frontmatter_match.group(1)
        frontmatter = {}
        for line in frontmatter_yaml.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"')
                frontmatter[key] = value
        
        # Validate frontmatter
        fm_validation = self.validator.validate_frontmatter(frontmatter)
        if not fm_validation["valid"]:
            errors.extend(fm_validation["errors"])
        
        # Validate code blocks
        content = mdx_content[frontmatter_match.end():]
        code_validation = self.validator.validate_code_blocks(content)
        if not code_validation["valid"]:
            errors.extend(code_validation["errors"])
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "frontmatter_validation": fm_validation,
            "code_validation": code_validation
        }


class CrawledDataScanner:
    """Handles scanning and processing crawled_data directory"""
    
    def __init__(self, crawled_dir: Path, tracker: Optional[ProcessingTracker] = None):
        self.crawled_dir = Path(crawled_dir)
        self.tracker = tracker
    
    def get_available_articles(self) -> List[Path]:
        """Get all available article files"""
        if not self.crawled_dir.exists():
            return []
            
        return [f for f in self.crawled_dir.glob("question_*.json") if f.is_file()]
    
    def get_unprocessed_articles(self) -> List[Path]:
        """Get articles that haven't been processed yet"""
        all_articles = self.get_available_articles()
        
        if not self.tracker:
            return all_articles
            
        unprocessed = []
        for article_file in all_articles:
            stackoverflow_id = self.extract_id(article_file.name)
            if stackoverflow_id and self.tracker.should_process(stackoverflow_id):
                unprocessed.append(article_file)
                
        return unprocessed
    
    def extract_id(self, filename: str) -> Optional[str]:
        """Extract StackOverflow ID from filename"""
        # Format: question_12345_title.json
        if filename.startswith('question_'):
            parts = filename.split('_')
            if len(parts) >= 2:
                return parts[1]
        
        # Format: processed_question_12345_title.json
        elif filename.startswith('processed_question_'):
            parts = filename.split('_')
            if len(parts) >= 3:
                return parts[2]
                
        return None


class SimplifiedPipeline:
    """Main simplified pipeline orchestrator with full schema compliance"""
    
    def __init__(self, crawled_data_dir: Path, staging_dir: Path, tracker_dir: Path, failed_dir: Optional[Path] = None):
        self.crawled_data_dir = Path(crawled_data_dir)
        self.staging_dir = Path(staging_dir)
        self.failed_dir = Path(failed_dir or tracker_dir / "failed")
        
        # Initialize components
        self.tracker = ProcessingTracker(tracker_dir)
        self.validator = SchemaValidator()
        self.converter = StagingConverter(staging_dir, self.validator)
        self.scanner = CrawledDataScanner(crawled_data_dir, self.tracker)
    
    def process_single_article(self, stackoverflow_id: str) -> Dict[str, Any]:
        """Process a single article by StackOverflow ID with full schema compliance"""
        try:
            # Find article file
            article_file = self._find_article_file(stackoverflow_id)
            if not article_file:
                return {"success": False, "error": f"Article {stackoverflow_id} not found"}
            
            # Check if already processed
            if self.tracker.is_processed(stackoverflow_id):
                return {"success": False, "error": f"Article {stackoverflow_id} already processed"}
            
            # Load article data
            article_data = json.loads(article_file.read_text())
            
            # Simulate AI generation (replace with real OpenRouter call in production)
            processed_article_data = self._simulate_ai_generation(article_data, stackoverflow_id)
            
            # Convert to staging with schema validation
            staging_path = self.converter.convert_to_staging(processed_article_data)
            
            # Mark as processed
            self.tracker.mark_as_processed(stackoverflow_id)
            
            return {
                "success": True,
                "staging_path": staging_path,
                "stackoverflow_id": stackoverflow_id
            }
            
        except Exception as e:
            # Move to failed directory
            self._move_to_failed(stackoverflow_id, str(e))
            return {"success": False, "error": str(e)}
    
    def process_batch(self, count: int) -> Dict[str, Any]:
        """Process multiple articles with schema compliance"""
        results = {"processed": 0, "failed": 0, "skipped": 0}
        
        all_articles = self.scanner.get_available_articles()
        processed_count = 0
        
        for article_file in all_articles:
            if processed_count >= count:
                break
                
            stackoverflow_id = self.scanner.extract_id(article_file.name)
            if not stackoverflow_id:
                continue
                
            if self.tracker.is_processed(stackoverflow_id):
                results["skipped"] += 1
                processed_count += 1  # Count skipped towards total
                continue
                
            result = self.process_single_article(stackoverflow_id)
            if result["success"]:
                results["processed"] += 1
            else:
                results["failed"] += 1
                
            processed_count += 1
                
        return results
    
    def _find_article_file(self, stackoverflow_id: str) -> Optional[Path]:
        """Find article file by StackOverflow ID"""
        for article_file in self.scanner.get_available_articles():
            if self.scanner.extract_id(article_file.name) == stackoverflow_id:
                return article_file
        return None
    
    def _simulate_ai_generation(self, article_data: Dict[str, Any], stackoverflow_id: str) -> Dict[str, Any]:
        """Simulate AI generation with schema-compliant output"""
        # Check if we should use a real OpenRouter client for testing
        try:
            client = OpenRouterClient()
            return client.generate_article(article_data)
        except Exception:
            # Fall back to simulation if client fails or doesn't exist
            pass
        
        title = article_data.get("title", "Untitled")
        question_text = article_data.get("question_text", "")
        tags = article_data.get("tags", ["programming"])
        
        # Generate schema-compliant content
        generated_content = f"""# {title}

## Overview

This comprehensive guide addresses: {question_text[:100]}...

## Solution

```javascript
// Example JavaScript solution
function solutionExample() {{
    console.log("Schema-compliant code block");
    return "Success";
}}
```

## Alternative Approaches

```python
# Python implementation
def alternative_solution():
    print("Every code block has a language!")
    return True
```

## Best Practices

1. Always specify programming language in code blocks
2. Follow schema-compliant frontmatter format
3. Ensure proper Next.js syntax highlighting

```mermaid
flowchart TD
    A[User Input] --> B{{Validation}}
    B -->|Valid| C[Process Request]
    B -->|Invalid| D[Return Error]
    C --> E[Generate Response]
```

## Conclusion

This provides a comprehensive, schema-compliant solution.
"""
        
        return {
            "title": title,
            "content": generated_content,
            "metadata": {
                "stackoverflow_id": stackoverflow_id,
                "tags": tags,
                "difficulty": "intermediate"
            }
        }
    
    def _move_to_failed(self, stackoverflow_id: str, error_message: str):
        """Move failed article to failed directory"""
        self.failed_dir.mkdir(parents=True, exist_ok=True)
        
        # Find and copy original file (don't move, preserve source)
        article_file = self._find_article_file(stackoverflow_id)
        if article_file:
            failed_file = self.failed_dir / article_file.name
            failed_file.write_text(article_file.read_text())
        
        # Create error log
        error_log = self.failed_dir / f"question_{stackoverflow_id}_error.txt"
        with open(error_log, 'w') as f:
            f.write(f"Failed at: {datetime.now()}\n")
            f.write(f"Error: {error_message}\n")


# Mock for testing
class OpenRouterClient:
    """Mock OpenRouter client for testing"""
    
    def generate_article(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock article generation"""
        raise Exception("API Error")  # For testing error handling, 'echo ', 'cd ', 'ls ', 'chmod ', 'grep ']):
            return 'bash'
        # JSON detection
        elif code_content.strip().startswith('{') and '"' in code_content:
            return 'json'
        # YAML detection
        elif ':' in code_content and ('-' in code_content or code_content.count('\n') > 0) and not any(keyword in code_lower for keyword in ['def ', 'function']):
            return 'yaml'
        # List comprehension or Python list operations
        elif any(keyword in code_lower for keyword in ['[x', 'for x in', 'x**', '**2']):
            return 'python'
        else:
            return 'text'
    
    def _detect_and_tag_mermaid(self, content: str) -> str:
        """Detect potential Mermaid diagrams and tag them properly"""
        # Look for flowchart indicators
        mermaid_indicators = [
            'flowchart td', 'flowchart lr', 'graph td', 'graph lr',
            'sequencediagram', 'classdiagram', 'erdiagram', 'pie title'
        ]
        
        def check_for_mermaid(match):
            language_line = match.group(1).strip()
            code_content = match.group(2).lower()
            
            # If no language specified and looks like mermaid
            if not language_line:
                for indicator in mermaid_indicators:
                    if indicator in code_content:
                        return f"```mermaid\n{match.group(2)}\n```"
            
            return match.group(0)  # Return unchanged
        
        content = re.sub(r'```([^\n]*)\n(.*?)\n```', check_for_mermaid, content, flags=re.DOTALL)
        return content
    
    def _validate_content(self, mdx_content: str) -> Dict[str, Any]:
        """Validate complete MDX content against schema"""
        errors = []
        
        # Extract frontmatter
        frontmatter_match = re.match(r'^---\n(.*?)\n---\n', mdx_content, re.DOTALL)
        if not frontmatter_match:
            errors.append("Missing frontmatter")
            return {"valid": False, "errors": errors}
        
        # Parse frontmatter as YAML (simplified)
        frontmatter_yaml = frontmatter_match.group(1)
        frontmatter = {}
        for line in frontmatter_yaml.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"')
                frontmatter[key] = value
        
        # Validate frontmatter
        fm_validation = self.validator.validate_frontmatter(frontmatter)
        if not fm_validation["valid"]:
            errors.extend(fm_validation["errors"])
        
        # Validate code blocks
        content = mdx_content[frontmatter_match.end():]
        code_validation = self.validator.validate_code_blocks(content)
        if not code_validation["valid"]:
            errors.extend(code_validation["errors"])
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "frontmatter_validation": fm_validation,
            "code_validation": code_validation
        }


class CrawledDataScanner:
    """Handles scanning and processing crawled_data directory"""
    
    def __init__(self, crawled_dir: Path, tracker: Optional[ProcessingTracker] = None):
        self.crawled_dir = Path(crawled_dir)
        self.tracker = tracker
    
    def get_available_articles(self) -> List[Path]:
        """Get all available article files"""
        if not self.crawled_dir.exists():
            return []
            
        return [f for f in self.crawled_dir.glob("question_*.json") if f.is_file()]
    
    def get_unprocessed_articles(self) -> List[Path]:
        """Get articles that haven't been processed yet"""
        all_articles = self.get_available_articles()
        
        if not self.tracker:
            return all_articles
            
        unprocessed = []
        for article_file in all_articles:
            stackoverflow_id = self.extract_id(article_file.name)
            if stackoverflow_id and self.tracker.should_process(stackoverflow_id):
                unprocessed.append(article_file)
                
        return unprocessed
    
    def extract_id(self, filename: str) -> Optional[str]:
        """Extract StackOverflow ID from filename"""
        # Format: question_12345_title.json
        if filename.startswith('question_'):
            parts = filename.split('_')
            if len(parts) >= 2:
                return parts[1]
        
        # Format: processed_question_12345_title.json
        elif filename.startswith('processed_question_'):
            parts = filename.split('_')
            if len(parts) >= 3:
                return parts[2]
                
        return None


class SimplifiedPipeline:
    """Main simplified pipeline orchestrator with full schema compliance"""
    
    def __init__(self, crawled_data_dir: Path, staging_dir: Path, tracker_dir: Path, failed_dir: Optional[Path] = None):
        self.crawled_data_dir = Path(crawled_data_dir)
        self.staging_dir = Path(staging_dir)
        self.failed_dir = Path(failed_dir or tracker_dir / "failed")
        
        # Initialize components
        self.tracker = ProcessingTracker(tracker_dir)
        self.validator = SchemaValidator()
        self.converter = StagingConverter(staging_dir, self.validator)
        self.scanner = CrawledDataScanner(crawled_data_dir, self.tracker)
    
    def process_single_article(self, stackoverflow_id: str) -> Dict[str, Any]:
        """Process a single article by StackOverflow ID with full schema compliance"""
        try:
            # Find article file
            article_file = self._find_article_file(stackoverflow_id)
            if not article_file:
                return {"success": False, "error": f"Article {stackoverflow_id} not found"}
            
            # Check if already processed
            if self.tracker.is_processed(stackoverflow_id):
                return {"success": False, "error": f"Article {stackoverflow_id} already processed"}
            
            # Load article data
            article_data = json.loads(article_file.read_text())
            
            # Simulate AI generation (replace with real OpenRouter call in production)
            processed_article_data = self._simulate_ai_generation(article_data, stackoverflow_id)
            
            # Convert to staging with schema validation
            staging_path = self.converter.convert_to_staging(processed_article_data)
            
            # Mark as processed
            self.tracker.mark_as_processed(stackoverflow_id)
            
            return {
                "success": True,
                "staging_path": staging_path,
                "stackoverflow_id": stackoverflow_id
            }
            
        except Exception as e:
            # Move to failed directory
            self._move_to_failed(stackoverflow_id, str(e))
            return {"success": False, "error": str(e)}
    
    def process_batch(self, count: int) -> Dict[str, Any]:
        """Process multiple articles with schema compliance"""
        results = {"processed": 0, "failed": 0, "skipped": 0}
        
        all_articles = self.scanner.get_available_articles()
        processed_count = 0
        
        for article_file in all_articles:
            if processed_count >= count:
                break
                
            stackoverflow_id = self.scanner.extract_id(article_file.name)
            if not stackoverflow_id:
                continue
                
            if self.tracker.is_processed(stackoverflow_id):
                results["skipped"] += 1
                processed_count += 1  # Count skipped towards total
                continue
                
            result = self.process_single_article(stackoverflow_id)
            if result["success"]:
                results["processed"] += 1
            else:
                results["failed"] += 1
                
            processed_count += 1
                
        return results
    
    def _find_article_file(self, stackoverflow_id: str) -> Optional[Path]:
        """Find article file by StackOverflow ID"""
        for article_file in self.scanner.get_available_articles():
            if self.scanner.extract_id(article_file.name) == stackoverflow_id:
                return article_file
        return None
    
    def _simulate_ai_generation(self, article_data: Dict[str, Any], stackoverflow_id: str) -> Dict[str, Any]:
        """Simulate AI generation with schema-compliant output"""
        # Check if we should use a real OpenRouter client for testing
        try:
            client = OpenRouterClient()
            return client.generate_article(article_data)
        except Exception:
            # Fall back to simulation if client fails or doesn't exist
            pass
        
        title = article_data.get("title", "Untitled")
        question_text = article_data.get("question_text", "")
        tags = article_data.get("tags", ["programming"])
        
        # Generate schema-compliant content
        generated_content = f"""# {title}

## Overview

This comprehensive guide addresses: {question_text[:100]}...

## Solution

```javascript
// Example JavaScript solution
function solutionExample() {{
    console.log("Schema-compliant code block");
    return "Success";
}}
```

## Alternative Approaches

```python
# Python implementation
def alternative_solution():
    print("Every code block has a language!")
    return True
```

## Best Practices

1. Always specify programming language in code blocks
2. Follow schema-compliant frontmatter format
3. Ensure proper Next.js syntax highlighting

```mermaid
flowchart TD
    A[User Input] --> B{{Validation}}
    B -->|Valid| C[Process Request]
    B -->|Invalid| D[Return Error]
    C --> E[Generate Response]
```

## Conclusion

This provides a comprehensive, schema-compliant solution.
"""
        
        return {
            "title": title,
            "content": generated_content,
            "metadata": {
                "stackoverflow_id": stackoverflow_id,
                "tags": tags,
                "difficulty": "intermediate"
            }
        }
    
    def _move_to_failed(self, stackoverflow_id: str, error_message: str):
        """Move failed article to failed directory"""
        self.failed_dir.mkdir(parents=True, exist_ok=True)
        
        # Find and copy original file (don't move, preserve source)
        article_file = self._find_article_file(stackoverflow_id)
        if article_file:
            failed_file = self.failed_dir / article_file.name
            failed_file.write_text(article_file.read_text())
        
        # Create error log
        error_log = self.failed_dir / f"question_{stackoverflow_id}_error.txt"
        with open(error_log, 'w') as f:
            f.write(f"Failed at: {datetime.now()}\n")
            f.write(f"Error: {error_message}\n")


# Mock for testing
class OpenRouterClient:
    """Mock OpenRouter client for testing"""
    
    def generate_article(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock article generation"""
        raise Exception("API Error")  # For testing error handling, 'echo ', 'cd ', 'ls ', 'chmod ', 'grep ']):
            return 'bash'
        # JSON detection
        elif code_content.strip().startswith('{') and '"' in code_content:
            return 'json'
        # YAML detection
        elif ':' in code_content and ('-' in code_content or code_content.count('\n') > 0) and not any(keyword in code_lower for keyword in ['def ', 'function']):
            return 'yaml'
        # List comprehension or Python list operations
        elif any(keyword in code_lower for keyword in ['[x', 'for x in', 'x**', '**2']):
            return 'python'
        else:
            return 'text'
    
    def _detect_and_tag_mermaid(self, content: str) -> str:
        """Detect potential Mermaid diagrams and tag them properly"""
        # Look for flowchart indicators
        mermaid_indicators = [
            'flowchart td', 'flowchart lr', 'graph td', 'graph lr',
            'sequencediagram', 'classdiagram', 'erdiagram', 'pie title'
        ]
        
        def check_for_mermaid(match):
            language_line = match.group(1).strip()
            code_content = match.group(2).lower()
            
            # If no language specified and looks like mermaid
            if not language_line:
                for indicator in mermaid_indicators:
                    if indicator in code_content:
                        return f"```mermaid\n{match.group(2)}\n```"
            
            return match.group(0)  # Return unchanged
        
        content = re.sub(r'```([^\n]*)\n(.*?)\n```', check_for_mermaid, content, flags=re.DOTALL)
        return content
    
    def _validate_content(self, mdx_content: str) -> Dict[str, Any]:
        """Validate complete MDX content against schema"""
        errors = []
        
        # Extract frontmatter
        frontmatter_match = re.match(r'^---\n(.*?)\n---\n', mdx_content, re.DOTALL)
        if not frontmatter_match:
            errors.append("Missing frontmatter")
            return {"valid": False, "errors": errors}
        
        # Parse frontmatter as YAML (simplified)
        frontmatter_yaml = frontmatter_match.group(1)
        frontmatter = {}
        for line in frontmatter_yaml.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"')
                frontmatter[key] = value
        
        # Validate frontmatter
        fm_validation = self.validator.validate_frontmatter(frontmatter)
        if not fm_validation["valid"]:
            errors.extend(fm_validation["errors"])
        
        # Validate code blocks
        content = mdx_content[frontmatter_match.end():]
        code_validation = self.validator.validate_code_blocks(content)
        if not code_validation["valid"]:
            errors.extend(code_validation["errors"])
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "frontmatter_validation": fm_validation,
            "code_validation": code_validation
        }


class CrawledDataScanner:
    """Handles scanning and processing crawled_data directory"""
    
    def __init__(self, crawled_dir: Path, tracker: Optional[ProcessingTracker] = None):
        self.crawled_dir = Path(crawled_dir)
        self.tracker = tracker
    
    def get_available_articles(self) -> List[Path]:
        """Get all available article files"""
        if not self.crawled_dir.exists():
            return []
            
        return [f for f in self.crawled_dir.glob("question_*.json") if f.is_file()]
    
    def get_unprocessed_articles(self) -> List[Path]:
        """Get articles that haven't been processed yet"""
        all_articles = self.get_available_articles()
        
        if not self.tracker:
            return all_articles
            
        unprocessed = []
        for article_file in all_articles:
            stackoverflow_id = self.extract_id(article_file.name)
            if stackoverflow_id and self.tracker.should_process(stackoverflow_id):
                unprocessed.append(article_file)
                
        return unprocessed
    
    def extract_id(self, filename: str) -> Optional[str]:
        """Extract StackOverflow ID from filename"""
        # Format: question_12345_title.json
        if filename.startswith('question_'):
            parts = filename.split('_')
            if len(parts) >= 2:
                return parts[1]
        
        # Format: processed_question_12345_title.json
        elif filename.startswith('processed_question_'):
            parts = filename.split('_')
            if len(parts) >= 3:
                return parts[2]
                
        return None


class SimplifiedPipeline:
    """Main simplified pipeline orchestrator with full schema compliance"""
    
    def __init__(self, crawled_data_dir: Path, staging_dir: Path, tracker_dir: Path, failed_dir: Optional[Path] = None):
        self.crawled_data_dir = Path(crawled_data_dir)
        self.staging_dir = Path(staging_dir)
        self.failed_dir = Path(failed_dir or tracker_dir / "failed")
        
        # Initialize components
        self.tracker = ProcessingTracker(tracker_dir)
        self.validator = SchemaValidator()
        self.converter = StagingConverter(staging_dir, self.validator)
        self.scanner = CrawledDataScanner(crawled_data_dir, self.tracker)
    
    def process_single_article(self, stackoverflow_id: str) -> Dict[str, Any]:
        """Process a single article by StackOverflow ID with full schema compliance"""
        try:
            # Find article file
            article_file = self._find_article_file(stackoverflow_id)
            if not article_file:
                return {"success": False, "error": f"Article {stackoverflow_id} not found"}
            
            # Check if already processed
            if self.tracker.is_processed(stackoverflow_id):
                return {"success": False, "error": f"Article {stackoverflow_id} already processed"}
            
            # Load article data
            article_data = json.loads(article_file.read_text())
            
            # Simulate AI generation (replace with real OpenRouter call in production)
            processed_article_data = self._simulate_ai_generation(article_data, stackoverflow_id)
            
            # Convert to staging with schema validation
            staging_path = self.converter.convert_to_staging(processed_article_data)
            
            # Mark as processed
            self.tracker.mark_as_processed(stackoverflow_id)
            
            return {
                "success": True,
                "staging_path": staging_path,
                "stackoverflow_id": stackoverflow_id
            }
            
        except Exception as e:
            # Move to failed directory
            self._move_to_failed(stackoverflow_id, str(e))
            return {"success": False, "error": str(e)}
    
    def process_batch(self, count: int) -> Dict[str, Any]:
        """Process multiple articles with schema compliance"""
        results = {"processed": 0, "failed": 0, "skipped": 0}
        
        all_articles = self.scanner.get_available_articles()
        processed_count = 0
        
        for article_file in all_articles:
            if processed_count >= count:
                break
                
            stackoverflow_id = self.scanner.extract_id(article_file.name)
            if not stackoverflow_id:
                continue
                
            if self.tracker.is_processed(stackoverflow_id):
                results["skipped"] += 1
                processed_count += 1  # Count skipped towards total
                continue
                
            result = self.process_single_article(stackoverflow_id)
            if result["success"]:
                results["processed"] += 1
            else:
                results["failed"] += 1
                
            processed_count += 1
                
        return results
    
    def _find_article_file(self, stackoverflow_id: str) -> Optional[Path]:
        """Find article file by StackOverflow ID"""
        for article_file in self.scanner.get_available_articles():
            if self.scanner.extract_id(article_file.name) == stackoverflow_id:
                return article_file
        return None
    
    def _simulate_ai_generation(self, article_data: Dict[str, Any], stackoverflow_id: str) -> Dict[str, Any]:
        """Simulate AI generation with schema-compliant output"""
        # Check if we should use a real OpenRouter client for testing
        try:
            client = OpenRouterClient()
            return client.generate_article(article_data)
        except Exception:
            # Fall back to simulation if client fails or doesn't exist
            pass
        
        title = article_data.get("title", "Untitled")
        question_text = article_data.get("question_text", "")
        tags = article_data.get("tags", ["programming"])
        
        # Generate schema-compliant content
        generated_content = f"""# {title}

## Overview

This comprehensive guide addresses: {question_text[:100]}...

## Solution

```javascript
// Example JavaScript solution
function solutionExample() {{
    console.log("Schema-compliant code block");
    return "Success";
}}
```

## Alternative Approaches

```python
# Python implementation
def alternative_solution():
    print("Every code block has a language!")
    return True
```

## Best Practices

1. Always specify programming language in code blocks
2. Follow schema-compliant frontmatter format
3. Ensure proper Next.js syntax highlighting

```mermaid
flowchart TD
    A[User Input] --> B{{Validation}}
    B -->|Valid| C[Process Request]
    B -->|Invalid| D[Return Error]
    C --> E[Generate Response]
```

## Conclusion

This provides a comprehensive, schema-compliant solution.
"""
        
        return {
            "title": title,
            "content": generated_content,
            "metadata": {
                "stackoverflow_id": stackoverflow_id,
                "tags": tags,
                "difficulty": "intermediate"
            }
        }
    
    def _move_to_failed(self, stackoverflow_id: str, error_message: str):
        """Move failed article to failed directory"""
        self.failed_dir.mkdir(parents=True, exist_ok=True)
        
        # Find and copy original file (don't move, preserve source)
        article_file = self._find_article_file(stackoverflow_id)
        if article_file:
            failed_file = self.failed_dir / article_file.name
            failed_file.write_text(article_file.read_text())
        
        # Create error log
        error_log = self.failed_dir / f"question_{stackoverflow_id}_error.txt"
        with open(error_log, 'w') as f:
            f.write(f"Failed at: {datetime.now()}\n")
            f.write(f"Error: {error_message}\n")


# Mock for testing
class OpenRouterClient:
    """Mock OpenRouter client for testing"""
    
    def generate_article(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock article generation"""
        raise Exception("API Error")  # For testing error handling, 'echo ', 'cd ', 'ls ', 'chmod ', 'grep ']):
            return 'bash'
        # JSON detection
        elif code_content.strip().startswith('{') and '"' in code_content:
            return 'json'
        # YAML detection
        elif ':' in code_content and ('-' in code_content or code_content.count('\n') > 0) and not any(keyword in code_lower for keyword in ['def ', 'function']):
            return 'yaml'
        # List comprehension or Python list operations
        elif any(keyword in code_lower for keyword in ['[x', 'for x in', 'x**', '**2']):
            return 'python'
        else:
            return 'text'
    
    def _detect_and_tag_mermaid(self, content: str) -> str:
        """Detect potential Mermaid diagrams and tag them properly"""
        # Look for flowchart indicators
        mermaid_indicators = [
            'flowchart td', 'flowchart lr', 'graph td', 'graph lr',
            'sequencediagram', 'classdiagram', 'erdiagram', 'pie title'
        ]
        
        def check_for_mermaid(match):
            language_line = match.group(1).strip()
            code_content = match.group(2).lower()
            
            # If no language specified and looks like mermaid
            if not language_line:
                for indicator in mermaid_indicators:
                    if indicator in code_content:
                        return f"```mermaid\n{match.group(2)}\n```"
            
            return match.group(0)  # Return unchanged
        
        content = re.sub(r'```([^\n]*)\n(.*?)\n```', check_for_mermaid, content, flags=re.DOTALL)
        return content
    
    def _validate_content(self, mdx_content: str) -> Dict[str, Any]:
        """Validate complete MDX content against schema"""
        errors = []
        
        # Extract frontmatter
        frontmatter_match = re.match(r'^---\n(.*?)\n---\n', mdx_content, re.DOTALL)
        if not frontmatter_match:
            errors.append("Missing frontmatter")
            return {"valid": False, "errors": errors}
        
        # Parse frontmatter as YAML (simplified)
        frontmatter_yaml = frontmatter_match.group(1)
        frontmatter = {}
        for line in frontmatter_yaml.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"')
                frontmatter[key] = value
        
        # Validate frontmatter
        fm_validation = self.validator.validate_frontmatter(frontmatter)
        if not fm_validation["valid"]:
            errors.extend(fm_validation["errors"])
        
        # Validate code blocks
        content = mdx_content[frontmatter_match.end():]
        code_validation = self.validator.validate_code_blocks(content)
        if not code_validation["valid"]:
            errors.extend(code_validation["errors"])
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "frontmatter_validation": fm_validation,
            "code_validation": code_validation
        }


class CrawledDataScanner:
    """Handles scanning and processing crawled_data directory"""
    
    def __init__(self, crawled_dir: Path, tracker: Optional[ProcessingTracker] = None):
        self.crawled_dir = Path(crawled_dir)
        self.tracker = tracker
    
    def get_available_articles(self) -> List[Path]:
        """Get all available article files"""
        if not self.crawled_dir.exists():
            return []
            
        return [f for f in self.crawled_dir.glob("question_*.json") if f.is_file()]
    
    def get_unprocessed_articles(self) -> List[Path]:
        """Get articles that haven't been processed yet"""
        all_articles = self.get_available_articles()
        
        if not self.tracker:
            return all_articles
            
        unprocessed = []
        for article_file in all_articles:
            stackoverflow_id = self.extract_id(article_file.name)
            if stackoverflow_id and self.tracker.should_process(stackoverflow_id):
                unprocessed.append(article_file)
                
        return unprocessed
    
    def extract_id(self, filename: str) -> Optional[str]:
        """Extract StackOverflow ID from filename"""
        # Format: question_12345_title.json
        if filename.startswith('question_'):
            parts = filename.split('_')
            if len(parts) >= 2:
                return parts[1]
        
        # Format: processed_question_12345_title.json
        elif filename.startswith('processed_question_'):
            parts = filename.split('_')
            if len(parts) >= 3:
                return parts[2]
                
        return None


class SimplifiedPipeline:
    """Main simplified pipeline orchestrator with full schema compliance"""
    
    def __init__(self, crawled_data_dir: Path, staging_dir: Path, tracker_dir: Path, failed_dir: Optional[Path] = None):
        self.crawled_data_dir = Path(crawled_data_dir)
        self.staging_dir = Path(staging_dir)
        self.failed_dir = Path(failed_dir or tracker_dir / "failed")
        
        # Initialize components
        self.tracker = ProcessingTracker(tracker_dir)
        self.validator = SchemaValidator()
        self.converter = StagingConverter(staging_dir, self.validator)
        self.scanner = CrawledDataScanner(crawled_data_dir, self.tracker)
    
    def process_single_article(self, stackoverflow_id: str) -> Dict[str, Any]:
        """Process a single article by StackOverflow ID with full schema compliance"""
        try:
            # Find article file
            article_file = self._find_article_file(stackoverflow_id)
            if not article_file:
                return {"success": False, "error": f"Article {stackoverflow_id} not found"}
            
            # Check if already processed
            if self.tracker.is_processed(stackoverflow_id):
                return {"success": False, "error": f"Article {stackoverflow_id} already processed"}
            
            # Load article data
            article_data = json.loads(article_file.read_text())
            
            # Simulate AI generation (replace with real OpenRouter call in production)
            processed_article_data = self._simulate_ai_generation(article_data, stackoverflow_id)
            
            # Convert to staging with schema validation
            staging_path = self.converter.convert_to_staging(processed_article_data)
            
            # Mark as processed
            self.tracker.mark_as_processed(stackoverflow_id)
            
            return {
                "success": True,
                "staging_path": staging_path,
                "stackoverflow_id": stackoverflow_id
            }
            
        except Exception as e:
            # Move to failed directory
            self._move_to_failed(stackoverflow_id, str(e))
            return {"success": False, "error": str(e)}
    
    def process_batch(self, count: int) -> Dict[str, Any]:
        """Process multiple articles with schema compliance"""
        results = {"processed": 0, "failed": 0, "skipped": 0}
        
        all_articles = self.scanner.get_available_articles()
        processed_count = 0
        
        for article_file in all_articles:
            if processed_count >= count:
                break
                
            stackoverflow_id = self.scanner.extract_id(article_file.name)
            if not stackoverflow_id:
                continue
                
            if self.tracker.is_processed(stackoverflow_id):
                results["skipped"] += 1
                processed_count += 1  # Count skipped towards total
                continue
                
            result = self.process_single_article(stackoverflow_id)
            if result["success"]:
                results["processed"] += 1
            else:
                results["failed"] += 1
                
            processed_count += 1
                
        return results
    
    def _find_article_file(self, stackoverflow_id: str) -> Optional[Path]:
        """Find article file by StackOverflow ID"""
        for article_file in self.scanner.get_available_articles():
            if self.scanner.extract_id(article_file.name) == stackoverflow_id:
                return article_file
        return None
    
    def _simulate_ai_generation(self, article_data: Dict[str, Any], stackoverflow_id: str) -> Dict[str, Any]:
        """Simulate AI generation with schema-compliant output"""
        # Check if we should use a real OpenRouter client for testing
        try:
            client = OpenRouterClient()
            return client.generate_article(article_data)
        except Exception:
            # Fall back to simulation if client fails or doesn't exist
            pass
        
        title = article_data.get("title", "Untitled")
        question_text = article_data.get("question_text", "")
        tags = article_data.get("tags", ["programming"])
        
        # Generate schema-compliant content
        generated_content = f"""# {title}

## Overview

This comprehensive guide addresses: {question_text[:100]}...

## Solution

```javascript
// Example JavaScript solution
function solutionExample() {{
    console.log("Schema-compliant code block");
    return "Success";
}}
```

## Alternative Approaches

```python
# Python implementation
def alternative_solution():
    print("Every code block has a language!")
    return True
```

## Best Practices

1. Always specify programming language in code blocks
2. Follow schema-compliant frontmatter format
3. Ensure proper Next.js syntax highlighting

```mermaid
flowchart TD
    A[User Input] --> B{{Validation}}
    B -->|Valid| C[Process Request]
    B -->|Invalid| D[Return Error]
    C --> E[Generate Response]
```

## Conclusion

This provides a comprehensive, schema-compliant solution.
"""
        
        return {
            "title": title,
            "content": generated_content,
            "metadata": {
                "stackoverflow_id": stackoverflow_id,
                "tags": tags,
                "difficulty": "intermediate"
            }
        }
    
    def _move_to_failed(self, stackoverflow_id: str, error_message: str):
        """Move failed article to failed directory"""
        self.failed_dir.mkdir(parents=True, exist_ok=True)
        
        # Find and copy original file (don't move, preserve source)
        article_file = self._find_article_file(stackoverflow_id)
        if article_file:
            failed_file = self.failed_dir / article_file.name
            failed_file.write_text(article_file.read_text())
        
        # Create error log
        error_log = self.failed_dir / f"question_{stackoverflow_id}_error.txt"
        with open(error_log, 'w') as f:
            f.write(f"Failed at: {datetime.now()}\n")
            f.write(f"Error: {error_message}\n")


# Mock for testing
class OpenRouterClient:
    """Mock OpenRouter client for testing"""
    
    def generate_article(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock article generation"""
        raise Exception("API Error")  # For testing error handling