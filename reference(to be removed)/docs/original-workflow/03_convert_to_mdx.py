#!/usr/bin/env python3
"""
03_convert_to_mdx.py - Convert generated articles to MDX format for Next.js
DeepV StackOverflow Workflow - Standalone Version
"""

import json
import argparse
import sys
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add modules directory for imports
sys.path.append(str(Path(__file__).parent.parent / "modules"))

from config_manager import ConfigManager
from path_resolver import PathResolver
from schema_manager import SchemaManager
from category_mapper import CategoryMapper


class MDXConverter:
    """Handles conversion of generated articles to MDX format"""
    
    def __init__(self, config_path: str = None):
        self.config = ConfigManager(config_path)
        self.schema_manager = SchemaManager(Path(__file__).parent.parent)
        self.category_mapper = CategoryMapper(self.schema_manager)
        self.resolver = PathResolver(self.config)
        
        print("🔄 MDX Converter Initialized")
        
        # Ensure schemas are updated
        if not self.schema_manager.ensure_schemas_updated():
            print("⚠️ Warning: Schema validation may be incomplete")
        if self.config.is_debug_mode():
            self.config.print_config_summary()
    
    def enhance_tags(self, base_tags: List[str], metadata: Dict[str, Any]) -> List[str]:
        """Enhance tags based on config-driven rules"""
        # Get tag enhancement config
        tag_config = self.config.config.get('tag_enhancement', {})
        category_rules = tag_config.get('category_rules', {})
        max_tags = tag_config.get('max_tags', 5)
        preserve_original = tag_config.get('preserve_original', True)
        
        # Start with original tags if preserving
        enhanced_tags = list(base_tags) if (preserve_original and base_tags) else []
        existing_tags_lower = [tag.lower() for tag in enhanced_tags]
        
        # Get category and subcategory
        category = metadata.get("category", "")
        subcategory = metadata.get("subcategory", "")
        
        # Apply category-specific rules
        if category in category_rules:
            subcategory_rules = category_rules[category].get('subcategory_rules', {})
            if subcategory in subcategory_rules:
                auto_tags = subcategory_rules[subcategory].get('auto_tags', [])
                
                # Add auto tags if not already present
                for tag in auto_tags:
                    if tag.lower() not in existing_tags_lower:
                        enhanced_tags.append(tag)
                        existing_tags_lower.append(tag.lower())
        
        # Limit to max tags
        return enhanced_tags[:max_tags]
    
    def generate_mdx_frontmatter(self, metadata: Dict[str, Any]) -> str:
        """Generate schema-compliant MDX frontmatter from article metadata"""
        from datetime import datetime
        
        # Get original tags and content for intelligent mapping
        original_tags = metadata.get("tags", [])
        title = metadata.get("title", "")
        description = metadata.get("description", "")
        
        # Ensure title length ≤ 70 characters for downstream validation
        if len(title) > 70:
            title = title[:67] + "..."
            print(f"📏 Title truncated to 70 chars: {title}")
        
        # Intelligent category mapping
        current_category = metadata.get("category", "")
        current_subcategory = metadata.get("subcategory", "")
        
        # Validate and fix category/subcategory if needed
        category, subcategory = self.category_mapper.validate_and_fix_category(
            current_category, current_subcategory, original_tags, title, description
        )
        
        # Enhance tags based on the final category assignment
        enhanced_tags = self.category_mapper.enhance_tags_for_category(original_tags, category, subcategory)
        
        frontmatter_lines = ["---"]
        
        # Required fields per content-schema.json
        frontmatter_lines.append(f'title: "{title.replace('"', '\\"')}"')
        frontmatter_lines.append(f'slug: "{metadata.get("slug", "")}"')
        frontmatter_lines.append(f'category: "{category}"')
        frontmatter_lines.append(f'subcategory: "{subcategory}"')
        frontmatter_lines.append(f'description: "{description.replace('"', '\\"')}"')
        frontmatter_lines.append(f'difficulty: "{metadata.get("difficulty", "intermediate")}"')
        frontmatter_lines.append(f'readTime: {metadata.get("readTime", 5)}')
        
        # Required: lastUpdated in ISO format (JavaScript Date().toISOString() compatible)
        from datetime import timezone
        current_time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        frontmatter_lines.append(f'lastUpdated: "{current_time}"')
        
        # Tags as YAML array
        if enhanced_tags:
            frontmatter_lines.append("tags:")
            for tag in enhanced_tags:
                frontmatter_lines.append(f'  - "{tag}"')
        else:
            frontmatter_lines.append("tags: []")
        
        # Optional fields per schema
        frontmatter_lines.append(f'featured: {str(metadata.get("featured", False)).lower()}')
        
        frontmatter_lines.append("---")
        
        # Validate the generated frontmatter
        frontmatter_dict = {
            "title": title,
            "slug": metadata.get("slug", ""),
            "category": category,
            "subcategory": subcategory,
            "description": description,
            "tags": enhanced_tags,
            "difficulty": metadata.get("difficulty", "intermediate"),
            "readTime": metadata.get("readTime", 5),
            "lastUpdated": current_time,
            "featured": metadata.get("featured", False)
        }
        
        validation = self.schema_manager.validate_frontmatter(frontmatter_dict)
        if not validation["valid"]:
            print(f"⚠️ Frontmatter validation warnings: {validation['errors']}")
        
        return "\n".join(frontmatter_lines)
    
    def clean_markdown_content(self, content: str) -> str:
        """Clean and optimize markdown content for MDX"""
        # Remove any potential frontmatter from content
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                content = parts[2].strip()
        
        # Fix common markdown issues
        content = self.fix_code_blocks(content)
        content = self.fix_mermaid_diagrams(content)
        content = self.fix_headers(content)
        content = self.fix_links(content)
        
        return content.strip()
    
    def fix_code_blocks(self, content: str) -> str:
        """Fix code block formatting and ensure proper syntax highlighting"""
        # Common language mappings for better syntax highlighting
        language_mappings = {
            'js': 'javascript',
            'ts': 'typescript',
            'py': 'python',
            'sh': 'bash',
            'shell': 'bash',
            'cmd': 'bash',
            'powershell': 'powershell',
            'ps1': 'powershell',
            'yml': 'yaml',
            'dockerfile': 'docker',
        }
        
        def replace_language(match):
            lang = match.group(1).lower() if match.group(1) else ''
            if lang in language_mappings:
                lang = language_mappings[lang]
            return f"```{lang}"
        
        # Fix language specifiers in code blocks
        content = re.sub(r'```(\w+)?', replace_language, content)
        
        # Fix unmatched code blocks by ensuring they're properly paired
        # Count existing delimiters
        delimiter_count = content.count('```')
        
        # If odd number, add a closing delimiter at the end
        if delimiter_count % 2 != 0:
            content += '\n```'
        
        return content
    
    def fix_mermaid_diagrams(self, content: str) -> str:
        """Fix Mermaid diagram formatting for Nextra/MDX compatibility"""
        # Ensure mermaid blocks are properly formatted
        content = re.sub(r'```mermaid\s*\n(.*?)\n```', r'```mermaid\n\1\n```', content, flags=re.DOTALL)
        
        return content
    
    def fix_headers(self, content: str) -> str:
        """Fix header formatting and ensure proper hierarchy"""
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Ensure headers have proper spacing
            if line.startswith('#'):
                # Add space after # if missing
                line = re.sub(r'^(#+)([^\s])', r'\1 \2', line)
                # Remove excessive #
                line = re.sub(r'^#{7,}', '######', line)
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def fix_links(self, content: str) -> str:
        """Fix and validate links in content"""
        # Remove or fix broken internal links
        content = re.sub(r'\[([^\]]+)\]\(#[^)]+\)', r'\1', content)  # Remove anchor links
        
        # Ensure external links are properly formatted
        content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'[\1](\2)', content)
        
        return content
    
    def generate_mdx_filename(self, metadata: Dict[str, Any]) -> str:
        """Generate MDX filename following Next.js flat structure"""
        slug = metadata.get('slug', 'article')
        unique_id = metadata.get('uniqueId', 'unknown')
        
        # Flat structure: {slug}-{id}.mdx
        return f"{slug}-{unique_id}.mdx"
    
    def validate_mdx_content(self, content: str) -> Dict[str, Any]:
        """Validate MDX content and return quality metrics"""
        validation = {
            'is_valid': True,
            'issues': [],
            'warnings': [],
            'metrics': {}
        }
        
        # Check for frontmatter
        if not content.startswith('---'):
            validation['issues'].append('Missing frontmatter')
            validation['is_valid'] = False
        
        # Check for proper code blocks
        code_block_count = content.count('```')
        if code_block_count % 2 != 0:
            validation['issues'].append('Unmatched code block delimiters')
            validation['is_valid'] = False
        
        # Check for headers
        headers = re.findall(r'^#+\s+.+$', content, re.MULTILINE)
        if len(headers) < 3:
            validation['warnings'].append('Few headers - content may lack structure')
        
        # Calculate metrics
        validation['metrics'] = {
            'word_count': len(content.split()),
            'code_blocks': code_block_count // 2,
            'headers': len(headers),
            'links': len(re.findall(r'\[([^\]]+)\]\([^)]+\)', content)),
            'characters': len(content)
        }
        
        return validation
    
    def convert_article_to_mdx(self, article_file: Path) -> Tuple[bool, str]:
        """Convert a single article to MDX format"""
        try:
            if self.config.is_debug_mode():
                print(f"🔄 Converting {article_file.name} to MDX")
            
            # Load article data
            with open(article_file, 'r', encoding='utf-8') as f:
                article_data = json.load(f)
            
            metadata = article_data.get('metadata', {})
            content = article_data.get('content', '')
            
            if not content:
                print(f"❌ No content found in {article_file.name}")
                return False, ""
            
            # Generate frontmatter
            frontmatter = self.generate_mdx_frontmatter(metadata)
            
            # Clean content
            cleaned_content = self.clean_markdown_content(content)
            
            # Combine frontmatter and content
            mdx_content = f"{frontmatter}\n\n{cleaned_content}"
            
            # Validate MDX
            validation = self.validate_mdx_content(mdx_content)
            
            if not validation['is_valid']:
                print(f"❌ MDX validation failed for {article_file.name}: {', '.join(validation['issues'])}")
                return False, ""
            
            if validation['warnings']:
                for warning in validation['warnings']:
                    print(f"⚠️  {article_file.name}: {warning}")
            
            # Generate filename
            mdx_filename = self.generate_mdx_filename(metadata)
            
            if self.config.is_debug_mode():
                metrics = validation['metrics']
                print(f"✅ MDX generated: {mdx_filename}")
                print(f"   📝 Words: {metrics['word_count']}")
                print(f"   💻 Code blocks: {metrics['code_blocks']}")
                print(f"   📑 Headers: {metrics['headers']}")
            
            return (True, mdx_content, mdx_filename)
            
        except Exception as e:
            print(f"❌ Error converting {article_file.name}: {e}")
            return False, ""
    
    def convert_specific_article(self, stackoverflow_id: str) -> Dict[str, Any]:
        """Convert specific article to MDX format"""
        generated_articles = self.resolver.get_generated_articles()
        
        # Find the specific article
        target_article = None
        for content_path, metadata_path in generated_articles:
            if f"_{stackoverflow_id}_" in content_path.name:
                target_article = (content_path, metadata_path)
                break
        
        if not target_article:
            return {"success": False, "error": f"No generated article found for StackOverflow ID {stackoverflow_id}"}
        
        print(f"🎯 Converting article for StackOverflow ID: {stackoverflow_id}")
        print(f"📄 Processing file: {target_article[0].name}")
        
        try:
            content_path, metadata_path = target_article
            success, message = self.convert_article_to_mdx(content_path)
            result = success
            
            if result:
                print(f"✅ Successfully converted article for ID {stackoverflow_id}")
                return {"success": True, "converted": 1, "failed": 0}
            else:
                print(f"❌ Failed to convert article for ID {stackoverflow_id}")
                return {"success": False, "converted": 0, "failed": 1}
                
        except Exception as e:
            print(f"❌ Error converting StackOverflow ID {stackoverflow_id}: {e}")
            return {"success": False, "error": str(e)}

    def convert_articles_to_mdx(self, limit: int = None) -> Dict[str, Any]:
        """Convert multiple articles to MDX format"""
        # Get generated articles
        articles = self.resolver.get_generated_articles(limit)
        
        if not articles:
            print("❌ No generated articles found")
            return {"success": False, "converted": 0}
        
        print(f"🔄 Converting {len(articles)} articles to MDX format...")
        
        converted = 0
        failed = 0
        mdx_files = []
        
        # Ensure output directory exists
        output_dir = self.config.get_generated_articles_path() / "mdx"
        if output_dir.exists() and output_dir.is_file():
            output_dir.unlink()  # Remove if it is a file
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for content_path, metadata_path in articles:
            try:
                result = self.convert_article_to_mdx(content_path)
                
                if len(result) == 3 and result[0]:  # Successful conversion
                    success, mdx_content, mdx_filename = result
                    
                    # Save MDX file
                    mdx_path = output_dir / mdx_filename
                    with open(mdx_path, 'w', encoding='utf-8') as f:
                        f.write(mdx_content)
                    
                    mdx_files.append(str(mdx_path))
                    converted += 1
                    
                    if not self.config.is_debug_mode():
                        print(f"✅ Converted: {mdx_filename}")
                else:
                    failed += 1
                    
            except Exception as e:
                print(f"❌ Error with {content_path.name}: {e}")
                failed += 1
        
        print(f"\n📊 MDX Conversion Complete:")
        print(f"✅ Converted: {converted}")
        print(f"❌ Failed: {failed}")
        print(f"📁 Output directory: {output_dir}")
        
        # Log the operation
        self.resolver.log_sync_operation("convert_to_mdx", {
            "articles_converted": converted,
            "articles_failed": failed,
            "mdx_files": mdx_files,
            "output_directory": str(output_dir)
        })
        
        return {
            "success": True,
            "converted": converted,
            "failed": failed,
            "output_directory": str(output_dir),
            "mdx_files": mdx_files
        }


def main():
    parser = argparse.ArgumentParser(description='Convert generated articles to MDX format')
    parser.add_argument('--config', '-c', type=str, 
                       help='Path to configuration file (default: config/workflow.yaml)')
    parser.add_argument('--limit', '-l', type=int, 
                       help='Maximum number of articles to convert (uses config default)')
    parser.add_argument('--stackoverflow-id', type=str,
                       help='Convert article for specific StackOverflow ID')
    parser.add_argument('--list-articles', action='store_true',
                       help='List available generated articles')
    parser.add_argument('--validate-only', action='store_true',
                       help='Only validate existing MDX files without conversion')
    
    args = parser.parse_args()
    
    try:
        converter = MDXConverter(args.config)
        
        if args.list_articles:
            articles = converter.resolver.get_generated_articles()
            print(f"📋 Available generated articles: {len(articles)}")
            for content_path, metadata_path in articles:
                print(f"  - {content_path.name}")
            return
        
        if args.validate_only:
            # Find existing MDX files and validate them
            mdx_dir = converter.config.get_generated_articles_path() / "mdx"
            if mdx_dir.exists():
                mdx_files = list(mdx_dir.glob("*.mdx"))
                print(f"🔍 Validating {len(mdx_files)} MDX files...")
                
                valid = 0
                invalid = 0
                
                for mdx_file in mdx_files:
                    with open(mdx_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    validation = converter.validate_mdx_content(content)
                    if validation['is_valid']:
                        valid += 1
                        print(f"✅ {mdx_file.name}")
                    else:
                        invalid += 1
                        print(f"❌ {mdx_file.name}: {', '.join(validation['issues'])}")
                
                print(f"\n📊 Validation complete: {valid} valid, {invalid} invalid")
            else:
                print("❌ No MDX directory found")
            return
        
        # Convert articles to MDX
        # Convert articles
        if args.stackoverflow_id:
            result = converter.convert_specific_article(args.stackoverflow_id)
        else:
            result = converter.convert_articles_to_mdx(limit=args.limit)
        
        if result["success"]:
            print(f"\n🚀 Ready for next step: python workflow/04_bridge_sync.py")
        else:
            print(f"\n❌ MDX conversion failed")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()