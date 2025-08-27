"""
Auto-Configuration Manager for mdquery.

Provides intelligent detection of note-taking systems and automatic
configuration of optimal settings for different platforms.
"""

import os
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class NoteSystemType(Enum):
    """Supported note-taking system types."""
    OBSIDIAN = "obsidian"
    JOPLIN = "joplin"
    JEKYLL = "jekyll"
    HUGO = "hugo"
    LOGSEQ = "logseq"
    GENERIC = "generic"


@dataclass
class SystemDetectionResult:
    """Result of note system detection."""
    system_type: NoteSystemType
    confidence: float
    evidence: List[str]
    config_files: List[str]
    special_directories: List[str]
    file_patterns: Dict[str, int]


@dataclass
class OptimalConfiguration:
    """Optimal configuration for a detected note system."""
    system_type: NoteSystemType
    performance_mode: str
    indexing_strategy: str
    optimization_settings: Dict[str, Any]
    cache_settings: Dict[str, Any]
    recommended_env_vars: Dict[str, str]


class AutoConfigurationManager:
    """Intelligent auto-configuration manager for mdquery."""

    def __init__(self):
        """Initialize the auto-configuration manager."""
        self.detection_patterns = {
            NoteSystemType.OBSIDIAN: {
                "config_files": [".obsidian/config", ".obsidian/workspace"],
                "directories": [".obsidian"],
                "patterns": {"wikilinks": r"\[\[([^\]]+)\]\]", "nested_tags": r"#\w+/\w+"},
                "confidence_weights": {".obsidian": 0.8, "wikilinks": 0.3}
            },
            NoteSystemType.JOPLIN: {
                "config_files": ["resources"],
                "directories": ["resources"],
                "patterns": {"joplin_id": r"^id: [a-f0-9]{32}$"},
                "confidence_weights": {"joplin_id": 0.9, "resources": 0.3}
            },
            NoteSystemType.JEKYLL: {
                "config_files": ["_config.yml", "Gemfile"],
                "directories": ["_posts", "_drafts"],
                "patterns": {"date_prefix": r"^\d{4}-\d{2}-\d{2}-", "liquid": r"\{\%.*?\%\}"},
                "confidence_weights": {"_config.yml": 0.8, "_posts": 0.6}
            },
            NoteSystemType.HUGO: {
                "config_files": ["config.toml", "hugo.toml"],
                "directories": ["content", "static"],
                "patterns": {"shortcodes": r"\{\{<.*?>\}\}"},
                "confidence_weights": {"config.toml": 0.8, "content": 0.6}
            },
            NoteSystemType.LOGSEQ: {
                "config_files": ["logseq/config.edn"],
                "directories": ["logseq", "pages", "journals"],
                "patterns": {"block_refs": r"\(\([a-f0-9-]{36}\)\)"},
                "confidence_weights": {"logseq": 0.9, "block_refs": 0.5}
            }
        }

        self.optimal_configs = {
            NoteSystemType.OBSIDIAN: OptimalConfiguration(
                system_type=NoteSystemType.OBSIDIAN,
                performance_mode="high",
                indexing_strategy="incremental",
                optimization_settings={
                    "auto_optimize": True,
                    "cache_ttl": 240,
                    "concurrent_queries": 5,
                    "lazy_loading": True
                },
                cache_settings={
                    "enable_query_cache": True,
                    "max_cache_size_mb": 500
                },
                recommended_env_vars={
                    "MDQUERY_PERFORMANCE_MODE": "high",
                    "MDQUERY_AUTO_OPTIMIZE": "true",
                    "MDQUERY_CACHE_TTL": "240"
                }
            ),
            NoteSystemType.JEKYLL: OptimalConfiguration(
                system_type=NoteSystemType.JEKYLL,
                performance_mode="medium",
                indexing_strategy="selective",
                optimization_settings={
                    "auto_optimize": True,
                    "cache_ttl": 480,
                    "concurrent_queries": 3
                },
                cache_settings={
                    "enable_query_cache": True,
                    "max_cache_size_mb": 300
                },
                recommended_env_vars={
                    "MDQUERY_PERFORMANCE_MODE": "medium",
                    "MDQUERY_EXCLUDE_PATTERNS": "_site,vendor,.bundle"
                }
            ),
            NoteSystemType.GENERIC: OptimalConfiguration(
                system_type=NoteSystemType.GENERIC,
                performance_mode="low",
                indexing_strategy="full",
                optimization_settings={
                    "auto_optimize": False,
                    "cache_ttl": 60,
                    "concurrent_queries": 2
                },
                cache_settings={
                    "enable_query_cache": True,
                    "max_cache_size_mb": 100
                },
                recommended_env_vars={
                    "MDQUERY_PERFORMANCE_MODE": "low"
                }
            )
        }

    def detect_note_system(self, directory: str) -> SystemDetectionResult:
        """Detect the note-taking system type for a directory."""
        directory_path = Path(directory)

        if not directory_path.exists():
            raise ValueError(f"Directory does not exist: {directory}")

        analysis = self._analyze_directory(directory_path)
        system_scores = {}

        for system_type, patterns in self.detection_patterns.items():
            score = self._calculate_score(analysis, patterns)
            system_scores[system_type] = score

        best_system = max(system_scores.keys(), key=lambda k: system_scores[k])
        best_score = system_scores[best_system]

        if best_score < 0.3:
            best_system = NoteSystemType.GENERIC
            best_score = 0.3

        evidence = self._gather_evidence(analysis, self.detection_patterns[best_system])

        return SystemDetectionResult(
            system_type=best_system,
            confidence=best_score,
            evidence=evidence,
            config_files=analysis.get("config_files", []),
            special_directories=analysis.get("special_directories", []),
            file_patterns=analysis.get("file_patterns", {})
        )

    def _analyze_directory(self, directory_path: Path) -> Dict[str, Any]:
        """Analyze directory structure and file patterns."""
        analysis = {
            "config_files": [],
            "special_directories": [],
            "file_patterns": {}
        }

        for root, dirs, files in os.walk(directory_path):
            root_path = Path(root)
            relative_root = root_path.relative_to(directory_path)

            # Check directories
            for dir_name in dirs:
                if dir_name in [".obsidian", "_posts", "_drafts", "content", "logseq", "resources"]:
                    analysis["special_directories"].append(str(relative_root / dir_name))

            # Check files
            for file_name in files:
                file_path = root_path / file_name
                relative_file = relative_root / file_name

                # Config files
                if file_name in ["_config.yml", "config.toml", "Gemfile"] or ".obsidian" in str(file_path):
                    analysis["config_files"].append(str(relative_file))

                # Analyze markdown files
                if file_name.endswith(('.md', '.markdown')):
                    self._analyze_markdown_file(file_path, analysis)

        return analysis

    def _analyze_markdown_file(self, file_path: Path, analysis: Dict[str, Any]) -> None:
        """Analyze markdown file for patterns."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            import re
            patterns = {
                "wikilinks": len(re.findall(r'\[\[([^\]]+)\]\]', content)),
                "nested_tags": len(re.findall(r'#\w+/\w+', content)),
                "liquid": len(re.findall(r'\{\%.*?\%\}', content)),
                "shortcodes": len(re.findall(r'\{\{<.*?>\}\}', content)),
                "block_refs": len(re.findall(r'\(\([a-f0-9-]{36}\)\)', content)),
                "joplin_id": len(re.findall(r'^id: [a-f0-9]{32}$', content, re.MULTILINE))
            }

            for pattern, count in patterns.items():
                if pattern not in analysis["file_patterns"]:
                    analysis["file_patterns"][pattern] = 0
                analysis["file_patterns"][pattern] += count

        except (OSError, UnicodeDecodeError):
            pass

    def _calculate_score(self, analysis: Dict[str, Any], patterns: Dict[str, Any]) -> float:
        """Calculate confidence score for a system type."""
        score = 0.0
        max_score = 0.0
        weights = patterns.get("confidence_weights", {})

        # Check config files and directories
        for item in patterns.get("config_files", []) + patterns.get("directories", []):
            max_score += weights.get(item, 0.5)
            if any(item in found for found in
                   analysis.get("config_files", []) + analysis.get("special_directories", [])):
                score += weights.get(item, 0.5)

        # Check file patterns
        file_patterns = analysis.get("file_patterns", {})
        for pattern in patterns.get("patterns", {}):
            max_score += weights.get(pattern, 0.2)
            if file_patterns.get(pattern, 0) > 0:
                frequency_score = min(file_patterns[pattern] / 10.0, 1.0)
                score += weights.get(pattern, 0.2) * frequency_score

        return score / max_score if max_score > 0 else 0.0

    def _gather_evidence(self, analysis: Dict[str, Any], patterns: Dict[str, Any]) -> List[str]:
        """Gather evidence for detected system type."""
        evidence = []

        for config_file in patterns.get("config_files", []):
            if any(config_file in cf for cf in analysis.get("config_files", [])):
                evidence.append(f"Configuration file found: {config_file}")

        for directory in patterns.get("directories", []):
            if any(directory in sd for sd in analysis.get("special_directories", [])):
                evidence.append(f"Special directory found: {directory}")

        file_patterns = analysis.get("file_patterns", {})
        for pattern in patterns.get("patterns", {}):
            count = file_patterns.get(pattern, 0)
            if count > 0:
                evidence.append(f"{pattern} pattern found {count} times")

        return evidence

    def generate_optimal_configuration(self, detection_result: SystemDetectionResult,
                                     directory: str) -> OptimalConfiguration:
        """Generate optimal configuration based on detection results."""
        base_config = self.optimal_configs.get(detection_result.system_type)
        if not base_config:
            base_config = self.optimal_configs[NoteSystemType.GENERIC]

        # Customize based on directory size
        config_dict = asdict(base_config)
        total_files = sum(1 for _ in Path(directory).rglob("*.md"))

        if total_files > 5000:
            config_dict["performance_mode"] = "high"
            config_dict["optimization_settings"]["concurrent_queries"] = 3
        elif total_files > 1000:
            config_dict["performance_mode"] = "medium"

        # Add notes directory to env vars
        config_dict["recommended_env_vars"]["MDQUERY_NOTES_DIR"] = directory

        return OptimalConfiguration(**config_dict)

    def auto_configure_directory(self, directory: str,
                                output_path: Optional[str] = None) -> Tuple[SystemDetectionResult, OptimalConfiguration]:
        """Automatically detect and configure a notes directory."""
        detection_result = self.detect_note_system(directory)
        optimal_config = self.generate_optimal_configuration(detection_result, directory)

        if output_path:
            self.save_configuration(optimal_config, output_path)

        return detection_result, optimal_config

    def save_configuration(self, config: OptimalConfiguration, output_path: str) -> None:
        """Save configuration to a file."""
        config_data = {
            "auto_generated": True,
            "generated_at": datetime.now().isoformat(),
            "system_type": config.system_type.value,
            "mcp_configuration": {
                "mcpServers": {
                    "mdquery": {
                        "command": "python",
                        "args": ["-m", "mdquery.mcp_server"],
                        "env": config.recommended_env_vars
                    }
                }
            },
            "optimization_settings": asdict(config)
        }

        with open(output_path, 'w') as f:
            json.dump(config_data, f, indent=2, default=str)

        logger.info(f"Configuration saved to {output_path}")

    def get_configuration_summary(self, config: OptimalConfiguration) -> str:
        """Get human-readable configuration summary."""
        return f"""
Optimal Configuration for {config.system_type.value.title()}
{'=' * 50}

Performance Settings:
- Mode: {config.performance_mode}
- Indexing: {config.indexing_strategy}
- Concurrent Queries: {config.optimization_settings.get('concurrent_queries', 'default')}
- Cache TTL: {config.optimization_settings.get('cache_ttl', 'default')} minutes

Recommended Environment Variables:
{chr(10).join(f'- {k}={v}' for k, v in config.recommended_env_vars.items())}
"""


def create_auto_configuration_manager() -> AutoConfigurationManager:
    """Create an auto-configuration manager instance."""
    return AutoConfigurationManager()