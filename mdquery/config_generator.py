"""
Automatic Configuration Generator for mdquery.

This module provides automatic generation of optimal configurations
based on detected note systems, including Claude Desktop configurations,
MCP server settings, and system-specific optimizations.

Implements requirements from task 12b of the MCP workflow optimization spec.
"""

import json
import os
import platform
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging

from .auto_config import (
    AutoConfigurationManager,
    SystemDetectionResult,
    OptimalConfiguration,
    NoteSystemType
)

logger = logging.getLogger(__name__)


@dataclass
class ConfigurationTemplate:
    """Template for generating configurations."""
    name: str
    system_type: NoteSystemType
    description: str
    template_data: Dict[str, Any]
    requirements: List[str]
    recommendations: List[str]


@dataclass
class GeneratedConfiguration:
    """Complete generated configuration package."""
    detection_result: SystemDetectionResult
    optimal_config: OptimalConfiguration
    claude_config: Dict[str, Any]
    env_script: str
    setup_instructions: List[str]
    template_used: ConfigurationTemplate


class AutomaticConfigurationGenerator:
    """
    Automatic configuration generator for mdquery.

    Generates complete configuration packages including:
    - Claude Desktop configuration
    - Environment variables setup
    - System-specific optimizations
    - Setup instructions
    """

    def __init__(self):
        """Initialize the configuration generator."""
        self.auto_config_manager = AutoConfigurationManager()
        self.templates = self._initialize_templates()

    def _initialize_templates(self) -> Dict[NoteSystemType, ConfigurationTemplate]:
        """Initialize configuration templates for different systems."""
        return {
            NoteSystemType.OBSIDIAN: ConfigurationTemplate(
                name="Obsidian Optimized",
                system_type=NoteSystemType.OBSIDIAN,
                description="Optimized configuration for Obsidian vaults with wikilinks and nested tags support",
                template_data={
                    "features": ["wikilinks", "nested_tags", "dataview_fields", "canvas_support"],
                    "performance_profile": "high",
                    "indexing_strategy": "incremental",
                    "special_handling": ["daily_notes", "templates", "plugins"]
                },
                requirements=[
                    "Obsidian vault directory",
                    "Python 3.8+",
                    "mdquery package installed"
                ],
                recommendations=[
                    "Enable auto-optimization for best performance",
                    "Use high cache TTL for active vaults",
                    "Consider excluding attachment directories for large vaults"
                ]
            ),

            NoteSystemType.JEKYLL: ConfigurationTemplate(
                name="Jekyll Site Optimized",
                system_type=NoteSystemType.JEKYLL,
                description="Optimized configuration for Jekyll static sites with posts and pages",
                template_data={
                    "features": ["liquid_tags", "frontmatter", "collections", "categories"],
                    "performance_profile": "medium",
                    "indexing_strategy": "selective",
                    "exclusions": ["_site", "vendor", ".bundle", ".sass-cache"]
                },
                requirements=[
                    "Jekyll site directory",
                    "_config.yml file present",
                    "Posts in _posts directory"
                ],
                recommendations=[
                    "Exclude generated directories for better performance",
                    "Use longer cache TTL for static content",
                    "Enable date-based organization analysis"
                ]
            ),

            NoteSystemType.HUGO: ConfigurationTemplate(
                name="Hugo Site Optimized",
                system_type=NoteSystemType.HUGO,
                description="Optimized configuration for Hugo static sites with content and themes",
                template_data={
                    "features": ["shortcodes", "page_bundles", "taxonomies", "archetypes"],
                    "performance_profile": "medium",
                    "indexing_strategy": "selective",
                    "exclusions": ["public", "resources", "node_modules"]
                },
                requirements=[
                    "Hugo site directory",
                    "config.toml or config.yaml file",
                    "Content directory"
                ],
                recommendations=[
                    "Enable taxonomy analysis for better categorization",
                    "Use selective indexing for large sites",
                    "Consider shortcode processing for rich content"
                ]
            ),

            NoteSystemType.LOGSEQ: ConfigurationTemplate(
                name="Logseq Graph Optimized",
                system_type=NoteSystemType.LOGSEQ,
                description="Optimized configuration for Logseq knowledge graphs with block references",
                template_data={
                    "features": ["block_refs", "page_refs", "journals", "queries"],
                    "performance_profile": "high",
                    "indexing_strategy": "incremental",
                    "special_handling": ["journals", "templates", "queries"]
                },
                requirements=[
                    "Logseq graph directory",
                    "logseq/config.edn file",
                    "Pages and journals directories"
                ],
                recommendations=[
                    "Enable block reference tracking",
                    "Use incremental indexing for performance",
                    "Consider journal-specific analysis"
                ]
            ),

            NoteSystemType.GENERIC: ConfigurationTemplate(
                name="Generic Markdown",
                system_type=NoteSystemType.GENERIC,
                description="Basic configuration for generic markdown collections",
                template_data={
                    "features": ["basic_frontmatter", "simple_tags", "standard_links"],
                    "performance_profile": "low",
                    "indexing_strategy": "full",
                    "special_handling": []
                },
                requirements=[
                    "Directory with markdown files",
                    "Basic frontmatter (optional)"
                ],
                recommendations=[
                    "Start with conservative settings",
                    "Enable optimizations after testing",
                    "Consider upgrading to specialized system"
                ]
            )
        }

    def generate_complete_configuration(self, directory: str,
                                      output_dir: Optional[str] = None,
                                      assistant_type: str = "claude") -> GeneratedConfiguration:
        """
        Generate a complete configuration package for a notes directory.

        Args:
            directory: Path to notes directory
            output_dir: Optional directory to save configuration files
            assistant_type: AI assistant type (claude, gpt, generic)

        Returns:
            GeneratedConfiguration with all configuration components
        """
        logger.info(f"Generating complete configuration for: {directory}")

        # Detect note system
        detection_result = self.auto_config_manager.detect_note_system(directory)
        logger.info(f"Detected system: {detection_result.system_type.value} (confidence: {detection_result.confidence:.2f})")

        # Generate optimal configuration
        optimal_config = self.auto_config_manager.generate_optimal_configuration(detection_result, directory)

        # Get appropriate template
        template = self.templates[detection_result.system_type]

        # Generate Claude Desktop configuration
        claude_config = self._generate_claude_config(optimal_config, assistant_type)

        # Generate environment setup script
        env_script = self._generate_env_script(optimal_config)

        # Generate setup instructions
        setup_instructions = self._generate_setup_instructions(detection_result, optimal_config, template)

        # Save files if output directory specified
        if output_dir:
            self._save_configuration_files(
                output_dir, claude_config, env_script, setup_instructions,
                detection_result, optimal_config
            )

        return GeneratedConfiguration(
            detection_result=detection_result,
            optimal_config=optimal_config,
            claude_config=claude_config,
            env_script=env_script,
            setup_instructions=setup_instructions,
            template_used=template
        )

    def _generate_claude_config(self, config: OptimalConfiguration, assistant_type: str) -> Dict[str, Any]:
        """Generate Claude Desktop configuration."""
        python_command = self._get_python_command()

        base_config = {
            "mcpServers": {
                "mdquery": {
                    "command": python_command,
                    "args": ["-m", "mdquery.mcp_server"],
                    "env": config.recommended_env_vars.copy()
                }
            }
        }

        # Add assistant-specific optimizations
        if assistant_type == "claude":
            base_config["mcpServers"]["mdquery"]["env"]["MDQUERY_ASSISTANT_TYPE"] = "claude"
            base_config["mcpServers"]["mdquery"]["env"]["MDQUERY_RESPONSE_FORMAT"] = "adaptive"
        elif assistant_type == "gpt":
            base_config["mcpServers"]["mdquery"]["env"]["MDQUERY_ASSISTANT_TYPE"] = "gpt"
            base_config["mcpServers"]["mdquery"]["env"]["MDQUERY_RESPONSE_FORMAT"] = "structured"

        # Add system-specific optimizations
        if config.system_type == NoteSystemType.OBSIDIAN:
            base_config["mcpServers"]["mdquery"]["env"]["MDQUERY_ENABLE_WIKILINKS"] = "true"
            base_config["mcpServers"]["mdquery"]["env"]["MDQUERY_ENABLE_NESTED_TAGS"] = "true"
        elif config.system_type == NoteSystemType.JEKYLL:
            base_config["mcpServers"]["mdquery"]["env"]["MDQUERY_EXCLUDE_PATTERNS"] = "_site,vendor,.bundle"
            base_config["mcpServers"]["mdquery"]["env"]["MDQUERY_ENABLE_LIQUID"] = "true"

        return base_config

    def _generate_env_script(self, config: OptimalConfiguration) -> str:
        """Generate environment setup script."""
        is_windows = platform.system() == "Windows"

        if is_windows:
            script_lines = ["@echo off", "REM mdquery environment setup script", ""]
            for key, value in config.recommended_env_vars.items():
                script_lines.append(f"set {key}={value}")
            script_lines.extend(["", "echo mdquery environment configured!", "pause"])
            return "\n".join(script_lines)
        else:
            script_lines = ["#!/bin/bash", "# mdquery environment setup script", ""]
            for key, value in config.recommended_env_vars.items():
                script_lines.append(f"export {key}={value}")
            script_lines.extend(["", "echo 'mdquery environment configured!'"])
            return "\n".join(script_lines)

    def _generate_setup_instructions(self, detection_result: SystemDetectionResult,
                                   config: OptimalConfiguration,
                                   template: ConfigurationTemplate) -> List[str]:
        """Generate step-by-step setup instructions."""
        instructions = [
            f"mdquery Setup Instructions for {detection_result.system_type.value.title()}",
            "=" * 60,
            "",
            f"System detected: {detection_result.system_type.value} (confidence: {detection_result.confidence:.1%})",
            f"Template: {template.name}",
            "",
            "DETECTION EVIDENCE:",
        ]

        for evidence in detection_result.evidence:
            instructions.append(f"  ✓ {evidence}")

        instructions.extend([
            "",
            "SETUP STEPS:",
            "",
            "1. Prerequisites:",
        ])

        for req in template.requirements:
            instructions.append(f"   • {req}")

        instructions.extend([
            "",
            "2. Install mdquery:",
            "   pip install mdquery",
            "",
            "3. Configure Claude Desktop:",
            "   • Copy the generated claude_desktop_config.json to your Claude config directory",
            f"   • Location: {self._get_claude_config_path()}",
            "",
            "4. Set Environment Variables:",
            "   • Run the generated setup script (setup_env.bat or setup_env.sh)",
            "   • Or manually set the following variables:",
        ])

        for key, value in config.recommended_env_vars.items():
            instructions.append(f"     {key}={value}")

        instructions.extend([
            "",
            "5. Restart Claude Desktop completely",
            "",
            "6. Test the integration:",
            '   Ask Claude: "Analyze my notes and show me the most common themes"',
            "",
            "RECOMMENDATIONS:",
        ])

        for rec in template.recommendations:
            instructions.append(f"  • {rec}")

        instructions.extend([
            "",
            "PERFORMANCE SETTINGS:",
            f"  • Mode: {config.performance_mode}",
            f"  • Indexing: {config.indexing_strategy}",
            f"  • Cache TTL: {config.optimization_settings.get('cache_ttl', 'default')} minutes",
            f"  • Concurrent Queries: {config.optimization_settings.get('concurrent_queries', 'default')}",
            "",
            "Need help? Check the troubleshooting guide or visit the documentation.",
        ])

        return instructions

    def _get_python_command(self) -> str:
        """Get the appropriate Python command for the system."""
        # Check if python3 is available
        if shutil.which("python3"):
            return "python3"
        elif shutil.which("python"):
            return "python"
        else:
            # Fallback to full path
            return "/usr/bin/python3" if platform.system() != "Windows" else "python"

    def _get_claude_config_path(self) -> str:
        """Get Claude Desktop configuration path for the current system."""
        system = platform.system()
        if system == "Darwin":  # macOS
            return "~/.claude/claude_desktop_config.json"
        elif system == "Windows":
            return "%APPDATA%/Claude/claude_desktop_config.json"
        else:  # Linux
            return "~/.config/claude/claude_desktop_config.json"

    def _save_configuration_files(self, output_dir: str,
                                 claude_config: Dict[str, Any],
                                 env_script: str,
                                 setup_instructions: List[str],
                                 detection_result: SystemDetectionResult,
                                 optimal_config: OptimalConfiguration) -> None:
        """Save all configuration files to output directory."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save Claude Desktop configuration
        claude_config_path = output_path / "claude_desktop_config.json"
        with open(claude_config_path, 'w') as f:
            json.dump(claude_config, f, indent=2)

        # Save environment setup script
        script_ext = ".bat" if platform.system() == "Windows" else ".sh"
        env_script_path = output_path / f"setup_env{script_ext}"
        with open(env_script_path, 'w') as f:
            f.write(env_script)

        # Make script executable on Unix systems
        if script_ext == ".sh":
            os.chmod(env_script_path, 0o755)

        # Save setup instructions
        instructions_path = output_path / "SETUP_INSTRUCTIONS.txt"
        with open(instructions_path, 'w') as f:
            f.write('\n'.join(setup_instructions))

        # Save detection report
        report_path = output_path / "detection_report.json"
        report_data = {
            "detection_result": {
                "system_type": detection_result.system_type.value,
                "confidence": detection_result.confidence,
                "evidence": detection_result.evidence,
                "config_files": detection_result.config_files,
                "special_directories": detection_result.special_directories,
                "file_patterns": detection_result.file_patterns
            },
            "optimal_configuration": {
                "system_type": optimal_config.system_type.value,
                "performance_mode": optimal_config.performance_mode,
                "indexing_strategy": optimal_config.indexing_strategy,
                "optimization_settings": optimal_config.optimization_settings,
                "cache_settings": optimal_config.cache_settings,
                "recommended_env_vars": optimal_config.recommended_env_vars
            }
        }

        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)

        logger.info(f"Configuration files saved to: {output_path}")

    def generate_quick_config(self, directory: str) -> str:
        """Generate a quick one-line configuration command."""
        detection_result = self.auto_config_manager.detect_note_system(directory)

        quick_config = {
            "mcpServers": {
                "mdquery": {
                    "command": "python",
                    "args": ["-m", "mdquery.mcp_server"],
                    "env": {"MDQUERY_NOTES_DIR": directory}
                }
            }
        }

        return json.dumps(quick_config, separators=(',', ':'))

    def optimize_existing_config(self, config_path: str, directory: str) -> Dict[str, Any]:
        """Optimize an existing configuration based on current best practices."""
        # Load existing configuration
        with open(config_path, 'r') as f:
            existing_config = json.load(f)

        # Detect current system
        detection_result = self.auto_config_manager.detect_note_system(directory)
        optimal_config = self.auto_config_manager.generate_optimal_configuration(detection_result, directory)

        # Merge with existing configuration
        if "mcpServers" in existing_config and "mdquery" in existing_config["mcpServers"]:
            # Update environment variables with optimizations
            if "env" not in existing_config["mcpServers"]["mdquery"]:
                existing_config["mcpServers"]["mdquery"]["env"] = {}

            # Add optimal settings while preserving user customizations
            for key, value in optimal_config.recommended_env_vars.items():
                if key not in existing_config["mcpServers"]["mdquery"]["env"]:
                    existing_config["mcpServers"]["mdquery"]["env"][key] = value

        return existing_config


def create_configuration_generator() -> AutomaticConfigurationGenerator:
    """Create a configuration generator instance."""
    return AutomaticConfigurationGenerator()