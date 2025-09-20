#!/usr/bin/env python3
"""
04_bridge_sync.py - Sync generated MDX files to Next.js project
DeepV StackOverflow Workflow - Standalone Version
"""

import json
import argparse
import shutil
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timezone

# Add modules directory for imports
sys.path.append(str(Path(__file__).parent.parent / "modules"))

from config_manager import ConfigManager
from path_resolver import PathResolver


class BridgeSync:
    """Handles syncing MDX files to Next.js project with backup and rollback capabilities"""
    
    def __init__(self, config_path: str = None):
        self.config = ConfigManager(config_path)
        self.resolver = PathResolver(self.config)
        
        print("🌉 Bridge Sync Initialized")
        if self.config.is_debug_mode():
            self.config.print_config_summary()
            
        # Validate Next.js project path
        self.nextjs_path = self.config.get_nextjs_project_path()
        self.content_path = self.resolver.get_nextjs_content_path()
        
        if not self.nextjs_path.exists():
            print(f"⚠️  Warning: Next.js project not found at {self.nextjs_path}")
    
    def get_mdx_files(self) -> List[Path]:
        """Get all MDX files ready for sync"""
        mdx_dir = self.config.get_generated_articles_path() / "mdx"
        
        if not mdx_dir.exists():
            return []
        
        return list(mdx_dir.glob("*.mdx"))
    
    def create_article_index_entry(self, mdx_file: Path) -> Dict[str, Any]:
        """Create article index entry from MDX file"""
        try:
            with open(mdx_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter_text = parts[1]
                    
                    # Parse frontmatter fields (handle YAML arrays)
                    metadata = {}
                    lines = frontmatter_text.split('\n')
                    i = 0
                    while i < len(lines):
                        line = lines[i].strip()
                        if ':' in line and not line.startswith('#'):
                            key, value = line.split(':', 1)
                            key = key.strip()
                            value = value.strip().strip('"\'')
                            
                            # Handle tags array
                            if key == 'tags' and not value:
                                tags = []
                                i += 1
                                while i < len(lines) and lines[i].strip().startswith('- '):
                                    tag = lines[i].strip()[2:].strip('"\'')
                                    tags.append(tag)
                                    i += 1
                                metadata[key] = tags
                                continue
                            
                            # Handle boolean values
                            if value.lower() in ['true', 'false']:
                                value = value.lower() == 'true'
                            # Handle numeric values
                            elif value.isdigit():
                                value = int(value)
                            
                            metadata[key] = value
                        i += 1
                    
                    # Extract uniqueId from filename (after last dash)
                    filename_parts = mdx_file.stem.split('-')
                    unique_id = filename_parts[-1] if filename_parts else mdx_file.stem
                    
                    # Create index entry
                    return {
                        "id": unique_id,
                        "title": metadata.get('title', 'Unknown'),
                        "slug": metadata.get('slug', mdx_file.stem),
                        "category": metadata.get('category', 'programming'),
                        "subcategory": metadata.get('subcategory', 'general'),
                        "difficulty": metadata.get('difficulty', 'intermediate'),
                        "technology": metadata.get('technology', 'Programming'),
                        "readTime": metadata.get('readTime', 5),
                        "publishedAt": metadata.get('publishedAt', datetime.now().strftime("%Y-%m-%d")),
                        "featured": metadata.get('featured', False),
                        "description": metadata.get('description', ''),
                        "tags": metadata.get('tags', []),
                        "filename": mdx_file.name,
                        "lastUpdated": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
                    }
            
            # Fallback if frontmatter parsing fails
            return {
                "id": mdx_file.stem,
                "title": mdx_file.stem.replace('-', ' ').title(),
                "slug": mdx_file.stem,
                "category": "programming",
                "subcategory": "general",
                "difficulty": "intermediate",
                "technology": "Programming",
                "readTime": 5,
                "publishedAt": datetime.now().strftime("%Y-%m-%d"),
                "featured": False,
                "excerpt": "Programming guide generated from StackOverflow data",
                "tags": [],
                "filename": mdx_file.name,
                "lastUpdated": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
            }
            
        except Exception as e:
            print(f"⚠️  Error parsing {mdx_file.name}: {e}")
            return None
    
    def update_article_index(self, mdx_files: List[Path]) -> bool:
        """Update or create article index for Next.js project"""
        try:
            # Ensure staging config directory exists in Next.js project
            config_dir = self.nextjs_path / "content" / "staging" / "config"
            config_dir.mkdir(parents=True, exist_ok=True)
            
            index_file = config_dir / "article-index-update.json"
            
            # Load existing index if it exists (with validation)
            existing_index = {}
            if index_file.exists():
                try:
                    with open(index_file, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                    # Only keep properly formatted entries (validate ID format and required fields)
                    for article in existing_data.get('articles', []):
                        article_id = article.get('id', '')
                        # Valid ID should be 8-character hash (not filename)
                        if (len(article_id) == 8 and 
                            'description' in article and 
                            isinstance(article.get('tags', []), list)):
                            existing_index[article_id] = article
                        else:
                            print(f"⚠️  Skipping invalid index entry: {article_id}")
                except Exception as e:
                    print(f"⚠️  Could not load existing index: {e}")
            
            # Create new index entries
            new_entries = []
            updated_count = 0
            
            for mdx_file in mdx_files:
                entry = self.create_article_index_entry(mdx_file)
                if entry:
                    article_id = entry['id']
                    if article_id in existing_index:
                        updated_count += 1
                    new_entries.append(entry)
            
            # Merge with existing entries (only keep entries with existing files)
            all_entries = []
            processed_ids = {entry['id'] for entry in new_entries}
            
            # Add new entries
            all_entries.extend(new_entries)
            
            # Add existing entries that weren't updated AND still have existing files
            for article_id, entry in existing_index.items():
                if article_id not in processed_ids:
                    # Check if the MDX file actually exists
                    filename = entry.get('filename', '')
                    file_path = self.content_path / filename
                    if file_path.exists():
                        all_entries.append(entry)
                    else:
                        print(f"⚠️  Removing phantom entry: {article_id} (file {filename} not found)")
            
            # Sort by publishedAt (newest first)
            all_entries.sort(key=lambda x: x.get('publishedAt', ''), reverse=True)
            
            # Create updated index
            index_data = {
                "lastUpdated": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                "totalArticles": len(all_entries),
                "categories": list(set(article.get('category', 'programming') for article in all_entries)),
                "technologies": list(set(article.get('technology', 'Programming') for article in all_entries)),
                "articles": all_entries
            }
            
            # Save updated index
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Updated article index: {len(new_entries)} new, {updated_count} updated")
            print(f"📊 Total articles in index: {len(all_entries)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to update article index: {e}")
            return False
    
    def sync_mdx_files(self, mdx_files: List[Path], dry_run: bool = False) -> Dict[str, Any]:
        """Sync MDX files to Next.js project"""
        if not self.content_path.exists():
            if dry_run:
                print(f"🧪 DRY RUN: Would create content directory: {self.content_path}")
            else:
                print(f"📁 Creating content directory: {self.content_path}")
                self.content_path.mkdir(parents=True, exist_ok=True)
        
        synced = 0
        failed = 0
        sync_details = []
        
        for mdx_file in mdx_files:
            try:
                target_path = self.content_path / mdx_file.name
                
                if dry_run:
                    action = "CREATE" if not target_path.exists() else "UPDATE"
                    print(f"🧪 DRY RUN: Would {action} {target_path.name}")
                    sync_details.append({
                        "file": mdx_file.name,
                        "action": action,
                        "target": str(target_path),
                        "status": "dry_run"
                    })
                    synced += 1
                else:
                    # Copy file
                    shutil.copy2(mdx_file, target_path)
                    action = "SYNCED"
                    print(f"✅ {action}: {target_path.name}")
                    
                    sync_details.append({
                        "file": mdx_file.name,
                        "action": action,
                        "target": str(target_path),
                        "status": "success",
                        "size": target_path.stat().st_size
                    })
                    synced += 1
                    
            except Exception as e:
                print(f"❌ Failed to sync {mdx_file.name}: {e}")
                sync_details.append({
                    "file": mdx_file.name,
                    "action": "FAILED",
                    "error": str(e),
                    "status": "failed"
                })
                failed += 1
        
        return {
            "synced": synced,
            "failed": failed,
            "details": sync_details
        }
    
    def perform_bridge_sync(self, dry_run: bool = False, limit: int = None) -> Dict[str, Any]:
        """Perform complete bridge sync operation"""
        bridge_config = self.config.get_bridge_config()
        
        # Get MDX files
        mdx_files = self.get_mdx_files()
        if limit:
            mdx_files = mdx_files[:limit]
        
        if not mdx_files:
            print("❌ No MDX files found for sync")
            return {"success": False, "message": "No MDX files available"}
        
        print(f"🌉 {'DRY RUN: ' if dry_run else ''}Bridge sync starting...")
        print(f"📁 Source: {self.config.get_generated_articles_path() / 'mdx'}")
        print(f"🎯 Target: {self.content_path}")
        print(f"📄 Files: {len(mdx_files)}")
        
        # Create backup if enabled and not dry run
        backup_path = None
        if bridge_config.get('backup_before_sync', True) and not dry_run:
            backup_path = self.resolver.backup_nextjs_content()
            if not backup_path:
                print("⚠️  Backup failed, continuing without backup...")
        
        # Sync files
        sync_result = self.sync_mdx_files(mdx_files, dry_run)
        
        # Update article index
        index_updated = False
        if not dry_run and sync_result['synced'] > 0:
            index_updated = self.update_article_index(mdx_files)
        elif dry_run:
            print("🧪 DRY RUN: Would update article index")
            index_updated = True
        
        # Log operation
        operation_details = {
            "files_synced": sync_result['synced'],
            "files_failed": sync_result['failed'],
            "dry_run": dry_run,
            "backup_created": str(backup_path) if backup_path else None,
            "index_updated": index_updated,
            "target_directory": str(self.content_path),
            "sync_details": sync_result['details']
        }
        
        if not dry_run:
            self.resolver.log_sync_operation("bridge_sync", operation_details)
        
        # Summary
        print(f"\n📊 Bridge Sync {'Simulation' if dry_run else 'Complete'}:")
        print(f"✅ Synced: {sync_result['synced']}")
        print(f"❌ Failed: {sync_result['failed']}")
        print(f"📋 Index updated: {'Yes' if index_updated else 'No'}")
        if backup_path and not dry_run:
            print(f"💾 Backup: {backup_path.name}")
        
        return {
            "success": True,
            "synced": sync_result['synced'],
            "failed": sync_result['failed'],
            "backup_path": str(backup_path) if backup_path else None,
            "index_updated": index_updated,
            "details": operation_details
        }
    
    def rollback_sync(self, backup_name: str = None) -> bool:
        """Rollback sync operation using backup"""
        backup_dir = self.config.get_backup_path()
        
        if backup_name:
            backup_path = backup_dir / backup_name
        else:
            # Find most recent backup
            backups = [d for d in backup_dir.iterdir() if d.is_dir() and d.name.startswith('nextjs_content_backup_')]
            if not backups:
                print("❌ No backups found for rollback")
                return False
            
            backup_path = max(backups, key=lambda x: x.stat().st_ctime)
        
        if not backup_path.exists():
            print(f"❌ Backup not found: {backup_path}")
            return False
        
        try:
            print(f"🔄 Rolling back to backup: {backup_path.name}")
            
            # Remove current content
            if self.content_path.exists():
                shutil.rmtree(self.content_path)
            
            # Restore from backup
            shutil.copytree(backup_path, self.content_path)
            
            print(f"✅ Rollback complete")
            
            # Log rollback
            self.resolver.log_sync_operation("rollback_sync", {
                "backup_used": str(backup_path),
                "restored_to": str(self.content_path)
            })
            
            return True
            
        except Exception as e:
            print(f"❌ Rollback failed: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description='Bridge sync MDX files to Next.js project')
    parser.add_argument('--config', '-c', type=str, 
                       help='Path to configuration file (default: config/workflow.yaml)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview sync operations without making changes')
    parser.add_argument('--limit', '-l', type=int,
                       help='Maximum number of files to sync')
    parser.add_argument('--list-mdx', action='store_true',
                       help='List available MDX files')
    parser.add_argument('--rollback', type=str, nargs='?', const='latest',
                       help='Rollback to backup (specify backup name or use latest)')
    parser.add_argument('--list-backups', action='store_true',
                       help='List available backups')
    parser.add_argument('--sync-all', action='store_true',
                       help='Sync all available MDX files')
    
    args = parser.parse_args()
    
    try:
        bridge = BridgeSync(args.config)
        
        if args.list_mdx:
            mdx_files = bridge.get_mdx_files()
            print(f"📋 Available MDX files: {len(mdx_files)}")
            for f in mdx_files:
                print(f"  - {f.name}")
            return
        
        if args.list_backups:
            backup_dir = bridge.config.get_backup_path()
            if backup_dir.exists():
                backups = [d for d in backup_dir.iterdir() 
                          if d.is_dir() and d.name.startswith('nextjs_content_backup_')]
                backups.sort(key=lambda x: x.stat().st_ctime, reverse=True)
                
                print(f"📋 Available backups: {len(backups)}")
                for backup in backups:
                    print(f"  - {backup.name}")
            else:
                print("📋 No backup directory found")
            return
        
        if args.rollback:
            backup_name = args.rollback if args.rollback != 'latest' else None
            success = bridge.rollback_sync(backup_name)
            if success:
                print("✅ Rollback successful")
            else:
                print("❌ Rollback failed")
            return
        
        # Determine limit
        limit = args.limit
        if args.sync_all:
            limit = None
        elif limit is None:
            limit = bridge.config.get_bridge_config().get('sync_batch_size', 50)
        
        # Perform bridge sync
        result = bridge.perform_bridge_sync(dry_run=args.dry_run, limit=limit)
        
        if result["success"]:
            if not args.dry_run:
                print(f"\n🎉 Bridge sync complete!")
                print(f"🚀 Next.js project updated with {result['synced']} articles")
            else:
                print(f"\n🧪 Dry run complete - no changes made")
        else:
            print(f"\n❌ Bridge sync failed: {result.get('message', 'Unknown error')}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()