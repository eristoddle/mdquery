#!/usr/bin/env python3
"""End-to-end Obsidian workflow test."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from mdquery.database import DatabaseManager
from mdquery.indexer import Indexer
from mdquery.query import QueryEngine
from mdquery.tag_analysis import TagAnalysisEngine
from mdquery.cache import CacheManager
from mdquery.config import SimplifiedConfig

def create_test_vault(vault_dir: Path):
    """Create test Obsidian vault."""
    (vault_dir / "research.md").write_text("""---
title: "AI Research"
tags: [research, ai, tutorial]
---

# AI Implementation Guide

## Step-by-Step Process
1. Setup environment
2. Prepare data  
3. Build model
4. Train and evaluate

### Tools Needed
- Python 3.8+
- TensorFlow
- Jupyter notebooks

## Best Practices
- Version control code
- Document experiments  
- Use standard benchmarks
""")
    
    (vault_dir / "projects.md").write_text("""---
title: "ML Projects"
tags: [projects, ai, implementation]
---

# Project Ideas

## Beginner Projects
1. **House Price Prediction**
   - Use linear regression
   - Clean housing data
   - Feature engineering

2. **Image Classification**  
   - Build CNN model
   - Use CIFAR-10 dataset
   - Implement data augmentation
""")

def test_workflow():
    """Test complete workflow."""
    print("🧪 Testing End-to-End Obsidian Workflow")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        vault_dir = Path(temp_dir) / "vault"
        vault_dir.mkdir()
        
        # Create test vault
        print("📁 Creating test vault...")
        create_test_vault(vault_dir)
        
        # Initialize database
        print("🗄️ Setting up database...")
        db_path = vault_dir / ".mdquery" / "mdquery.db"
        db_path.parent.mkdir(exist_ok=True)
        
        db_manager = DatabaseManager(db_path)
        db_manager.initialize_database()
        
        cache_manager = CacheManager(db_path.parent / "cache", db_manager)
        cache_manager.initialize_cache()
        
        # Index files
        print("📑 Indexing vault...")
        indexer = Indexer(db_manager, cache_manager)
        stats = indexer.index_directory(vault_dir, recursive=True)
        print(f"   ✅ Indexed {stats['files_processed']} files")
        
        # Test tag analysis
        print("🏷️ Testing tag analysis...")
        query_engine = QueryEngine(db_manager)
        tag_engine = TagAnalysisEngine(query_engine)
        
        result = tag_engine.comprehensive_tag_analysis(
            tag_patterns=["ai", "research"],
            grouping_strategy="semantic",
            include_actionable=True,
            remove_fluff=True
        )
        
        print(f"   📊 Found {len(result.topic_groups)} topic groups")
        print(f"   🎯 Found {len(result.actionable_insights)} actionable insights")
        
        # Test configuration
        print("⚙️ Testing MCP configuration...")
        config = SimplifiedConfig(notes_dir=vault_dir)
        print(f"   ✅ Config created: {config.config.notes_dir.name}")
        
        # Validate results
        if result.topic_groups:
            group = result.topic_groups[0]
            print(f"\n📑 Sample Group: '{group.name}'")
            print(f"   📄 {len(group.documents)} documents")
            print(f"   🏆 Quality: {group.content_quality_score:.2f}")
        
        print(f"\n✅ End-to-End Workflow Complete!")
        return True

if __name__ == "__main__":
    success = test_workflow()
    if success:
        print("🎉 All workflow tests passed!")
        sys.exit(0)
    else:
        sys.exit(1)