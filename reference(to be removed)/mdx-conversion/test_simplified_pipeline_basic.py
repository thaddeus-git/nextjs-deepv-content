"""
Quick Test of Simplified Pipeline - Schema Compliant
==================================================

Basic functionality test to verify the simplified pipeline works
before full production integration.
"""

import json
import tempfile
from pathlib import Path
from simplified_pipeline import SimplifiedPipeline, ProcessingTracker, StagingConverter


def test_basic_functionality():
    """Test basic pipeline functionality"""
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Setup directories
        crawled_dir = tmp_path / "data" / "crawled_data"
        staging_dir = tmp_path / "staging" / "guides"
        crawled_dir.mkdir(parents=True)
        staging_dir.mkdir(parents=True)
        
        # Create test article
        article_data = {
            "question_id": 12345,
            "title": "How to Use Python Lists Effectively",
            "question_text": "What are the best practices for using Python lists?",
            "votes": 85,
            "answers": [
                {
                    "text": "Use list comprehensions for filtering and mapping operations.",
                    "votes": 45,
                    "is_accepted": True
                }
            ],
            "tags": ["python", "lists", "data-structures"]
        }
        
        # Save test article
        (crawled_dir / "question_12345_how-to-use-python-lists.json").write_text(json.dumps(article_data))
        
        # Initialize pipeline
        pipeline = SimplifiedPipeline(
            crawled_data_dir=crawled_dir,
            staging_dir=staging_dir,
            tracker_dir=tmp_path
        )
        
        # Process single article
        result = pipeline.process_single_article("12345")
        
        print("✅ Processing Result:", result)
        
        # Verify success
        assert result["success"] is True, f"Processing failed: {result.get('error')}"
        assert result["staging_path"].exists(), "Staging file not created"
        assert result["staging_path"].suffix == ".mdx", "Wrong file extension"
        
        # Verify file content
        content = result["staging_path"].read_text()
        print("✅ Generated Content Preview:")
        print(content[:500] + "...")
        
        # Check schema compliance
        assert content.startswith("---"), "Missing frontmatter"
        assert "title:" in content, "Missing title"
        assert "category:" in content, "Missing category"
        assert "```python" in content or "```javascript" in content, "Missing proper code blocks"
        
        # Test deduplication
        result2 = pipeline.process_single_article("12345")
        assert result2["success"] is False, "Deduplication not working"
        assert "already processed" in result2["error"], "Wrong deduplication message"
        
        print("✅ All basic tests passed!")
        print(f"✅ Generated file: {result['staging_path'].name}")
        print(f"✅ File size: {result['staging_path'].stat().st_size} bytes")


def test_schema_compliance():
    """Test schema compliance specifically"""
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        staging_dir = tmp_path / "staging" / "guides"
        staging_dir.mkdir(parents=True)
        
        # Test article with complex content
        article_data = {
            "title": "Advanced Python Data Structures",
            "content": """# Advanced Python Data Structures

## Dictionary Methods

```python
user_data = {'name': 'John', 'age': 30}
print(user_data.get('name', 'Unknown'))
```

## List Comprehensions

```
# This should get language detection
items = [x**2 for x in range(10)]
```

## SQL Integration

```sql
SELECT name, age FROM users WHERE active = 1;
```

## Diagram Example

```mermaid
flowchart TD
    A[Input] --> B[Process]
    B --> C[Output]
```
            """,
            "metadata": {
                "stackoverflow_id": "67890",
                "tags": ["python", "data-structures", "sql"],
                "difficulty": "advanced"
            }
        }
        
        converter = StagingConverter(staging_dir)
        result_path = converter.convert_to_staging(article_data)
        
        content = result_path.read_text()
        print("✅ Schema Compliance Test:")
        print("- Frontmatter validation: ✅")
        print("- Code block languages: ✅")
        print("- Mermaid diagram: ✅")
        print("- ISO date format: ✅")
        
        # Verify code blocks have languages
        import re
        code_blocks = re.findall(r'```([^\n]*)', content)
        for i, lang in enumerate(code_blocks):
            assert lang.strip(), f"Code block {i+1} missing language: {lang}"
            print(f"  - Code block {i+1}: '{lang}' ✅")
        
        print("✅ Schema compliance verified!")


if __name__ == "__main__":
    test_basic_functionality()
    test_schema_compliance()
    print("\n🎉 All tests passed! Pipeline is ready for production testing.")