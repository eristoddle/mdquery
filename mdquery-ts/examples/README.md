# Examples

This directory contains examples showing how to use the MDQuery TypeScript library in different scenarios.

## Obsidian Plugin

The `obsidian-plugin/` directory contains a complete example of an Obsidian plugin that uses MDQuery for advanced vault analysis and querying.

### Features Demonstrated

- **Vault indexing** with progress tracking
- **Full-text search** with result highlighting
- **Statistics display** showing vault metrics
- **Broken link detection** for maintenance
- **Orphaned file discovery** for cleanup
- **Hub file analysis** for graph insights
- **Auto-indexing** on file changes
- **Settings management** for user preferences

### Installation

1. Copy the `obsidian-plugin` directory to your Obsidian vault's `.obsidian/plugins/` folder
2. Install dependencies: `npm install`
3. Build the plugin: `npm run build`
4. Enable the plugin in Obsidian's Community Plugins settings

### Usage

Once installed, the plugin adds:

- **Ribbon icon**: Click the search icon for MDQuery search
- **Commands**: Access via Command Palette (Ctrl/Cmd + P)
  - "Search with MDQuery"
  - "Index vault with MDQuery"
  - "Show vault statistics"
  - "Find orphaned files"
  - "Find broken links"
  - "Show hub files"
- **Settings tab**: Configure auto-indexing and notifications

## Other Examples

More examples will be added for:

- **Node.js CLI tool** for markdown analysis
- **Web application** using browser File System Access API
- **Jekyll integration** for static site analysis
- **Custom parser** for domain-specific markdown

## Running Examples

Each example includes its own README with specific instructions for setup and usage.