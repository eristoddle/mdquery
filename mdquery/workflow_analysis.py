"""
Workflow analysis engine for mdquery.

This module provides specialized analysis capabilities for AI development workflows,
building on the tag analysis engine to provide process improvement insights,
development pattern recognition, and actionable recommendations.
"""

import re
import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict, Counter
from pathlib import Path
import json

from .models import QueryResult
from .query import QueryEngine
from .tag_analysis import TagAnalysisEngine, TagAnalysisResult, ActionableInsight, TheoreticalInsight, TopicGroup
from .exceptions import MdqueryError

logger = logging.getLogger(__name__)


@dataclass
class ImprovementOpportunity:
    """Represents a specific improvement opportunity in the development workflow."""
    title: str
    description: str
    category: str  # "process", "tools", "automation", "quality"
    implementation_difficulty: str  # "low", "medium", "high"
    expected_impact: str  # "low", "medium", "high"
    priority_score: float  # 0.0 to 1.0
    source_files: List[str]
    related_patterns: List[str]
    suggested_actions: List[str]


@dataclass
class WorkflowPattern:
    """Represents a detected pattern in the development workflow."""
    pattern_name: str
    description: str
    frequency: int
    files_involved: List[str]
    tags_involved: List[str]
    pattern_type: str  # "positive", "negative", "neutral"
    confidence_score: float


@dataclass
class WorkflowAnalysisResult:
    """Complete workflow analysis results."""
    topic_groups: List[TopicGroup]
    actionable_insights: List[ActionableInsight]
    theoretical_insights: List[TheoreticalInsight]
    improvement_opportunities: List[ImprovementOpportunity]
    workflow_patterns: List[WorkflowPattern]
    development_metrics: Dict[str, Any]
    recommendations: Dict[str, List[str]]


class WorkflowAnalyzer:
    """
    Specialized analyzer for AI development workflows.

    Extends the TagAnalysisEngine to provide development-specific insights,
    pattern recognition, and process improvement recommendations.
    """

    def __init__(self, query_engine: QueryEngine):
        """Initialize workflow analyzer."""
        self.query_engine = query_engine
        self.tag_analyzer = TagAnalysisEngine(query_engine)

        # Development-specific keywords and patterns
        self.development_keywords = {
            'mcp': ['mcp', 'model context protocol', 'mcp server', 'mcp tool'],
            'agents': ['agent', 'ai agent', 'autonomous', 'llm agent', 'assistant'],
            'automation': ['automation', 'automated', 'script', 'pipeline', 'ci/cd', 'deploy'],
            'coding': ['code', 'programming', 'development', 'implementation', 'refactor'],
            'testing': ['test', 'testing', 'unit test', 'integration test', 'qa'],
            'documentation': ['docs', 'documentation', 'readme', 'guide', 'tutorial'],
            'performance': ['performance', 'optimization', 'speed', 'efficiency', 'benchmark'],
            'debugging': ['debug', 'bug', 'issue', 'error', 'troubleshoot', 'fix'],
            'architecture': ['architecture', 'design', 'pattern', 'structure', 'framework'],
            'integration': ['integration', 'api', 'interface', 'connection', 'plugin']
        }

        # Workflow improvement patterns
        self.improvement_patterns = {
            'process_gaps': [
                'manual process', 'repetitive task', 'time consuming', 'inefficient',
                'bottleneck', 'slow process', 'manual intervention'
            ],
            'tool_opportunities': [
                'missing tool', 'need automation', 'could automate', 'tool gap',
                'manual work', 'repetitive coding', 'copy paste'
            ],
            'quality_issues': [
                'bug prone', 'error prone', 'inconsistent', 'unreliable',
                'hard to maintain', 'technical debt', 'code smell'
            ],
            'knowledge_gaps': [
                'need to learn', 'research needed', 'unclear approach',
                'best practice', 'how to', 'documentation missing'
            ]
        }

    def analyze_development_workflow(
        self,
        focus_areas: Optional[List[str]] = None,
        time_range: Optional[str] = None,
        improvement_categories: List[str] = None
    ) -> WorkflowAnalysisResult:
        """
        Analyze AI development workflow patterns and suggest improvements.

        Args:
            focus_areas: Specific areas to focus on (e.g., ["mcp", "agents", "automation"])
            time_range: Time range for analysis (e.g., "last-3-months")
            improvement_categories: Types of improvements to identify

        Returns:
            WorkflowAnalysisResult with comprehensive workflow analysis
        """
        logger.info(f"Starting development workflow analysis with focus areas: {focus_areas}")

        if improvement_categories is None:
            improvement_categories = ["process", "tools", "automation", "quality"]

        # Build tag patterns for development-focused analysis
        tag_patterns = self._build_development_tag_patterns(focus_areas)

        # Get base tag analysis
        base_analysis = self.tag_analyzer.comprehensive_tag_analysis(
            tag_patterns=tag_patterns,
            grouping_strategy="semantic",
            include_actionable=True,
            include_theoretical=True,
            remove_fluff=True,
            min_content_quality=0.4
        )

        # Enhance with workflow-specific analysis
        workflow_patterns = self._detect_workflow_patterns(base_analysis.topic_groups)
        improvement_opportunities = self._identify_improvement_opportunities(
            base_analysis.topic_groups,
            improvement_categories
        )
        development_metrics = self._calculate_development_metrics(base_analysis)
        recommendations = self._generate_workflow_recommendations(
            improvement_opportunities,
            workflow_patterns
        )

        return WorkflowAnalysisResult(
            topic_groups=base_analysis.topic_groups,
            actionable_insights=base_analysis.actionable_insights,
            theoretical_insights=base_analysis.theoretical_insights,
            improvement_opportunities=improvement_opportunities,
            workflow_patterns=workflow_patterns,
            development_metrics=development_metrics,
            recommendations=recommendations
        )

    def _build_development_tag_patterns(self, focus_areas: Optional[List[str]]) -> List[str]:
        """Build tag patterns focused on development workflow analysis."""
        patterns = []

        if focus_areas:
            # Use specified focus areas
            for area in focus_areas:
                area_lower = area.lower()
                if area_lower in self.development_keywords:
                    # Add hierarchical patterns for this area
                    patterns.extend([
                        area_lower,
                        f"{area_lower}/*",
                        f"*/{area_lower}",
                        f"*{area_lower}*"
                    ])
                else:
                    # Add as direct pattern
                    patterns.append(area_lower)
        else:
            # Default development-focused patterns
            patterns = [
                "ai/*", "llm/*", "mcp/*", "agent/*", "automation/*",
                "development/*", "coding/*", "tool/*", "workflow/*",
                "process/*", "testing/*", "debug/*", "performance/*"
            ]

        return patterns

    def _detect_workflow_patterns(self, topic_groups: List[TopicGroup]) -> List[WorkflowPattern]:
        """Detect patterns in the development workflow."""
        patterns = []

        for group in topic_groups:
            # Analyze content for workflow patterns
            group_content = []
            group_tags = []

            for doc in group.documents:
                content = doc.get('content', '').lower()
                group_content.append(content)
                group_tags.extend(doc.get('tags', []))

            combined_content = ' '.join(group_content)

            # Check for development patterns
            for category, keywords in self.development_keywords.items():
                keyword_count = sum(
                    combined_content.count(keyword.lower()) for keyword in keywords
                )

                if keyword_count >= 3:  # Threshold for pattern detection
                    pattern_type = self._classify_pattern_type(combined_content, keywords)

                    pattern = WorkflowPattern(
                        pattern_name=f"{category.title()} Focus Pattern",
                        description=f"Strong focus on {category} activities detected",
                        frequency=keyword_count,
                        files_involved=[doc['path'] for doc in group.documents],
                        tags_involved=list(set(group_tags)),
                        pattern_type=pattern_type,
                        confidence_score=min(1.0, keyword_count / 10.0)
                    )
                    patterns.append(pattern)

        # Sort by confidence and frequency
        patterns.sort(key=lambda p: (p.confidence_score, p.frequency), reverse=True)

        return patterns[:10]  # Limit to top 10 patterns

    def _classify_pattern_type(self, content: str, keywords: List[str]) -> str:
        """Classify whether a pattern is positive, negative, or neutral."""
        positive_indicators = [
            'success', 'working', 'effective', 'improved', 'optimized',
            'automated', 'streamlined', 'efficient', 'good practice'
        ]

        negative_indicators = [
            'problem', 'issue', 'bug', 'error', 'failed', 'broken',
            'slow', 'inefficient', 'manual', 'repetitive', 'difficult'
        ]

        positive_score = sum(1 for indicator in positive_indicators if indicator in content)
        negative_score = sum(1 for indicator in negative_indicators if indicator in content)

        if positive_score > negative_score:
            return "positive"
        elif negative_score > positive_score:
            return "negative"
        else:
            return "neutral"

    def _identify_improvement_opportunities(
        self,
        topic_groups: List[TopicGroup],
        categories: List[str]
    ) -> List[ImprovementOpportunity]:
        """Identify specific improvement opportunities in the workflow."""
        opportunities = []

        for group in topic_groups:
            group_content = []
            group_files = []

            for doc in group.documents:
                content = doc.get('content', '').lower()
                group_content.append(content)
                group_files.append(doc['path'])

            combined_content = ' '.join(group_content)

            # Check each improvement pattern category
            for pattern_category, indicators in self.improvement_patterns.items():
                if self._should_analyze_category(pattern_category, categories):
                    indicator_matches = []

                    for indicator in indicators:
                        if indicator in combined_content:
                            indicator_matches.append(indicator)

                    if len(indicator_matches) >= 2:  # Threshold for opportunity
                        opportunity = self._create_improvement_opportunity(
                            pattern_category,
                            indicator_matches,
                            group,
                            group_files,
                            combined_content
                        )
                        opportunities.append(opportunity)

        # Sort by priority score
        opportunities.sort(key=lambda o: o.priority_score, reverse=True)

        return opportunities[:15]  # Limit to top 15 opportunities

    def _should_analyze_category(self, pattern_category: str, categories: List[str]) -> bool:
        """Check if a pattern category should be analyzed based on requested categories."""
        category_mapping = {
            'process_gaps': 'process',
            'tool_opportunities': 'tools',
            'quality_issues': 'quality',
            'knowledge_gaps': 'process'
        }

        mapped_category = category_mapping.get(pattern_category, 'process')
        return mapped_category in categories

    def _create_improvement_opportunity(
        self,
        pattern_category: str,
        indicators: List[str],
        group: TopicGroup,
        files: List[str],
        content: str
    ) -> ImprovementOpportunity:
        """Create an improvement opportunity from detected patterns."""

        # Map pattern categories to improvement categories
        category_mapping = {
            'process_gaps': 'process',
            'tool_opportunities': 'tools',
            'quality_issues': 'quality',
            'knowledge_gaps': 'process'
        }

        category = category_mapping.get(pattern_category, 'process')

        # Generate title and description
        title = self._generate_opportunity_title(pattern_category, group.name)
        description = self._generate_opportunity_description(pattern_category, indicators)

        # Estimate difficulty and impact
        difficulty = self._estimate_opportunity_difficulty(pattern_category, content)
        impact = self._estimate_opportunity_impact(pattern_category, len(files))

        # Calculate priority score
        priority_score = self._calculate_priority_score(difficulty, impact, len(indicators))

        # Generate suggested actions
        suggested_actions = self._generate_suggested_actions(pattern_category, indicators)

        return ImprovementOpportunity(
            title=title,
            description=description,
            category=category,
            implementation_difficulty=difficulty,
            expected_impact=impact,
            priority_score=priority_score,
            source_files=files,
            related_patterns=indicators,
            suggested_actions=suggested_actions
        )

    def _generate_opportunity_title(self, pattern_category: str, group_name: str) -> str:
        """Generate a descriptive title for an improvement opportunity."""
        titles = {
            'process_gaps': f"Streamline {group_name} Process",
            'tool_opportunities': f"Automate {group_name} Tasks",
            'quality_issues': f"Improve {group_name} Quality",
            'knowledge_gaps': f"Document {group_name} Best Practices"
        }

        return titles.get(pattern_category, f"Improve {group_name}")

    def _generate_opportunity_description(self, pattern_category: str, indicators: List[str]) -> str:
        """Generate a description for an improvement opportunity."""
        descriptions = {
            'process_gaps': f"Manual processes detected that could be streamlined. Key indicators: {', '.join(indicators[:3])}",
            'tool_opportunities': f"Automation opportunities identified. Areas for tooling: {', '.join(indicators[:3])}",
            'quality_issues': f"Quality improvement opportunities found. Issues: {', '.join(indicators[:3])}",
            'knowledge_gaps': f"Knowledge documentation opportunities. Areas needing documentation: {', '.join(indicators[:3])}"
        }

        return descriptions.get(pattern_category, f"Improvement opportunity based on: {', '.join(indicators[:3])}")

    def _estimate_opportunity_difficulty(self, pattern_category: str, content: str) -> str:
        """Estimate implementation difficulty for an opportunity."""
        difficulty_mapping = {
            'process_gaps': 'medium',  # Process changes require coordination
            'tool_opportunities': 'low',  # Often can be automated
            'quality_issues': 'high',  # Quality improvements are complex
            'knowledge_gaps': 'low'  # Documentation is straightforward
        }

        base_difficulty = difficulty_mapping.get(pattern_category, 'medium')

        # Adjust based on content complexity
        complexity_indicators = ['complex', 'enterprise', 'scale', 'integration', 'architecture']
        if any(indicator in content for indicator in complexity_indicators):
            if base_difficulty == 'low':
                return 'medium'
            elif base_difficulty == 'medium':
                return 'high'

        return base_difficulty

    def _estimate_opportunity_impact(self, pattern_category: str, file_count: int) -> str:
        """Estimate expected impact of an opportunity."""
        # Base impact by category
        impact_mapping = {
            'process_gaps': 'high',  # Process improvements have broad impact
            'tool_opportunities': 'medium',  # Automation saves time
            'quality_issues': 'high',  # Quality affects everything
            'knowledge_gaps': 'medium'  # Documentation helps but not immediate
        }

        base_impact = impact_mapping.get(pattern_category, 'medium')

        # Adjust based on scope (number of files affected)
        if file_count >= 10:
            if base_impact == 'medium':
                return 'high'
        elif file_count <= 3:
            if base_impact == 'high':
                return 'medium'

        return base_impact

    def _calculate_priority_score(self, difficulty: str, impact: str, indicator_count: int) -> float:
        """Calculate priority score for an opportunity."""
        impact_scores = {'low': 0.3, 'medium': 0.6, 'high': 1.0}
        difficulty_scores = {'low': 1.0, 'medium': 0.7, 'high': 0.4}

        impact_score = impact_scores.get(impact, 0.6)
        difficulty_score = difficulty_scores.get(difficulty, 0.7)
        evidence_score = min(1.0, indicator_count / 5.0)

        # Weighted combination: impact is most important, then ease of implementation
        priority = (impact_score * 0.5) + (difficulty_score * 0.3) + (evidence_score * 0.2)

        return round(priority, 2)

    def _generate_suggested_actions(self, pattern_category: str, indicators: List[str]) -> List[str]:
        """Generate specific suggested actions for an opportunity."""
        actions = {
            'process_gaps': [
                "Identify repetitive manual steps",
                "Create process documentation",
                "Design automation workflow",
                "Implement process improvements"
            ],
            'tool_opportunities': [
                "Research existing automation tools",
                "Create custom scripts for repetitive tasks",
                "Set up CI/CD pipelines",
                "Integrate development tools"
            ],
            'quality_issues': [
                "Implement code review processes",
                "Add automated testing",
                "Create quality checklists",
                "Establish coding standards"
            ],
            'knowledge_gaps': [
                "Document current processes",
                "Create how-to guides",
                "Record best practices",
                "Build knowledge base"
            ]
        }

        return actions.get(pattern_category, ["Analyze and improve current approach"])

    def _calculate_development_metrics(self, base_analysis: TagAnalysisResult) -> Dict[str, Any]:
        """Calculate development-specific metrics."""
        metrics = base_analysis.content_statistics.copy()

        # Development focus metrics
        all_tags = []
        for group in base_analysis.topic_groups:
            all_tags.extend(group.tag_patterns)

        tag_counter = Counter(all_tags)

        # Calculate development area distribution
        dev_areas = {}
        for area, keywords in self.development_keywords.items():
            area_count = sum(
                tag_counter.get(keyword, 0) for keyword in keywords
                if keyword in tag_counter
            )
            if area_count > 0:
                dev_areas[area] = area_count

        metrics.update({
            'development_focus_areas': dev_areas,
            'most_active_dev_area': max(dev_areas.items(), key=lambda x: x[1])[0] if dev_areas else None,
            'development_diversity': len(dev_areas),
            'actionable_insight_count': len(base_analysis.actionable_insights),
            'theoretical_insight_count': len(base_analysis.theoretical_insights),
            'workflow_maturity_score': self._calculate_workflow_maturity(base_analysis)
        })

        return metrics

    def _calculate_workflow_maturity(self, analysis: TagAnalysisResult) -> float:
        """Calculate a workflow maturity score based on analysis results."""
        # Factors that indicate mature workflow
        factors = {
            'documentation_ratio': 0.0,
            'automation_ratio': 0.0,
            'testing_ratio': 0.0,
            'process_ratio': 0.0
        }

        total_insights = len(analysis.actionable_insights) + len(analysis.theoretical_insights)

        if total_insights > 0:
            # Count insights by category
            for insight in analysis.actionable_insights:
                if 'documentation' in insight.category.lower():
                    factors['documentation_ratio'] += 1
                elif 'automation' in insight.category.lower():
                    factors['automation_ratio'] += 1
                elif 'testing' in insight.category.lower() or 'quality' in insight.category.lower():
                    factors['testing_ratio'] += 1
                elif 'process' in insight.category.lower():
                    factors['process_ratio'] += 1

            # Normalize by total insights
            for key in factors:
                factors[key] = factors[key] / total_insights

        # Calculate weighted maturity score
        maturity = (
            factors['documentation_ratio'] * 0.25 +
            factors['automation_ratio'] * 0.35 +
            factors['testing_ratio'] * 0.25 +
            factors['process_ratio'] * 0.15
        )

        return round(maturity, 2)

    def _generate_workflow_recommendations(
        self,
        opportunities: List[ImprovementOpportunity],
        patterns: List[WorkflowPattern]
    ) -> Dict[str, List[str]]:
        """Generate high-level workflow recommendations."""
        recommendations = {
            'immediate_actions': [],
            'short_term_goals': [],
            'long_term_strategy': [],
            'tool_suggestions': []
        }

        # Sort opportunities by priority
        high_priority = [op for op in opportunities if op.priority_score >= 0.7]
        medium_priority = [op for op in opportunities if 0.4 <= op.priority_score < 0.7]

        # Immediate actions (high priority, low difficulty)
        for op in high_priority:
            if op.implementation_difficulty == 'low':
                recommendations['immediate_actions'].extend(op.suggested_actions[:2])

        # Short-term goals (high priority, medium difficulty)
        for op in high_priority:
            if op.implementation_difficulty == 'medium':
                recommendations['short_term_goals'].append(op.title)

        # Long-term strategy (high difficulty items)
        for op in opportunities:
            if op.implementation_difficulty == 'high' and op.expected_impact == 'high':
                recommendations['long_term_strategy'].append(op.title)

        # Tool suggestions based on patterns
        tool_opportunities = [op for op in opportunities if op.category == 'tools']
        for op in tool_opportunities[:3]:
            recommendations['tool_suggestions'].append(f"Consider tools for: {op.title}")

        # Limit recommendations
        for key in recommendations:
            recommendations[key] = recommendations[key][:5]

        return recommendations