#!/usr/bin/env python3
"""
01_ingest_source_data.py - Load and validate StackOverflow JSON source data
DeepV StackOverflow Workflow - Standalone Version
"""

import json
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add modules directory for imports
sys.path.append(str(Path(__file__).parent.parent / "modules"))

from config_manager import ConfigManager
from path_resolver import PathResolver


class SourceDataIngestor:
    """Handles ingestion and validation of StackOverflow source data"""
    
    def __init__(self, config_path: str = None):
        self.config = ConfigManager(config_path)
        self.resolver = PathResolver(self.config)
        
        print("🔧 StackOverflow Data Ingestor Initialized")
        if self.config.is_debug_mode():
            self.config.print_config_summary()
    
    def get_quality_answers(self, answers: List[Dict]) -> List[Dict]:
        """
        Enhanced answer selection - include all answers with votes > 0, minimum 3, maximum 8
        """
        if not answers:
            return []
            
        # Sort by votes descending
        sorted_answers = sorted(answers, key=lambda x: x.get('votes', 0), reverse=True)
        
        # Always include accepted answer if it exists
        accepted = [a for a in sorted_answers if a.get('is_accepted', False)]
        voted = [a for a in sorted_answers if a.get('votes', 0) > 0 and not a.get('is_accepted', False)]
        
        # Combine: accepted + voted answers
        quality_answers = accepted + voted
        
        # Ensure minimum 3 answers for better content generation
        if len(quality_answers) < 3:
            remaining = [a for a in sorted_answers if a not in quality_answers]
            quality_answers.extend(remaining[:3-len(quality_answers)])
        
        # Cap at maximum 8 to avoid overwhelming the AI
        return quality_answers[:8]
    
    def validate_source_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance source data quality"""
        validation_report = {
            'is_valid': True,
            'quality_score': 0,
            'issues': [],
            'enhancements': []
        }
        
        # Check required fields
        required_fields = ['title', 'question_text', 'answers', 'tags']
        for field in required_fields:
            if field not in data or not data[field]:
                validation_report['issues'].append(f"Missing or empty {field}")
                validation_report['is_valid'] = False
        
        if not validation_report['is_valid']:
            return validation_report
            
        # Quality scoring
        answers = data.get('answers', [])
        votes = data.get('votes', 0)
        
        # Base quality score
        quality_score = 0
        
        # Vote-based scoring
        if votes >= 50:
            quality_score += 30
        elif votes >= 10:
            quality_score += 20
        elif votes >= 5:
            quality_score += 10
        
        # Answer quality scoring
        quality_answers = self.get_quality_answers(answers)
        if len(quality_answers) >= 3:
            quality_score += 20
        if any(a.get('is_accepted', False) for a in answers):
            quality_score += 20
        if any(a.get('votes', 0) >= 10 for a in answers):
            quality_score += 15
        
        # Content length scoring
        question_length = len(data.get('question_text', ''))
        if question_length >= 200:
            quality_score += 10
        elif question_length >= 100:
            quality_score += 5
            
        # Code snippet bonus
        total_code_snippets = sum(len(a.get('code_snippets', [])) for a in answers)
        if total_code_snippets >= 3:
            quality_score += 15
        elif total_code_snippets >= 1:
            quality_score += 10
            
        validation_report['quality_score'] = quality_score
        
        # Add enhancements info
        validation_report['enhancements'] = [
            f"Selected {len(quality_answers)} quality answers",
            f"Question length: {question_length} characters",
            f"Total code snippets: {total_code_snippets}",
            f"Tags: {', '.join(data.get('tags', []))}"
        ]
        
        return validation_report
    
    def process_single_file(self, input_file: Path) -> Dict[str, Any]:
        """Process a single StackOverflow JSON file"""
        if self.config.is_debug_mode():
            print(f"📄 Processing: {input_file.name}")
        
        try:
            data = self.resolver.load_stackoverflow_data(input_file)
            
            if not data:
                return None
                
            # Validate data quality
            validation = self.validate_source_data(data)
            
            if not validation['is_valid']:
                print(f"❌ Invalid data in {input_file.name}: {', '.join(validation['issues'])}")
                return None
                
            if self.config.is_debug_mode():
                print(f"✅ Quality score: {validation['quality_score']}/100")
            
            # Enhance the data with quality answers
            enhanced_data = data.copy()
            enhanced_data['quality_answers'] = self.get_quality_answers(data.get('answers', []))
            enhanced_data['validation_report'] = validation
            enhanced_data['processed_at'] = Path(__file__).stem
            enhanced_data['workflow_version'] = "deepv_stackoverflow_v1.0"
            
            return enhanced_data
            
        except Exception as e:
            print(f"❌ Error processing {input_file.name}: {e}")
            return None
    
    def ingest_batch(self, limit: int = None, min_quality: int = None) -> List[str]:
        """
        Ingest a batch of source files and prepare them for article generation
        
        Args:
            limit: Maximum number of articles to process (from config if None)
            min_quality: Minimum quality score threshold (from config if None)
            
        Returns:
            List of output file paths ready for next step
        """
        # Use config defaults if not specified
        if limit is None:
            limit = self.config.get_processing_config().get('default_batch_size', 10)
        if min_quality is None:
            min_quality = self.config.get_quality_config().get('min_quality_score', 30)
        
        print(f"🔄 Ingesting batch of {limit} articles (min quality: {min_quality})")
        
        # Get available source files
        source_files = self.resolver.get_json_files_from_crawled_data()
        if not source_files:
            print(f"❌ No source files found in {self.config.get_crawled_data_path()}")
            return []
            
        print(f"📁 Found {len(source_files)} source files")
        
        processed_files = []
        successful_count = 0
        
        for source_file in source_files:
            if successful_count >= limit:
                break
                
            # Check if already processed
            output_filename = f"processed_{source_file.name}"
            output_file = self.config.get_workflow_queue_path() / output_filename
            
            if output_file.exists():
                if self.config.is_debug_mode():
                    print(f"⏭️  Skipping already processed: {source_file.name}")
                continue
            
            # Process the file
            enhanced_data = self.process_single_file(source_file)
            
            if enhanced_data and enhanced_data['validation_report']['quality_score'] >= min_quality:
                # Save processed data
                saved_path = self.resolver.save_workflow_queue_item(enhanced_data, output_filename)
                processed_files.append(str(saved_path))
                successful_count += 1
                
                if self.config.is_debug_mode():
                    print(f"✅ Saved: {output_filename}")
            else:
                quality_score = enhanced_data['validation_report']['quality_score'] if enhanced_data else 0
                if self.config.is_debug_mode():
                    print(f"❌ Skipped: Quality score {quality_score} below threshold {min_quality}")
        
        print(f"\n🎯 Batch complete: {successful_count} files processed")
        print(f"📂 Output directory: {self.config.get_workflow_queue_path()}")
        
        # Log the operation
        self.resolver.log_sync_operation("ingest_batch", {
            "files_processed": successful_count,
            "limit": limit,
            "min_quality": min_quality,
            "output_files": processed_files
        })
        
        return processed_files


def main():
    parser = argparse.ArgumentParser(description='Ingest StackOverflow source data for article generation')
    parser.add_argument('--config', '-c', type=str, 
                       help='Path to configuration file (default: config/workflow.yaml)')
    parser.add_argument('--limit', '-l', type=int, 
                       help='Maximum number of files to process (uses config default)')
    parser.add_argument('--min-quality', '-q', type=int,
                       help='Minimum quality score threshold (uses config default)')
    parser.add_argument('--list-queue', action='store_true',
                       help='List files in the processing queue')
    parser.add_argument('--list-sources', action='store_true',
                       help='List available source files')
    
    args = parser.parse_args()
    
    try:
        ingestor = SourceDataIngestor(args.config)
        
        if args.list_queue:
            queue_files = ingestor.resolver.get_workflow_queue_files()
            print(f"📋 Files in processing queue: {len(queue_files)}")
            for f in queue_files:
                print(f"  - {f.name}")
            return
        
        if args.list_sources:
            source_files = ingestor.resolver.get_json_files_from_crawled_data()
            print(f"📋 Available source files: {len(source_files)}")
            for f in source_files[:10]:  # Show first 10
                print(f"  - {f.name}")
            if len(source_files) > 10:
                print(f"  ... and {len(source_files) - 10} more")
            return
        
        # Process batch
        processed_files = ingestor.ingest_batch(
            limit=args.limit,
            min_quality=args.min_quality
        )
        
        if processed_files:
            print(f"\n🚀 Ready for next step: python workflow/02_generate_article.py")
            print(f"Queue directory: {ingestor.config.get_workflow_queue_path()}")
        else:
            print("\n❌ No files processed. Check source data quality or adjust parameters.")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()