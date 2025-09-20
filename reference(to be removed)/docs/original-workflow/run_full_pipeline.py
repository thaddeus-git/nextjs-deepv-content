#!/usr/bin/env python3
"""
run_full_pipeline.py - Complete DeepV StackOverflow Workflow Pipeline
Runs all steps: ingest -> generate -> convert -> bridge sync
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Dict, Any

# Add modules directory for imports
sys.path.append(str(Path(__file__).parent.parent / "modules"))

from config_manager import ConfigManager
from path_resolver import PathResolver

# Import workflow steps
sys.path.append(str(Path(__file__).parent))

# Import individual workflow step classes
import importlib.util

def import_module_from_file(file_path, module_name):
    """Import a module from a file path"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import workflow modules
workflow_dir = Path(__file__).parent
ingest_module = import_module_from_file(workflow_dir / "01_ingest_source_data.py", "ingest")
generate_module = import_module_from_file(workflow_dir / "02_generate_article.py", "generate")
convert_module = import_module_from_file(workflow_dir / "03_convert_to_mdx.py", "convert")
sync_module = import_module_from_file(workflow_dir / "04_bridge_sync.py", "sync")

SourceDataIngestor = ingest_module.SourceDataIngestor
ArticleGenerator = generate_module.ArticleGenerator
MDXConverter = convert_module.MDXConverter
BridgeSync = sync_module.BridgeSync


class FullPipeline:
    """Orchestrates the complete StackOverflow workflow pipeline"""
    
    def __init__(self, config_path: str = None):
        self.config = ConfigManager(config_path)
        self.resolver = PathResolver(self.config)
        
        print("🚀 DeepV StackOverflow Workflow Pipeline")
        print("=" * 50)
        if self.config.is_debug_mode():
            self.config.print_config_summary()
            print("=" * 50)
    
    def run_step_01_ingest(self, limit: int, min_quality: int) -> Dict[str, Any]:
        """Step 1: Ingest source data"""
        print("\n📥 STEP 1: Ingesting Source Data")
        print("-" * 30)
        
        try:
            ingestor = SourceDataIngestor()
            processed_files = ingestor.ingest_batch(limit=limit, min_quality=min_quality)
            
            return {
                "success": True,
                "processed_files": processed_files,
                "count": len(processed_files)
            }
        except Exception as e:
            print(f"❌ Step 1 failed: {e}")
            return {"success": False, "error": str(e)}
    
    def run_step_02_generate(self, limit: int) -> Dict[str, Any]:
        """Step 2: Generate articles with AI"""
        print("\n🤖 STEP 2: Generating Articles with AI")
        print("-" * 40)
        
        try:
            generator = ArticleGenerator()
            result = generator.generate_articles(limit=limit)
            
            return result
        except Exception as e:
            print(f"❌ Step 2 failed: {e}")
            return {"success": False, "error": str(e)}
    
    def run_step_03_convert(self, limit: int) -> Dict[str, Any]:
        """Step 3: Convert to MDX format"""
        print("\n🔄 STEP 3: Converting to MDX Format")
        print("-" * 35)
        
        try:
            converter = MDXConverter()
            result = converter.convert_articles_to_mdx(limit=limit)
            
            return result
        except Exception as e:
            print(f"❌ Step 3 failed: {e}")
            return {"success": False, "error": str(e)}
    
    def run_step_04_bridge_sync(self, dry_run: bool, limit: int) -> Dict[str, Any]:
        """Step 4: Bridge sync to Next.js"""
        print(f"\n🌉 STEP 4: Bridge Sync to Next.js {'(DRY RUN)' if dry_run else ''}")
        print("-" * 45)
        
        try:
            bridge = BridgeSync()
            result = bridge.perform_bridge_sync(dry_run=dry_run, limit=limit)
            
            return result
        except Exception as e:
            print(f"❌ Step 4 failed: {e}")
            return {"success": False, "error": str(e)}
    
    def run_complete_pipeline(self, limit: int = 5, min_quality: int = 30, 
                            dry_run: bool = False, auto_sync: bool = False) -> Dict[str, Any]:
        """Run the complete pipeline with all steps"""
        start_time = time.time()
        
        print(f"🎯 Running complete pipeline with {limit} articles")
        print(f"📊 Quality threshold: {min_quality}")
        print(f"🧪 Dry run mode: {'ON' if dry_run else 'OFF'}")
        print(f"🔗 Auto sync: {'ON' if auto_sync else 'OFF'}")
        
        pipeline_results = {
            "start_time": start_time,
            "steps": {},
            "overall_success": True,
            "final_stats": {}
        }
        
        # Step 1: Ingest Source Data
        step1_result = self.run_step_01_ingest(limit, min_quality)
        pipeline_results["steps"]["ingest"] = step1_result
        
        if not step1_result["success"]:
            pipeline_results["overall_success"] = False
            print(f"\n❌ Pipeline stopped at Step 1: {step1_result.get('error', 'Unknown error')}")
            return pipeline_results
        
        if step1_result["count"] == 0:
            print(f"\n⚠️  No files processed in Step 1. Check source data or quality threshold.")
            pipeline_results["overall_success"] = False
            return pipeline_results
        
        # Step 2: Generate Articles
        step2_result = self.run_step_02_generate(limit)
        pipeline_results["steps"]["generate"] = step2_result
        
        if not step2_result["success"] or step2_result["processed"] == 0:
            pipeline_results["overall_success"] = False
            print(f"\n❌ Pipeline stopped at Step 2: {step2_result.get('error', 'No articles generated')}")
            return pipeline_results
        
        # Step 3: Convert to MDX
        step3_result = self.run_step_03_convert(limit)
        pipeline_results["steps"]["convert"] = step3_result
        
        if not step3_result["success"] or step3_result["converted"] == 0:
            pipeline_results["overall_success"] = False
            print(f"\n❌ Pipeline stopped at Step 3: {step3_result.get('error', 'No MDX files created')}")
            
            # Set final stats even for failed pipeline
            end_time = time.time()
            duration = end_time - start_time
            pipeline_results["end_time"] = end_time
            pipeline_results["duration"] = duration
            pipeline_results["final_stats"] = {
                "source_files_processed": step1_result["count"],
                "articles_generated": step2_result["processed"],
                "mdx_files_created": 0,
                "files_synced": 0,
                "total_duration_minutes": round(duration / 60, 2)
            }
            
            return pipeline_results
        
        # Step 4: Bridge Sync (optional based on auto_sync or user choice)
        should_sync = auto_sync
        if not auto_sync and not dry_run:
            response = input(f"\n🌉 Sync {step3_result['converted']} articles to Next.js project? (y/N): ")
            should_sync = response.lower().startswith('y')
        
        if should_sync or dry_run:
            step4_result = self.run_step_04_bridge_sync(dry_run, limit)
            pipeline_results["steps"]["bridge_sync"] = step4_result
            
            if not step4_result["success"]:
                print(f"\n⚠️  Step 4 failed but pipeline completed: {step4_result.get('message', 'Unknown error')}")
        else:
            print(f"\n⏭️  Skipping bridge sync. Run manually with: python workflow/04_bridge_sync.py")
            pipeline_results["steps"]["bridge_sync"] = {"success": True, "skipped": True}
        
        # Calculate final statistics
        end_time = time.time()
        duration = end_time - start_time
        
        pipeline_results["end_time"] = end_time
        pipeline_results["duration"] = duration
        pipeline_results["final_stats"] = {
            "source_files_processed": step1_result["count"],
            "articles_generated": step2_result["processed"],
            "mdx_files_created": step3_result["converted"],
            "files_synced": pipeline_results["steps"].get("bridge_sync", {}).get("synced", 0),
            "total_duration_minutes": round(duration / 60, 2)
        }
        
        return pipeline_results
    
    def print_pipeline_summary(self, results: Dict[str, Any]):
        """Print comprehensive pipeline summary"""
        print("\n" + "=" * 60)
        print("🎉 PIPELINE SUMMARY")
        print("=" * 60)
        
        stats = results["final_stats"]
        duration = results["duration"]
        
        print(f"⏱️  Total Duration: {duration:.1f} seconds ({stats['total_duration_minutes']} minutes)")
        print(f"📄 Source Files Processed: {stats['source_files_processed']}")
        print(f"🤖 Articles Generated: {stats['articles_generated']}")
        print(f"🔄 MDX Files Created: {stats['mdx_files_created']}")
        print(f"🌉 Files Synced: {stats['files_synced']}")
        
        # Success rate
        if stats['source_files_processed'] > 0:
            success_rate = (stats['mdx_files_created'] / stats['source_files_processed']) * 100
            print(f"✅ Success Rate: {success_rate:.1f}%")
        
        # Performance metrics
        if duration > 0:
            articles_per_minute = (stats['articles_generated'] / duration) * 60
            print(f"⚡ Performance: {articles_per_minute:.1f} articles/minute")
        
        # Step details
        print("\n📊 Step Results:")
        for step_name, step_result in results["steps"].items():
            if step_result.get("skipped"):
                print(f"   {step_name}: ⏭️  SKIPPED")
            elif step_result["success"]:
                print(f"   {step_name}: ✅ SUCCESS")
            else:
                print(f"   {step_name}: ❌ FAILED")
        
        # Next steps
        print("\n🚀 Next Steps:")
        if results["overall_success"]:
            if stats['files_synced'] > 0:
                print("   • Articles are synced to Next.js project")
                print("   • Build and deploy your Next.js application")
                print("   • Test the new articles in production")
            else:
                print("   • Run bridge sync: python workflow/04_bridge_sync.py")
                print("   • Or use --auto-sync flag for automatic syncing")
        else:
            print("   • Check error messages above")
            print("   • Verify configuration and source data")
            print("   • Run individual steps for debugging")
        
        # Log operation
        self.resolver.log_sync_operation("full_pipeline", {
            "results": results["final_stats"],
            "success": results["overall_success"],
            "duration": duration
        })


def main():
    parser = argparse.ArgumentParser(description='Run complete DeepV StackOverflow workflow pipeline')
    parser.add_argument('--config', '-c', type=str, 
                       help='Path to configuration file (default: config/workflow.yaml)')
    parser.add_argument('--limit', '-l', type=int, default=5,
                       help='Maximum number of articles to process (default: 5)')
    parser.add_argument('--min-quality', '-q', type=int, default=30,
                       help='Minimum quality score threshold (default: 30)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview sync operations without making changes')
    parser.add_argument('--auto-sync', action='store_true',
                       help='Automatically sync to Next.js without user confirmation')
    parser.add_argument('--quick-test', action='store_true',
                       help='Quick test with 1 article and high quality threshold')
    parser.add_argument('--production', action='store_true',
                       help='Production run with higher limits and auto-sync')
    
    args = parser.parse_args()
    
    try:
        # Adjust parameters for special modes
        if args.quick_test:
            args.limit = 1
            args.min_quality = 50
            print("🧪 Quick test mode: 1 article, quality ≥50")
        
        if args.production:
            args.limit = 20
            args.auto_sync = True
            print("🏭 Production mode: 20 articles, auto-sync enabled")
        
        # Initialize and run pipeline
        pipeline = FullPipeline(args.config)
        
        results = pipeline.run_complete_pipeline(
            limit=args.limit,
            min_quality=args.min_quality,
            dry_run=args.dry_run,
            auto_sync=args.auto_sync
        )
        
        # Print summary
        pipeline.print_pipeline_summary(results)
        
        # Exit code
        sys.exit(0 if results["overall_success"] else 1)
    
    except KeyboardInterrupt:
        print("\n⏹️  Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Pipeline error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()