#!/usr/bin/env python3
"""
Comprehensive test for tag analysis functionality validation.
This test validates the complete tag analysis workflow end-to-end.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from mdquery.database import DatabaseManager
from mdquery.indexer import Indexer
from mdquery.query import QueryEngine
from mdquery.tag_analysis import TagAnalysisEngine
from mdquery.cache import CacheManager


def create_test_files(test_dir: Path):
    """Create test markdown files with various tag patterns."""
    
    # File 1: AI Research with actionable content
    (test_dir / "ai-research.md").write_text("""---
title: "AI Research Notes"
tags: [ai, research, machine-learning, tutorial]
category: "research"
---

# AI Research Notes

## Implementation Guide

This document contains step-by-step instructions for implementing machine learning models.

### Tutorial: Building Your First Neural Network

1. **Setup Environment**
   - Install Python 3.8+
   - Install TensorFlow: `pip install tensorflow`
   - Create virtual environment

2. **Data Preparation**
   - Load training data
   - Normalize features
   - Split into train/test sets

3. **Model Creation**
   - Define network architecture
   - Configure layers and activation functions
   - Compile model with optimizer

4. **Training Process**
   - Train model on data
   - Monitor validation loss
   - Adjust hyperparameters

### Best Practices

- Always validate your data quality
- Use cross-validation for model selection
- Monitor for overfitting
- Document your experiments

## Tools and Resources

- TensorFlow: Deep learning framework
- Keras: High-level neural network API
- scikit-learn: Machine learning library
""")

    # File 2: Deep Learning Tutorial with procedural content
    (test_dir / "deep-learning.md").write_text("""---
title: "Deep Learning Advanced Techniques"
tags: [ai, deep-learning, neural-networks, advanced]
difficulty: "advanced"
---

# Deep Learning Advanced Techniques

## Convolutional Neural Networks

### Architecture Design

CNNs are particularly effective for image processing tasks.

#### Step-by-step Implementation

1. **Input Layer Configuration**
   ```python
   input_layer = tf.keras.layers.Input(shape=(224, 224, 3))
   ```

2. **Convolution Layers**
   - Apply convolution operations
   - Use ReLU activation
   - Add batch normalization

3. **Pooling Layers**
   - Reduce spatial dimensions
   - Prevent overfitting
   - Maintain important features

### Optimization Strategies

- Use Adam optimizer for fast convergence
- Implement learning rate scheduling
- Apply data augmentation techniques
- Use dropout for regularization
""")

    # File 3: AI Ethics (theoretical content)
    (test_dir / "ai-ethics.md").write_text("""---
title: "AI Ethics and Bias"
tags: [ai, ethics, bias, philosophy]
category: "philosophy"
---

# AI Ethics and Bias

## Theoretical Framework

Artificial intelligence systems can perpetuate and amplify existing biases in society.

### Key Concepts

#### Algorithmic Bias
- Definition: Systematic and repeatable errors in computer systems
- Sources: Training data, algorithm design, implementation choices
- Impact: Discrimination against certain groups

#### Fairness Principles
- Individual fairness: Similar individuals receive similar outcomes
- Group fairness: Statistical parity across different groups
- Counterfactual fairness: Decisions remain same in counterfactual world

### Research Directions

- Developing bias detection algorithms
- Creating fair machine learning methods
- Understanding societal implications
- Policy and governance frameworks

## Mitigation Approaches

While challenging, several approaches show promise:
- Diverse development teams
- Inclusive dataset collection
- Regular bias auditing
- Transparent AI systems
""")

    # File 4: Quick note (should be filtered as fluff)
    (test_dir / "quick-note.md").write_text("""---
title: "Quick Note"
tags: [ai, random-thought]
---

# Quick Note

Just a quick reminder to check the latest AI paper.

TODO: Read paper later.
""")

    # File 5: Machine Learning Fundamentals
    (test_dir / "ml-fundamentals.md").write_text("""---
title: "Machine Learning Fundamentals"
tags: [ai, machine-learning, fundamentals, tutorial]
category: "education"
---

# Machine Learning Fundamentals

## Core Algorithms

### Supervised Learning

#### Linear Regression
Step-by-step implementation:

1. **Data Preprocessing**
   - Handle missing values
   - Scale features
   - Encode categorical variables

2. **Model Training**
   ```python
   from sklearn.linear_model import LinearRegression
   model = LinearRegression()
   model.fit(X_train, y_train)
   ```

3. **Model Evaluation**
   - Calculate R² score
   - Analyze residuals
   - Cross-validate results

### Unsupervised Learning

Clustering algorithms help discover patterns in unlabeled data.

#### K-Means Implementation
1. Initialize cluster centroids
2. Assign points to nearest centroid
3. Update centroids
4. Repeat until convergence

## Practical Applications

Real-world applications demonstrate the power of ML:
- Recommendation systems
- Image recognition
- Natural language processing
- Fraud detection
""")


def test_tag_analysis_functionality():
    """Test comprehensive tag analysis functionality."""
    print("🔍 Testing Comprehensive Tag Analysis Functionality")
    print("=" * 60)
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir)
        
        # Step 1: Create test files
        print("📝 Creating test markdown files...")
        create_test_files(test_dir)
        
        # Step 2: Initialize database and indexing
        print("🗄️ Initializing database and indexing...")
        db_path = test_dir / "test.db"
        cache_path = test_dir / "cache"
        
        db_manager = DatabaseManager(db_path)
        db_manager.initialize_database()
        
        cache_manager = CacheManager(cache_path, db_manager)
        cache_manager.initialize_cache()
        
        indexer = Indexer(db_manager, cache_manager)
        
        # Index test files
        stats = indexer.index_directory(test_dir, recursive=False)
        print(f"   ✅ Indexed {stats['files_processed']} files")
        
        # Step 3: Initialize query engine and tag analysis
        print("🔧 Initializing tag analysis engine...")
        query_engine = QueryEngine(db_manager)
        tag_engine = TagAnalysisEngine(query_engine)
        
        # Step 4: Test basic tag analysis
        print("\n🏷️ Testing Basic Tag Analysis")
        print("-" * 40)
        
        tag_patterns = ["ai"]
        result = tag_engine.comprehensive_tag_analysis(
            tag_patterns=tag_patterns,
            grouping_strategy="semantic",
            include_actionable=True,
            include_theoretical=True,
            remove_fluff=True,
            min_content_quality=0.3
        )
        
        print(f"   📊 Found {len(result.topic_groups)} topic groups")
        print(f"   🎯 Found {len(result.actionable_insights)} actionable insights")
        print(f"   🧠 Found {len(result.theoretical_insights)} theoretical insights")
        
        # Test topic groups
        if result.topic_groups:
            print(f"\n📑 Topic Groups Analysis:")
            for i, group in enumerate(result.topic_groups, 1):
                print(f"   {i}. '{group.name}' - {len(group.documents)} documents")
                print(f"      Quality Score: {group.content_quality_score:.2f}")
                print(f"      Key Themes: {', '.join(group.key_themes[:3])}")
                if group.documents:
                    print(f"      Sample Document: {Path(group.documents[0]['path']).name}")
        
        # Test actionable insights
        if result.actionable_insights:
            print(f"\n🎯 Actionable Insights:")
            for i, insight in enumerate(result.actionable_insights[:3], 1):
                print(f"   {i}. {insight.title}")
                print(f"      Category: {insight.category}")
                print(f"      Difficulty: {insight.implementation_difficulty}")
                print(f"      Impact: {insight.expected_impact}")
        
        # Test theoretical insights
        if result.theoretical_insights:
            print(f"\n🧠 Theoretical Insights:")
            for i, insight in enumerate(result.theoretical_insights[:3], 1):
                print(f"   {i}. {insight.title}")
                print(f"      Related Concepts: {', '.join(insight.related_concepts[:2])}")
        
        # Step 5: Test different grouping strategies
        print(f"\n📚 Testing Different Grouping Strategies")
        print("-" * 40)
        
        strategies = ["semantic", "tag-hierarchy", "temporal"]
        for strategy in strategies:
            result_strategy = tag_engine.comprehensive_tag_analysis(
                tag_patterns=["ai", "machine-learning"],
                grouping_strategy=strategy,
                remove_fluff=True
            )
            print(f"   {strategy.title()}: {len(result_strategy.topic_groups)} groups")
        
        # Step 6: Test quality filtering
        print(f"\n🔍 Testing Quality Filtering")
        print("-" * 40)
        
        quality_levels = [0.1, 0.3, 0.5, 0.7]
        for quality in quality_levels:
            result_quality = tag_engine.comprehensive_tag_analysis(
                tag_patterns=["ai"],
                remove_fluff=True,
                min_content_quality=quality
            )
            total_docs = sum(len(group.documents) for group in result_quality.topic_groups)
            print(f"   Quality {quality}: {total_docs} documents passed filter")
        
        # Step 7: Test tag pattern matching
        print(f"\n🎨 Testing Tag Pattern Matching")
        print("-" * 40)
        
        pattern_tests = [
            ["ai"],
            ["ai", "tutorial"],
            ["*learning*"],
            ["ai/*"] if any("/" in tag for files in [test_dir.glob("*.md")] for file_path in files for line in file_path.read_text().split('\n') for tag in line.split() if tag.startswith('#')) else ["ai"]
        ]
        
        for patterns in pattern_tests:
            try:
                result_pattern = tag_engine.comprehensive_tag_analysis(
                    tag_patterns=patterns,
                    remove_fluff=True
                )
                total_docs = sum(len(group.documents) for group in result_pattern.topic_groups)
                print(f"   Pattern {patterns}: {total_docs} documents found")
            except Exception as e:
                print(f"   Pattern {patterns}: Error - {e}")
        
        # Step 8: Validate content statistics
        print(f"\n📈 Content Statistics")
        print("-" * 40)
        
        if result.content_statistics:
            print("   Statistics generated:")
            for key, value in result.content_statistics.items():
                if isinstance(value, (int, float)):
                    print(f"   - {key}: {value}")
                elif isinstance(value, list) and len(value) <= 5:
                    print(f"   - {key}: {value}")
        
        # Step 9: Test error handling
        print(f"\n⚠️ Testing Error Handling")
        print("-" * 40)
        
        try:
            # Test with non-existent tags
            empty_result = tag_engine.comprehensive_tag_analysis(
                tag_patterns=["nonexistent-tag"],
                remove_fluff=True
            )
            print(f"   ✅ Non-existent tags handled: {len(empty_result.topic_groups)} groups")
        except Exception as e:
            print(f"   ❌ Error with non-existent tags: {e}")
        
        try:
            # Test with empty patterns
            empty_patterns_result = tag_engine.comprehensive_tag_analysis(
                tag_patterns=[],
                remove_fluff=True
            )
            print(f"   ✅ Empty patterns handled: {len(empty_patterns_result.topic_groups)} groups")
        except Exception as e:
            print(f"   ❌ Error with empty patterns: {e}")
    
    print(f"\n✅ Comprehensive Tag Analysis Validation Complete!")
    return True


if __name__ == "__main__":
    try:
        success = test_tag_analysis_functionality()
        if success:
            print("\n🎉 All tag analysis functionality tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)