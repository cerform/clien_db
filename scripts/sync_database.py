#!/usr/bin/env python3
"""
Database synchronization script
Синхронизирует данные из Google Sheets в локальное хранилище/кэш
"""

import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from src.db.sheets_client import GoogleSheetsClient
from src.config import get_config


class DatabaseSyncManager:
    """Manage database synchronization with Google Sheets"""
    
    SYNC_CACHE_DIR = Path(__file__).parent / ".sync_cache"
    CACHE_TTL = 3600  # 1 hour
    
    TABLES_TO_SYNC = [
        "masters",
        "services", 
        "schedule",
        "bookings",
        "clients"
    ]
    
    def __init__(self):
        """Initialize sync manager"""
        self.config = get_config()
        self.sheets_client = GoogleSheetsClient(
            self.config.google_credentials_json,
            self.config.google_spreadsheet_id
        )
        self.SYNC_CACHE_DIR.mkdir(exist_ok=True)
        logger.info(f"📁 Sync cache directory: {self.SYNC_CACHE_DIR}")
    
    def get_cache_file(self, table_name: str) -> Path:
        """Get path to cache file for a table"""
        return self.SYNC_CACHE_DIR / f"{table_name}_cache.json"
    
    def is_cache_valid(self, table_name: str) -> bool:
        """Check if cache is still valid (not expired)"""
        cache_file = self.get_cache_file(table_name)
        
        if not cache_file.exists():
            logger.warning(f"⚠️  Cache for {table_name} doesn't exist")
            return False
        
        # Check file age
        file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        is_valid = file_age < timedelta(seconds=self.CACHE_TTL)
        
        if is_valid:
            logger.info(f"✅ Cache for {table_name} is valid ({int(file_age.total_seconds())}s old)")
        else:
            logger.warning(f"⏰ Cache for {table_name} expired ({int(file_age.total_seconds())}s old)")
        
        return is_valid
    
    def save_cache(self, table_name: str, data: List[Dict[str, Any]]) -> bool:
        """Save table data to cache"""
        try:
            cache_file = self.get_cache_file(table_name)
            
            cache_data = {
                "table": table_name,
                "timestamp": datetime.now().isoformat(),
                "row_count": len(data),
                "data": data
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 Saved cache for {table_name} ({len(data)} rows)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save cache for {table_name}: {e}")
            return False
    
    def load_cache(self, table_name: str) -> Optional[List[Dict[str, Any]]]:
        """Load table data from cache"""
        try:
            cache_file = self.get_cache_file(table_name)
            
            if not cache_file.exists():
                logger.warning(f"⚠️  Cache file doesn't exist: {cache_file}")
                return None
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            logger.info(f"📖 Loaded cache for {table_name} ({cache_data.get('row_count', 0)} rows)")
            return cache_data.get('data', [])
            
        except Exception as e:
            logger.error(f"❌ Failed to load cache for {table_name}: {e}")
            return None
    
    def fetch_table(self, table_name: str) -> List[Dict[str, Any]]:
        """Fetch table from Google Sheets"""
        try:
            logger.info(f"🔄 Fetching {table_name} from Google Sheets...")
            
            rows = self.sheets_client.get_all_rows(table_name)
            
            if not rows:
                logger.warning(f"⚠️  No data found in {table_name}")
                return []
            
            # Convert rows to list of dicts
            headers = rows[0]
            data = []
            
            for row in rows[1:]:
                # Pad row if needed
                if len(row) < len(headers):
                    row = row + [''] * (len(headers) - len(row))
                
                row_dict = {headers[i]: row[i] for i in range(len(headers))}
                data.append(row_dict)
            
            logger.info(f"✅ Fetched {table_name}: {len(data)} rows")
            return data
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch {table_name}: {e}")
            return []
    
    def sync_table(self, table_name: str, force: bool = False) -> Dict[str, Any]:
        """Sync a single table"""
        logger.info(f"\n{'='*80}")
        logger.info(f"🔄 Syncing table: {table_name}")
        logger.info(f"{'='*80}")
        
        # Check cache validity
        if not force and self.is_cache_valid(table_name):
            logger.info(f"✅ Using cached data for {table_name}")
            cached_data = self.load_cache(table_name)
            return {
                "table": table_name,
                "status": "cached",
                "rows": len(cached_data) if cached_data else 0,
                "timestamp": datetime.now().isoformat()
            }
        
        # Fetch from Google Sheets
        data = self.fetch_table(table_name)
        
        if not data:
            logger.warning(f"⚠️  No data fetched for {table_name}")
            return {
                "table": table_name,
                "status": "error",
                "error": "No data fetched",
                "rows": 0,
                "timestamp": datetime.now().isoformat()
            }
        
        # Save to cache
        success = self.save_cache(table_name, data)
        
        return {
            "table": table_name,
            "status": "synced" if success else "failed",
            "rows": len(data),
            "timestamp": datetime.now().isoformat()
        }
    
    def sync_all(self, force: bool = False) -> Dict[str, Any]:
        """Sync all tables"""
        logger.info(f"\n{'#'*80}")
        logger.info(f"# DATABASE SYNCHRONIZATION STARTED")
        logger.info(f"# Force sync: {force}")
        logger.info(f"{'#'*80}\n")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "tables": {},
            "summary": {
                "total": 0,
                "synced": 0,
                "cached": 0,
                "failed": 0,
                "total_rows": 0
            }
        }
        
        for table_name in self.TABLES_TO_SYNC:
            try:
                result = self.sync_table(table_name, force=force)
                results["tables"][table_name] = result
                
                # Update summary
                results["summary"]["total"] += 1
                results["summary"]["total_rows"] += result.get("rows", 0)
                
                if result["status"] == "synced":
                    results["summary"]["synced"] += 1
                elif result["status"] == "cached":
                    results["summary"]["cached"] += 1
                else:
                    results["summary"]["failed"] += 1
                    
            except Exception as e:
                logger.error(f"❌ Exception while syncing {table_name}: {e}")
                results["tables"][table_name] = {
                    "table": table_name,
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                results["summary"]["failed"] += 1
        
        # Print summary
        logger.info(f"\n{'#'*80}")
        logger.info(f"# SYNCHRONIZATION COMPLETE")
        logger.info(f"{'#'*80}")
        logger.info(f"📊 Summary:")
        logger.info(f"   Total tables: {results['summary']['total']}")
        logger.info(f"   Synced: {results['summary']['synced']}")
        logger.info(f"   Cached: {results['summary']['cached']}")
        logger.info(f"   Failed: {results['summary']['failed']}")
        logger.info(f"   Total rows: {results['summary']['total_rows']}")
        logger.info(f"{'#'*80}\n")
        
        return results
    
    def get_table_data(self, table_name: str, use_cache: bool = True) -> Optional[List[Dict[str, Any]]]:
        """Get table data (cached or fresh)"""
        if use_cache:
            cached_data = self.load_cache(table_name)
            if cached_data:
                return cached_data
        
        # Fetch from Sheets
        data = self.fetch_table(table_name)
        if data:
            self.save_cache(table_name, data)
        
        return data
    
    def print_table(self, table_name: str, max_rows: int = 10):
        """Print table data in a readable format"""
        data = self.get_table_data(table_name)
        
        if not data:
            logger.info(f"❌ No data for {table_name}")
            return
        
        logger.info(f"\n📋 Table: {table_name} ({len(data)} rows)")
        logger.info("=" * 100)
        
        # Print headers
        headers = list(data[0].keys())
        logger.info(f"Columns: {headers}")
        logger.info("-" * 100)
        
        # Print rows
        for i, row in enumerate(data[:max_rows]):
            logger.info(f"Row {i+1}: {row}")
        
        if len(data) > max_rows:
            logger.info(f"... and {len(data) - max_rows} more rows")
        logger.info("=" * 100)


def main():
    """Main sync function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Sync database with Google Sheets")
    parser.add_argument("--table", help="Sync specific table only")
    parser.add_argument("--force", action="store_true", help="Force sync (ignore cache)")
    parser.add_argument("--print", action="store_true", help="Print table data")
    parser.add_argument("--cache-dir", help="Show cache directory")
    
    args = parser.parse_args()
    
    try:
        sync_manager = DatabaseSyncManager()
        
        if args.cache_dir:
            logger.info(f"📁 Cache directory: {sync_manager.SYNC_CACHE_DIR}")
            logger.info(f"Cache files:")
            for cache_file in sorted(sync_manager.SYNC_CACHE_DIR.glob("*.json")):
                file_size = cache_file.stat().st_size
                logger.info(f"   {cache_file.name} ({file_size} bytes)")
            return
        
        if args.table:
            # Sync specific table
            if args.print:
                sync_manager.print_table(args.table)
            else:
                result = sync_manager.sync_table(args.table, force=args.force)
                logger.info(f"\nResult: {json.dumps(result, indent=2)}")
        else:
            # Sync all tables
            results = sync_manager.sync_all(force=args.force)
            
            # Print results
            logger.info(f"\nFull results:")
            logger.info(json.dumps(results, indent=2))
            
            if args.print:
                logger.info("\n\nTable Data:")
                for table_name in sync_manager.TABLES_TO_SYNC:
                    sync_manager.print_table(table_name, max_rows=3)
    
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
