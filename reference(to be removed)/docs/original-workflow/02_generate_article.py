#!/usr/bin/env python3
"""
02_generate_article.py - AI-powered article generation from StackOverflow data
DeepV StackOverflow Workflow - Standalone Version
"""

import json
import argparse
import hashlib
import re
import sys
import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Add modules directory for imports
sys.path.append(str(Path(__file__).parent.parent / "modules"))

from config_manager import ConfigManager
from path_resolver import PathResolver
from openrouter_client import OpenRouterClient
from dynamic_token_allocator import calculate_dynamic_tokens, analyze_token_allocation


class ArticleGenerator:
    """Handles AI-powered article generation from StackOverflow data"""
    
    def __init__(self, config_path: str = None):
        self.config = ConfigManager(config_path)
        self.resolver = PathResolver(self.config)
        self.ai_client = OpenRouterClient(self.config)
        
        # Track vote statistics for featured calculation
        self.vote_statistics = self._load_vote_statistics()
        
        print("🤖 Article Generator Initialized")
        if self.config.is_debug_mode():
            self.config.print_config_summary()
            print(f"🎯 AI Model: {self.ai_client.model}")
    
    def _load_vote_statistics(self) -> Dict[str, int]:
        """Load vote statistics from all available source files to calculate top 10%"""
        vote_stats = []
        source_files = self.resolver.get_json_files_from_crawled_data()
        
        for json_file in source_files:
            try:
                data = self.resolver.load_stackoverflow_data(json_file)
                votes = data.get('votes', 0)
                if isinstance(votes, int) and votes > 0:
                    vote_stats.append(votes)
            except Exception:
                continue
        
        if not vote_stats:
            return {"top_10_percent_threshold": 0}
            
        vote_stats.sort(reverse=True)
        top_10_percent_index = max(0, int(len(vote_stats) * 0.1))
        threshold = vote_stats[top_10_percent_index] if top_10_percent_index < len(vote_stats) else 0
        
        print(f"📊 Vote statistics: {len(vote_stats)} articles, top 10% threshold: {threshold} votes")
        return {"top_10_percent_threshold": threshold}
    
    def generate_unique_id(self, stackoverflow_id: str) -> str:
        """Generate deterministic unique ID based on StackOverflow ID (config-driven)"""
        # Get uniqueId settings from config
        unique_id_config = self.config.config.get('unique_id', {})
        method = unique_id_config.get('method', 'sha256')
        salt = unique_id_config.get('salt', 'deepv-content-2025')
        length = unique_id_config.get('length', 8)
        
        # Generate hash based on config
        hash_input = f"{salt}-{stackoverflow_id}"
        if method == 'sha256':
            hash_object = hashlib.sha256(hash_input.encode())
        else:  # fallback to md5 if needed
            hash_object = hashlib.md5(hash_input.encode())
            
        return hash_object.hexdigest()[:length]
    
    def generate_slug(self, title: str) -> str:
        """Generate URL-friendly slug from title"""
        # Clean and normalize title
        title = title.replace('[duplicate]', '').replace('[closed]', '').strip()
        title = title.lower()
        
        # Replace special characters and spaces
        title = re.sub(r'[^\w\s-]', '', title)  # Remove special chars except spaces and hyphens
        title = re.sub(r'\s+', '-', title)      # Replace spaces with hyphens
        title = re.sub(r'-+', '-', title)       # Replace multiple hyphens with single
        title = title.strip('-')                # Remove leading/trailing hyphens
        
        # Limit length for URL friendliness
        if len(title) > 60:
            title = title[:60].rsplit('-', 1)[0]  # Cut at word boundary
            
        return title
    
    def calculate_read_time(self, content: str) -> int:
        """Calculate read time based on content length (words per minute = 200)"""
        word_count = len(content.split())
        read_time_minutes = max(1, round(word_count / 200))  # 200 WPM average reading speed
        return read_time_minutes
    
    def is_featured_article(self, votes: int) -> bool:
        """Determine if article is featured based on top 10% StackOverflow votes"""
        threshold = self.vote_statistics.get("top_10_percent_threshold", 0)
        return votes >= threshold and threshold > 0
    
    def extract_technology(self, tags: List[str]) -> str:
        """Extract main technology from tags with comprehensive mapping"""
        if not tags:
            return "Programming"
        
        primary_tech = tags[0].upper()
        tech_mapping = {
            'CSS': 'CSS',
            'HTML': 'HTML', 
            'JAVASCRIPT': 'JavaScript',
            'PYTHON': 'Python',
            'JAVA': 'Java',
            'CPP': 'C++',
            'C': 'C',
            'CSHARP': 'C#',
            'GO': 'Go',
            'RUST': 'Rust',
            'PHP': 'PHP',
            'RUBY': 'Ruby',
            'SQL': 'SQL',
            'MYSQL': 'MySQL',
            'POSTGRESQL': 'PostgreSQL',
            'MONGODB': 'MongoDB',
            'REACT': 'React',
            'VUE': 'Vue.js',
            'ANGULAR': 'Angular',
            'NODE': 'Node.js',
            'EXPRESS': 'Express.js',
            'DJANGO': 'Django',
            'FLASK': 'Flask',
            'SPRING': 'Spring',
            'DOCKER': 'Docker',
            'KUBERNETES': 'Kubernetes',
            'AWS': 'AWS',
            'GIT': 'Git',
            'LINUX': 'Linux',
            'BASH': 'Bash',
            'POWERSHELL': 'PowerShell',
            'RPM': 'RPM/Linux',
            'ANDROID': 'Android',
            'IOS': 'iOS',
            'SWIFT': 'Swift',
            'KOTLIN': 'Kotlin',
            'TYPESCRIPT': 'TypeScript'
        }
        
        return tech_mapping.get(primary_tech, primary_tech.title())
    
    def optimize_title(self, title: str, answers: List[Dict]) -> str:
        """Create SEO-optimized title with method count"""
        method_count = min(len(answers), 6)
        
        # Clean up title
        title = title.replace('[duplicate]', '').replace('[closed]', '').strip()
        
        if any(phrase in title.lower() for phrase in ['how to', 'how can', 'how do', 'how should']):
            return f"{title}: {method_count} Methods + Performance Guide"
        else:
            return f"{title}: Complete Guide with {method_count} Solutions"
    
    def create_comprehensive_prompt(self, qa_data: Dict[str, Any]) -> str:
        """Create the comprehensive prompt for article generation"""
        title = qa_data.get('title', '')
        question_text = qa_data.get('question_text', '')
        quality_answers = qa_data.get('quality_answers', [])
        tags = qa_data.get('tags', [])
        technology = self.extract_technology(tags)
        optimized_title = self.optimize_title(title, quality_answers)
        
        # Build the enhanced 18-module prompt based on your tested structure
        prompt_parts = []
        method_count = min(len(quality_answers), 5)
        
        prompt_parts.append("act as you are top tech writer for content marketing with the target to satisfy users searching the queries. do me the contents in markdown. when it's necessary to put an image, do the detailed image as in a cloud-architecture diagram. do the decision tree as in the style of the uploaded image.")
        prompt_parts.append("")
        prompt_parts.append(f"user queries like:")
        prompt_parts.append(f"{title}")
        prompt_parts.append("")
        prompt_parts.append("user PERSONAS")
        prompt_parts.append("    |")
        prompt_parts.append("    |-- 🚀 Speed Seeker ─────────► Fastest method, minimal code")
        prompt_parts.append("    |-- 📚 Learning Explorer ────► Most educational, best practices")
        prompt_parts.append("    |-- 🔧 Problem Solver ───────► Just works, copy-paste solution")
        prompt_parts.append("    |-- 🏗️ Architecture Builder ──► Scalable, maintainable approach")
        prompt_parts.append("    |-- 🎨 Output Focused ───────► Formatting, presentation needs")
        prompt_parts.append("    |-- ⚡ Legacy Maintainer ────► Works with older versions/systems")
        prompt_parts.append("")
        prompt_parts.append("Here's the optimal module structure, ordered from top to bottom for maximum SEO and user experience. pick the best parts as you see fit. user PERSONAS can be used in the decision tree or for any purpose:")
        prompt_parts.append("")
        prompt_parts.append("## Complete Module Structure (Top to Bottom)")
        prompt_parts.append("")
        prompt_parts.append("### 1. **The Question/Title**")
        prompt_parts.append("```markdown")
        prompt_parts.append(f"# {optimized_title}")
        prompt_parts.append("```")
        prompt_parts.append("")
        prompt_parts.append("### 2. **Quick Answer** (must have)")
        prompt_parts.append("```markdown")
        prompt_parts.append("## Quick Answer")
        prompt_parts.append("[Provide the immediate, copy-paste solution based on the highest-voted answer]")
        prompt_parts.append("```")
        prompt_parts.append("")
        prompt_parts.append("### 3. **Decision Tree** (must have)")
        prompt_parts.append("```markdown")
        prompt_parts.append("## Choose Your Method")
        prompt_parts.append("[Interactive flowchart helping users pick the right method instantly - use mermaid syntax]")
        prompt_parts.append("```")
        prompt_parts.append("")
        prompt_parts.append("### 4. **Table of Contents**")
        prompt_parts.append("```markdown")
        prompt_parts.append("## Table of Contents")
        prompt_parts.append("- [Method 1: Best Method](#method-1)")
        prompt_parts.append("- [Performance Comparison](#performance)")
        prompt_parts.append("```")
        prompt_parts.append("")
        prompt_parts.append("### 5. **Quick Copy-Paste Solutions** (must have)")
        prompt_parts.append("```markdown")
        prompt_parts.append("## Ready-to-Use Code")
        prompt_parts.append("[Extract the best 2-3 solutions from answers as copy-paste code blocks with proper syntax highlighting]")
        prompt_parts.append("```")
        prompt_parts.append("")
        prompt_parts.append("### 6-10. **Method Sections** (for each major approach from answers)")
        prompt_parts.append("[Detailed explanation of each method from the StackOverflow answers]")
        prompt_parts.append("")
        prompt_parts.append("### 11. **Performance Comparison**")
        prompt_parts.append("[Create table comparing methods by speed, browser support, complexity]")
        prompt_parts.append("")
        prompt_parts.append("### 12. **Version Compatibility Matrix**")
        prompt_parts.append("```markdown")
        prompt_parts.append(f"## {technology} Version Support")
        prompt_parts.append("| Method | Version1 | Version2 | Version3+ |")
        prompt_parts.append("```")
        prompt_parts.append("")
        prompt_parts.append("### 13. **Common Problems & Solutions**")
        prompt_parts.append("[Address issues mentioned in comments/answers]")
        prompt_parts.append("")
        prompt_parts.append("### 14. **Real-World Examples** (must have)")
        prompt_parts.append("```markdown")
        prompt_parts.append("## Real-World Use Cases")
        prompt_parts.append("[Practical applications from the context]")
        prompt_parts.append("```")
        prompt_parts.append("")
        prompt_parts.append("### 15. **Related Technology Functions**")
        prompt_parts.append("```markdown")
        prompt_parts.append(f"## Related: Other {technology} Operations")
        prompt_parts.append("[List related functions/methods from the domain]")
        prompt_parts.append("```")
        prompt_parts.append("")
        prompt_parts.append("### 16. **Summary/Key Takeaways**")
        prompt_parts.append("```markdown")
        prompt_parts.append("## Summary")
        prompt_parts.append("1. Use X for modern versions")
        prompt_parts.append("2. Use Y for performance")
        prompt_parts.append("3. Avoid Z unless needed")
        prompt_parts.append("```")
        prompt_parts.append("")
        prompt_parts.append("### 17. **FAQ Section** (must have)")
        prompt_parts.append("```markdown")
        prompt_parts.append("## Frequently Asked Questions")
        prompt_parts.append("[Convert answer comments and follow-up questions into FAQ format]")
        prompt_parts.append("```")
        prompt_parts.append("")
        prompt_parts.append("### 18. **Tools & Resources**")
        prompt_parts.append("```markdown")
        prompt_parts.append("## Test Your Code")
        prompt_parts.append("- [Online tools for testing]")
        prompt_parts.append("- [Documentation links]")
        prompt_parts.append("- [Version checking commands]")
        prompt_parts.append("```")
        prompt_parts.append("")
        prompt_parts.append("## Why This Order Works")
        prompt_parts.append("")
        prompt_parts.append("**🎯 User Intent Matching:**")
        prompt_parts.append("- Question → Quick Answer → Decision Tree = Immediate satisfaction")
        prompt_parts.append("- Copy-paste code early = Practical users happy")
        prompt_parts.append("- Detailed methods = Learning-focused users satisfied")
        prompt_parts.append("")
        prompt_parts.append("**📈 SEO Benefits:**")
        prompt_parts.append("- FAQ section targets long-tail keywords")
        prompt_parts.append("- Multiple H2s for featured snippets")
        prompt_parts.append("- Internal linking opportunities with related functions")
        prompt_parts.append("")
        prompt_parts.append("**⚡ Performance:**")
        prompt_parts.append("- Critical info frontloaded")
        prompt_parts.append("- Progressive disclosure")
        prompt_parts.append("- Multiple exit points for different user types")
        prompt_parts.append("")
        prompt_parts.append("**🔄 Engagement:**")
        prompt_parts.append("- Decision tree keeps users engaged")
        prompt_parts.append("- Real-world examples show practical value")
        prompt_parts.append("- FAQ addresses search queries you might miss")
        prompt_parts.append("")
        prompt_parts.append("This structure serves both the \"quick answer\" searchers AND the \"deep learning\" developers while maximizing your chances of ranking for various related queries.")
        prompt_parts.append("")
        prompt_parts.append("=====below is the data for your reference making the content in json=======")
        prompt_parts.append("")
        prompt_parts.append(f"Original Question: {question_text}")
        prompt_parts.append("")
        prompt_parts.append(f"High-Quality Answers ({len(quality_answers)} available):")
        
        # Add quality answers with enhanced context
        for i, answer in enumerate(quality_answers, 1):
            votes = answer.get('votes', 0)
            is_accepted = "ACCEPTED ANSWER" if answer.get('is_accepted', False) else f"{votes} votes"
            answer_text = answer.get('text', '')[:1500]  # Increased for enhanced context
            code_snippets = answer.get('code_snippets', [])
            
            prompt_parts.append("")
            prompt_parts.append(f"=== ANSWER {i} ({is_accepted}) ===")
            prompt_parts.append(answer_text)
            prompt_parts.append("")
            prompt_parts.append("Code Examples:")
            if code_snippets:
                prompt_parts.extend(code_snippets[:8])  # More code examples
            else:
                prompt_parts.append("No code provided")
            prompt_parts.append("")
            prompt_parts.append("Comments:")
            comments = [comment.get('text', '')[:300] for comment in answer.get('comments', [])[:5]]  # More comments
            prompt_parts.extend(comments if comments else ["No comments"])
        
        prompt_parts.append("")
        prompt_parts.append("ENHANCED CONTENT REQUIREMENTS:")
        prompt_parts.append("- Generate 5,000-7,000 words for comprehensive coverage")
        prompt_parts.append("- Include MINIMUM 80 code blocks with proper syntax highlighting")
        prompt_parts.append("- Follow ALL 18 modules in exact order")
        prompt_parts.append("- Use user PERSONAS throughout content and decision trees")
        prompt_parts.append("- Create sophisticated mermaid decision trees")
        prompt_parts.append("- Generate detailed performance comparison tables")
        prompt_parts.append("- Include comprehensive FAQ section for SEO optimization")
        prompt_parts.append("- Focus on practical, copy-paste ready solutions")
        prompt_parts.append(f"- Use all {len(quality_answers)} provided answers")
        prompt_parts.append("- Update examples to current practices (2025)")
        prompt_parts.append("- Balance quick answers with deep technical understanding")
        prompt_parts.append("- Ensure each method section is tagged with relevant personas")
        prompt_parts.append("- Provide multiple working examples per method")
        prompt_parts.append("")
        prompt_parts.append("EXCLUSIONS:")
        prompt_parts.append("- NO StackOverflow vote/view statistics")
        prompt_parts.append("- NO references to original post metadata")
        prompt_parts.append("- NO duplicate/closed labels in content")
        prompt_parts.append("- Focus purely on technical solutions")
        
        return "\n".join(prompt_parts)
    
    def categorize_article(self, tags: List[str]) -> Dict[str, str]:
        """Auto-categorize article based on tags"""
        if not tags:
            return {"category": "programming", "subcategory": "general"}
        
        tag_mapping = {
            "javascript": {"category": "web-frontend", "subcategory": "javascript"},
            "css": {"category": "web-frontend", "subcategory": "css"},
            "html": {"category": "web-frontend", "subcategory": "html"},
            "react": {"category": "web-frontend", "subcategory": "javascript"},
            "vue": {"category": "web-frontend", "subcategory": "javascript"},
            "angular": {"category": "web-frontend", "subcategory": "javascript"},
            
            "python": {"category": "programming-languages", "subcategory": "python"},
            "java": {"category": "programming-languages", "subcategory": "java"},
            "cpp": {"category": "programming-languages", "subcategory": "cpp"},
            "c": {"category": "programming-languages", "subcategory": "c"},
            "csharp": {"category": "programming-languages", "subcategory": "csharp"},
            "go": {"category": "programming-languages", "subcategory": "go"},
            "rust": {"category": "programming-languages", "subcategory": "rust"},
            "php": {"category": "programming-languages", "subcategory": "php"},
            "ruby": {"category": "programming-languages", "subcategory": "ruby"},
            
            "sql": {"category": "databases", "subcategory": "sql"},
            "mysql": {"category": "databases", "subcategory": "mysql"},
            "postgresql": {"category": "databases", "subcategory": "postgresql"},
            "mongodb": {"category": "databases", "subcategory": "mongodb"},
            
            "android": {"category": "mobile", "subcategory": "android"},
            "ios": {"category": "mobile", "subcategory": "ios"},
            "swift": {"category": "mobile", "subcategory": "ios"},
            "kotlin": {"category": "mobile", "subcategory": "android"},
            
            "linux": {"category": "system-devops", "subcategory": "linux"},
            "bash": {"category": "system-devops", "subcategory": "shell"},
            "docker": {"category": "system-devops", "subcategory": "containerization"},
            "kubernetes": {"category": "system-devops", "subcategory": "containerization"},
            "git": {"category": "system-devops", "subcategory": "version-control"},
            "rpm": {"category": "system-devops", "subcategory": "package-management"},
            "aws": {"category": "system-devops", "subcategory": "cloud"},
        }
        
        for tag in tags:
            tag_lower = tag.lower()
            if tag_lower in tag_mapping:
                return tag_mapping[tag_lower]
        
        # Fallback
        return {"category": "programming", "subcategory": "general"}
    
    def assess_difficulty(self, qa_data: Dict[str, Any], content: str) -> str:
        """Assess article difficulty based on content and context"""
        question_text = qa_data.get('question_text', '').lower()
        
        # Beginner indicators
        beginner_keywords = ['how to', 'getting started', 'basic', 'simple', 'introduction', 'tutorial']
        if any(keyword in question_text for keyword in beginner_keywords):
            return "beginner"
        
        # Advanced indicators
        advanced_keywords = ['performance', 'optimization', 'scalability', 'architecture', 'best practices', 'production']
        if any(keyword in question_text for keyword in advanced_keywords):
            return "advanced"
        
        # Intermediate by default
        return "intermediate"
    
    def extract_description_from_content(self, content: str) -> str:
        """Extract SEO description from generated content"""
        # Look for Quick Answer section
        quick_answer_match = re.search(r'## Quick Answer\s*(.*?)(?=##|\n\n)', content, re.DOTALL)
        if quick_answer_match:
            description = quick_answer_match.group(1).strip()
            # Clean up markdown and limit to 160 chars
            description = re.sub(r'```.*?```', '', description, flags=re.DOTALL)
            description = re.sub(r'[*_`#]', '', description)
            description = description.replace('\n', ' ').strip()
            if len(description) > 160:
                description = description[:157] + "..."
            return description
        
        # Fallback to first paragraph
        paragraphs = content.split('\n\n')
        for para in paragraphs[1:]:  # Skip title
            if para.strip() and not para.startswith('#'):
                description = para.strip()[:157] + "..."
                return re.sub(r'[*_`#]', '', description)
        
        return "Comprehensive programming guide with multiple solutions, code examples, and user persona-driven approach."
    
    def generate_article_metadata(self, qa_data: Dict[str, Any], content: str) -> Dict[str, Any]:
        """Generate comprehensive metadata for the article"""
        stackoverflow_id = qa_data.get('question_id', str(qa_data.get('id', 'unknown')))
        title = qa_data.get('title', '').replace('[duplicate]', '').replace('[closed]', '').strip()
        tags = qa_data.get('tags', [])
        quality_answers = qa_data.get('quality_answers', [])
        votes = qa_data.get('votes', 0)
        
        # Generate enhanced metadata fields
        optimized_title = self.optimize_title(title, quality_answers)
        slug = self.generate_slug(title)
        unique_id = self.generate_unique_id(stackoverflow_id)
        read_time = self.calculate_read_time(content)
        featured = self.is_featured_article(votes)
        
        # Generate SEO description from content
        description = self.extract_description_from_content(content)
        
        # Auto-categorize based on tags
        category_info = self.categorize_article(tags)
        
        # Calculate difficulty based on answers and content
        difficulty = self.assess_difficulty(qa_data, content)
        
        # Comprehensive metadata structure
        metadata = {
            "title": optimized_title,
            "slug": slug,
            "uniqueId": unique_id,
            "category": category_info['category'],
            "subcategory": category_info['subcategory'],
            "description": description,  # SEO-friendly description (150-160 chars)
            "tags": tags,
            "difficulty": difficulty,
            "readTime": read_time,
            "publishedAt": datetime.now().strftime("%Y-%m-%d"),
            "featured": featured,
            
            # Technical metadata
            "technology": self.extract_technology(tags),
            "votes": votes,
            "answersCount": len(quality_answers),
            "sourceStackOverflowId": stackoverflow_id,
            "generatedAt": datetime.now().isoformat(),
            "workflowVersion": "deepv_stackoverflow_v1.0",
            
            # Quality metrics for search and categorization
            "qualityMetrics": {
                "wordCount": len(content.split()),
                "codeBlocks": content.count('```'),
                "sections": content.count('##'),
                "personaIntegration": sum([content.count(persona) for persona in ['Speed Seeker', 'Learning Explorer', 'Problem Solver', 'Architecture Builder', 'Output Focused', 'Legacy Maintainer']]),
                "practicalFocusScore": min(100, (content.count('```') * 2) + (content.count('##') * 1))
            }
        }
        
        return metadata
    
    def process_article(self, file_path: Path) -> bool:
        """Process a single article with AI generation"""
        try:
            print(f"🤖 Processing {file_path.name}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                qa_data = json.load(f)
            
            title = qa_data.get('title', 'Unknown')
            quality_answers = qa_data.get('quality_answers', [])
            votes = qa_data.get('votes', 0)
            
            if self.config.is_debug_mode():
                print(f"📊 Title: {title}")
                print(f"📊 Quality answers: {len(quality_answers)}")
                print(f"📊 Votes: {votes}")
            
            # Calculate dynamic token allocation (if enabled)
            use_dynamic_allocation = os.getenv('ENABLE_DYNAMIC_TOKENS', 'false').lower() == 'true'
            
            if use_dynamic_allocation:
                dynamic_tokens = calculate_dynamic_tokens(qa_data)
                allocation_analysis = analyze_token_allocation(qa_data)
                
                if self.config.is_debug_mode():
                    print(f"🎯 Dynamic token allocation: {dynamic_tokens} ({allocation_analysis['tier']} tier)")
                    print(f"📊 Allocation factors: {allocation_analysis['factors']}")
            else:
                dynamic_tokens = None
                allocation_analysis = None
                if self.config.is_debug_mode():
                    print(f"🎯 Using default token allocation (16K baseline)")
            
            # Create comprehensive prompt
            prompt = self.create_comprehensive_prompt(qa_data)
            
            # Validate prompt size
            if not self.ai_client.validate_prompt_size(prompt):
                print(f"⚠️  Warning: Prompt may be too large for {file_path.name}")
            
            # Generate article with AI using protocol-compliant file attachment
            print(f"📝 Generating article with {self.ai_client.model}...")
            if dynamic_tokens:
                print(f"🎯 Using {dynamic_tokens} tokens ({allocation_analysis['tier']} tier)")
                response = self.ai_client.generate_article_with_attachment(prompt, qa_data, max_tokens=dynamic_tokens)
            else:
                print(f"🎯 Using default token allocation")
                response = self.ai_client.generate_article_with_attachment(prompt, qa_data)
            
            if not response['success']:
                print(f"❌ Failed to generate article: {response.get('error', 'Unknown error')}")
                return False
            
            content = response['content']
            
            # Generate comprehensive metadata
            metadata = self.generate_article_metadata(qa_data, content)
            
            # Quality metrics
            word_count = len(content.split())
            code_blocks = content.count('```')
            
            print(f"✅ Generated article:")
            print(f"   📝 Words: ~{word_count}")
            print(f"   💻 Code blocks: {code_blocks}")
            print(f"   ⏱️ Read time: {metadata['readTime']} min")
            print(f"   ⭐ Featured: {metadata['featured']}")
            print(f"   🔗 Slug: {metadata['slug']}")
            
            # Save article with metadata
            # Prepare article data
            article_data = {
                "metadata": metadata,
                "content": content,
                "source_file": str(file_path),
                "generation_stats": response.get('metadata', {}),
                "workflow_version": "deepv_stackoverflow_v1.0"
            }
            
            # Add dynamic allocation info if enabled
            if dynamic_tokens and allocation_analysis:
                article_data["dynamic_allocation"] = {
                    "tokens_allocated": dynamic_tokens,
                    "tier": allocation_analysis['tier'],
                    "allocation_breakdown": allocation_analysis['breakdown'],
                    "content_factors": allocation_analysis['factors']
                }
            
            # Generate output filename
            output_filename = f"{file_path.stem}_article.json"
            saved_path = self.resolver.save_generated_article(
                json.dumps(article_data, indent=2, ensure_ascii=False),
                article_data,
                output_filename
            )
            
            print(f"✅ Saved: {saved_path.name}")
            return True
            
        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
            return False
    
    def generate_specific_article(self, stackoverflow_id: str) -> Dict[str, Any]:
        """Generate article for a specific StackOverflow ID"""
        queue_files = self.resolver.get_workflow_queue_files()
        
        # Find the specific file
        target_file = None
        for file_path in queue_files:
            if f"_question_{stackoverflow_id}_" in file_path.name:
                target_file = file_path
                break
        
        if not target_file:
            return {"success": False, "error": f"No file found for StackOverflow ID {stackoverflow_id}"}
        
        print(f"🎯 Generating article for StackOverflow ID: {stackoverflow_id}")
        print(f"📄 Processing file: {target_file.name}")
        
        try:
            # Process the specific file
            result = self.process_article(target_file)
            
            if result:
                print(f"✅ Successfully generated article for ID {stackoverflow_id}")
                return {"success": True, "processed": 1, "failed": 0}
            else:
                print(f"❌ Failed to generate article for ID {stackoverflow_id}")
                return {"success": False, "processed": 0, "failed": 1}
                
        except Exception as e:
            print(f"❌ Error processing StackOverflow ID {stackoverflow_id}: {e}")
            return {"success": False, "error": str(e)}

    def generate_articles(self, limit: int = None) -> Dict[str, Any]:
        """Generate multiple articles from the workflow queue"""
        # Use config default if not specified
        if limit is None:
            limit = self.config.get_processing_config().get('default_batch_size', 10)
        
        queue_files = self.resolver.get_workflow_queue_files(limit)
        
        if not queue_files:
            print("❌ No files found in workflow queue")
            return {"success": False, "processed": 0}
        
        print(f"🎯 Generating {len(queue_files)} articles...")
        
        processed = 0
        failed = 0
        
        for file_path in queue_files:
            if self.process_article(file_path):
                processed += 1
            else:
                failed += 1
        
        print(f"\n📊 Article Generation Complete:")
        print(f"✅ Processed: {processed}")
        print(f"❌ Failed: {failed}")
        print(f"📁 Output directory: {self.config.get_generated_articles_path()}")
        
        # Log the operation
        self.resolver.log_sync_operation("generate_articles", {
            "articles_generated": processed,
            "articles_failed": failed,
            "limit": limit,
            "model_used": self.ai_client.model
        })
        
        return {
            "success": True,
            "processed": processed,
            "failed": failed,
            "output_directory": str(self.config.get_generated_articles_path())
        }


def main():
    parser = argparse.ArgumentParser(description='Generate articles from StackOverflow data using AI')
    parser.add_argument('--config', '-c', type=str, 
                       help='Path to configuration file (default: config/workflow.yaml)')
    parser.add_argument('--limit', '-l', type=int, 
                       help='Maximum number of articles to generate (uses config default)')
    parser.add_argument('--stackoverflow-id', type=str,
                       help='Generate article for specific StackOverflow ID')
    parser.add_argument('--list-queue', action='store_true',
                       help='List files in the generation queue')
    parser.add_argument('--list-generated', action='store_true',
                       help='List generated articles')
    parser.add_argument('--test-connection', action='store_true',
                       help='Test AI API connection')
    
    args = parser.parse_args()
    
    try:
        generator = ArticleGenerator(args.config)
        
        if args.test_connection:
            success = generator.ai_client.test_connection()
            if success:
                print("✅ AI API connection successful")
            else:
                print("❌ AI API connection failed")
            return
        
        if args.list_queue:
            queue_files = generator.resolver.get_workflow_queue_files()
            print(f"📋 Files in generation queue: {len(queue_files)}")
            for f in queue_files:
                print(f"  - {f.name}")
            return
        
        if args.list_generated:
            articles = generator.resolver.get_generated_articles()
            print(f"📋 Generated articles: {len(articles)}")
            for content_path, metadata_path in articles:
                print(f"  - {content_path.name}")
            return
        
        # Generate articles
        if args.stackoverflow_id:
            result = generator.generate_specific_article(args.stackoverflow_id)
        else:
            result = generator.generate_articles(limit=args.limit)
        
        if result["success"]:
            print(f"\n🚀 Ready for next step: python workflow/03_convert_to_mdx.py")
        else:
            print(f"\n❌ Article generation failed")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()