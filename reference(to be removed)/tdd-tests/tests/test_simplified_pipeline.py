"""
TDD Tests for Simplified Pipeline Implementation
==================================================

Test-Driven Development approach for robust pipeline:
1. Text file tracking (deduplication)
2. Direct staging conversion
3. Crawled data processing
4. End-to-end integration

Following pytest best practices with tmp_path for isolation.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch


class TestTextFileTracking:
    """🔴 RED: Test text file tracking system for deduplication"""
    
    def test_mark_article_as_processed(self, tmp_path):
        """Test marking an article as processed in text file"""
        # This test should FAIL initially (Red phase)
        from simplified_pipeline import ProcessingTracker
        
        tracker = ProcessingTracker(tmp_path)
        stackoverflow_id = "12345"
        
        # Mark as processed
        tracker.mark_as_processed(stackoverflow_id)
        
        # Verify it's tracked
        processed_file = tmp_path / "processed_ids.txt"
        assert processed_file.exists()
        assert stackoverflow_id in processed_file.read_text()
    
    def test_check_if_article_already_processed(self, tmp_path):
        """Test checking if article was already processed"""
        from simplified_pipeline import ProcessingTracker
        
        tracker = ProcessingTracker(tmp_path)
        stackoverflow_id = "12345"
        
        # Initially not processed
        assert not tracker.is_processed(stackoverflow_id)
        
        # After marking as processed
        tracker.mark_as_processed(stackoverflow_id)
        assert tracker.is_processed(stackoverflow_id)
    
    def test_deduplication_prevents_reprocessing(self, tmp_path):
        """Test that deduplication prevents reprocessing same article"""
        from simplified_pipeline import ProcessingTracker
        
        tracker = ProcessingTracker(tmp_path)
        stackoverflow_id = "12345"
        
        # Process first time
        tracker.mark_as_processed(stackoverflow_id)
        
        # Should be marked as processed
        assert tracker.is_processed(stackoverflow_id)
        
        # Should not allow reprocessing
        assert not tracker.should_process(stackoverflow_id)


class TestDirectStagingConversion:
    """🔴 RED: Test direct conversion to staging (bypass local MDX)"""
    
    def test_convert_writes_to_staging_not_local(self, tmp_path):
        """Test that conversion writes directly to staging directory"""
        from simplified_pipeline import StagingConverter
        
        # Setup test directories
        staging_dir = tmp_path / "staging" / "guides"
        staging_dir.mkdir(parents=True)
        
        # Mock article data
        article_data = {
            "title": "Test Article",
            "content": "# Test Content\n\n```python\nprint('hello')\n```",
            "metadata": {"stackoverflow_id": "12345"}
        }
        
        converter = StagingConverter(staging_dir)
        result_path = converter.convert_to_staging(article_data)
        
        # Should write directly to staging
        assert result_path.parent == staging_dir
        assert result_path.exists()
        assert "test-article-" in result_path.name
        assert result_path.suffix == ".mdx"
    
    def test_staging_file_format_correct(self, tmp_path):
        """Test that staging file has correct MDX format"""
        from simplified_pipeline import StagingConverter
        
        staging_dir = tmp_path / "staging" / "guides"
        staging_dir.mkdir(parents=True)
        
        article_data = {
            "title": "Python Enum Guide",
            "content": "# How to use Python enums\n\n```python\nfrom enum import Enum\n```",
            "metadata": {
                "stackoverflow_id": "12345",
                "tags": ["python", "enum"],
                "difficulty": "beginner"
            }
        }
        
        converter = StagingConverter(staging_dir)
        result_path = converter.convert_to_staging(article_data)
        
        content = result_path.read_text()
        
        # Should have frontmatter
        assert content.startswith("---")
        assert "title:" in content
        assert "category:" in content
        assert "---" in content.split("\n")[5:15]  # Frontmatter should end
        
        # Should have content
        assert "# How to use Python enums" in content
        assert "```python" in content
    
    def test_next_js_code_syntax_highlighting(self, tmp_path):
        """Test that code blocks have proper syntax highlighting for Next.js"""
        from simplified_pipeline import StagingConverter
        
        staging_dir = tmp_path / "staging" / "guides"
        staging_dir.mkdir(parents=True)
        
        article_data = {
            "title": "Code Examples",
            "content": """
# Code Examples

```
print('no language specified')
```

```js
const x = 1;
```

```python
def hello():
    pass
```
            """,
            "metadata": {"stackoverflow_id": "12345"}
        }
        
        converter = StagingConverter(staging_dir)
        result_path = converter.convert_to_staging(article_data)
        
        content = result_path.read_text()
        
        # Should have proper language mappings
        assert "```javascript" in content  # js -> javascript
        assert "```python" in content     # python stays python
        # First block should get smart detection or default to text
        assert "```text" in content or "```javascript" in content


class TestCrawledDataProcessing:
    """🔴 RED: Test direct processing from crawled_data"""
    
    def test_scan_crawled_data_directory(self, tmp_path):
        """Test scanning crawled_data for available articles"""
        from simplified_pipeline import CrawledDataScanner
        
        # Setup mock crawled_data
        crawled_dir = tmp_path / "data" / "crawled_data"
        crawled_dir.mkdir(parents=True)
        
        # Create test files
        (crawled_dir / "question_12345_test-article.json").write_text('{"test": "data"}')
        (crawled_dir / "question_67890_another-article.json").write_text('{"test": "data2"}')
        (crawled_dir / "not_a_question.txt").write_text("ignore this")
        
        scanner = CrawledDataScanner(crawled_dir)
        articles = scanner.get_available_articles()
        
        assert len(articles) == 2
        assert all(f.name.startswith("question_") for f in articles)
        assert all(f.suffix == ".json" for f in articles)
    
    def test_skip_already_processed_articles(self, tmp_path):
        """Test that scanner skips already processed articles"""
        from simplified_pipeline import CrawledDataScanner, ProcessingTracker
        
        # Setup
        crawled_dir = tmp_path / "data" / "crawled_data"
        crawled_dir.mkdir(parents=True)
        
        (crawled_dir / "question_12345_test-article.json").write_text('{"test": "data"}')
        (crawled_dir / "question_67890_another-article.json").write_text('{"test": "data2"}')
        
        tracker = ProcessingTracker(tmp_path)
        scanner = CrawledDataScanner(crawled_dir, tracker)
        
        # Mark one as processed
        tracker.mark_as_processed("12345")
        
        # Should only return unprocessed
        articles = scanner.get_unprocessed_articles()
        assert len(articles) == 1
        assert "67890" in articles[0].name
    
    def test_extract_stackoverflow_id_from_filename(self, tmp_path):
        """Test extracting StackOverflow ID from various filename formats"""
        from simplified_pipeline import CrawledDataScanner
        
        scanner = CrawledDataScanner(tmp_path)
        
        # Test different formats
        assert scanner.extract_id("question_12345_title.json") == "12345"
        assert scanner.extract_id("processed_question_67890_title.json") == "67890"
        assert scanner.extract_id("invalid_format.json") is None


class TestEndToEndIntegration:
    """🔴 RED: Test complete workflow integration"""
    
    def test_single_article_end_to_end(self, tmp_path):
        """Test processing a single article from crawled_data to staging"""
        from simplified_pipeline import SimplifiedPipeline
        
        # Setup complete environment
        crawled_dir = tmp_path / "data" / "crawled_data"
        staging_dir = tmp_path / "staging" / "guides"
        crawled_dir.mkdir(parents=True)
        staging_dir.mkdir(parents=True)
        
        # Create test article
        article_data = {
            "question_id": 12345,
            "title": "Test Question",
            "question_text": "How to test?",
            "votes": 50,
            "answers": [{"text": "Use pytest!", "votes": 30}],
            "tags": ["python", "testing"]
        }
        (crawled_dir / "question_12345_test-question.json").write_text(json.dumps(article_data))
        
        # Initialize pipeline
        pipeline = SimplifiedPipeline(
            crawled_data_dir=crawled_dir,
            staging_dir=staging_dir,
            tracker_dir=tmp_path
        )
        
        # Process one article
        result = pipeline.process_single_article("12345")
        
        # Verify success
        assert result["success"] is True
        assert result["staging_path"].exists()
        assert result["staging_path"].suffix == ".mdx"
        
        # Verify tracking
        assert pipeline.tracker.is_processed("12345")
    
    def test_batch_processing_with_deduplication(self, tmp_path):
        """Test processing multiple articles with deduplication"""
        from simplified_pipeline import SimplifiedPipeline
        
        # Setup
        crawled_dir = tmp_path / "data" / "crawled_data"
        staging_dir = tmp_path / "staging" / "guides"
        crawled_dir.mkdir(parents=True)
        staging_dir.mkdir(parents=True)
        
        # Create multiple test articles
        for i, title in enumerate(["Article A", "Article B", "Article C"], 1):
            article_data = {
                "question_id": f"1234{i}",
                "title": title,
                "question_text": f"Test question {i}",
                "votes": 50,
                "answers": [{"text": f"Answer {i}", "votes": 30}],
                "tags": ["python"]
            }
            (crawled_dir / f"question_1234{i}_{title.lower().replace(' ', '-')}.json").write_text(json.dumps(article_data))
        
        pipeline = SimplifiedPipeline(
            crawled_data_dir=crawled_dir,
            staging_dir=staging_dir,
            tracker_dir=tmp_path
        )
        
        # Process batch
        results = pipeline.process_batch(count=3)
        
        # All should succeed
        assert results["processed"] == 3
        assert results["failed"] == 0
        assert len(list(staging_dir.glob("*.mdx"))) == 3
        
        # Run again - should skip all (deduplication)
        results2 = pipeline.process_batch(count=3)
        assert results2["processed"] == 0  # All skipped
        assert results2["skipped"] == 3
    
    @patch('simplified_pipeline.OpenRouterClient')
    def test_error_handling_and_recovery(self, mock_client, tmp_path):
        """Test that pipeline handles errors gracefully"""
        from simplified_pipeline import SimplifiedPipeline
        
        # Setup
        crawled_dir = tmp_path / "data" / "crawled_data"
        staging_dir = tmp_path / "staging" / "guides"
        failed_dir = tmp_path / "data" / "failed"
        crawled_dir.mkdir(parents=True)
        staging_dir.mkdir(parents=True)
        
        # Create test article
        article_data = {"question_id": 12345, "title": "Test"}
        (crawled_dir / "question_12345_test.json").write_text(json.dumps(article_data))
        
        # Mock AI generation to fail
        mock_client_instance = Mock()
        mock_client_instance.generate_article.side_effect = Exception("API Error")
        mock_client.return_value = mock_client_instance
        
        pipeline = SimplifiedPipeline(
            crawled_data_dir=crawled_dir,
            staging_dir=staging_dir,
            tracker_dir=tmp_path,
            failed_dir=failed_dir
        )
        
        # Process should handle error
        result = pipeline.process_single_article("12345")
        
        # Should fail gracefully
        assert result["success"] is False
        assert "API Error" in result["error"]
        
        # Should move to failed directory
        failed_files = list((failed_dir).glob("*12345*"))
        assert len(failed_files) >= 1  # Article + error log