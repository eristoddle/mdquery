import { Plugin, TFile, Notice, Modal, App, Setting } from 'obsidian';
import { ObsidianPluginHelper, ObsidianPluginContext } from 'mdquery-ts/obsidian';

interface MDQueryPluginSettings {
  autoIndex: boolean;
  showNotifications: boolean;
  indexOnStartup: boolean;
}

const DEFAULT_SETTINGS: MDQueryPluginSettings = {
  autoIndex: true,
  showNotifications: true,
  indexOnStartup: true
};

export default class MDQueryDemoPlugin extends Plugin {
  settings: MDQueryPluginSettings;
  helper: ObsidianPluginHelper;

  async onload() {
    await this.loadSettings();

    // Initialize MDQuery helper
    const context: ObsidianPluginContext = {
      app: this.app,
      vault: this.app.vault,
      workspace: this.app.workspace
    };

    this.helper = new ObsidianPluginHelper(context);
    
    try {
      await this.helper.init();
      
      if (this.settings.showNotifications) {
        new Notice('MDQuery initialized successfully');
      }

      // Index vault on startup if enabled
      if (this.settings.indexOnStartup) {
        this.indexVault();
      }

      // Setup auto-indexing
      if (this.settings.autoIndex) {
        this.helper.setupAutoIndexing();
      }
    } catch (error) {
      new Notice(`MDQuery initialization failed: ${error.message}`);
      console.error('MDQuery initialization error:', error);
    }

    // Add ribbon icon
    this.addRibbonIcon('search', 'MDQuery Search', () => {
      this.openSearchModal();
    });

    // Add commands
    this.addCommand({
      id: 'mdquery-search',
      name: 'Search with MDQuery',
      callback: () => this.openSearchModal()
    });

    this.addCommand({
      id: 'mdquery-index-vault',
      name: 'Index vault with MDQuery',
      callback: () => this.indexVault()
    });

    this.addCommand({
      id: 'mdquery-show-stats',
      name: 'Show vault statistics',
      callback: () => this.showVaultStats()
    });

    this.addCommand({
      id: 'mdquery-find-orphans',
      name: 'Find orphaned files',
      callback: () => this.findOrphanedFiles()
    });

    this.addCommand({
      id: 'mdquery-find-broken-links',
      name: 'Find broken links',
      callback: () => this.findBrokenLinks()
    });

    this.addCommand({
      id: 'mdquery-show-hubs',
      name: 'Show hub files',
      callback: () => this.showHubFiles()
    });

    // Add settings tab
    this.addSettingTab(new MDQuerySettingTab(this.app, this));
  }

  async onunload() {
    if (this.helper) {
      await this.helper.cleanup();
    }
  }

  async loadSettings() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
  }

  async saveSettings() {
    await this.saveData(this.settings);
  }

  private async indexVault() {
    try {
      new Notice('Starting vault indexing...');
      
      await this.helper.indexVault({
        showProgress: true,
        onProgress: (processed, total, file) => {
          if (processed % 10 === 0) { // Update every 10 files
            new Notice(`Indexing: ${processed}/${total} files`, 1000);
          }
        }
      });

      new Notice('Vault indexing completed!');
    } catch (error) {
      new Notice(`Indexing failed: ${error.message}`);
      console.error('Indexing error:', error);
    }
  }

  private openSearchModal() {
    new MDQuerySearchModal(this.app, this.helper).open();
  }

  private async showVaultStats() {
    try {
      const stats = await this.helper.getVaultStats();
      
      const message = `
**Vault Statistics**

📁 Total Files: ${stats.totalFiles}
🏷️ Total Tags: ${stats.totalTags}
🔗 Total Links: ${stats.totalLinks}
📊 Average File Size: ${Math.round(stats.avgFileSize)} bytes
📝 Average Word Count: ${Math.round(stats.avgWordCount)} words
📅 Last Modified: ${stats.lastModified?.toLocaleDateString() || 'Unknown'}
      `.trim();

      new Notice(message, 10000);
    } catch (error) {
      new Notice(`Failed to get stats: ${error.message}`);
    }
  }

  private async findOrphanedFiles() {
    try {
      const orphans = await this.helper.getOrphanedFiles();
      
      if (orphans.length === 0) {
        new Notice('No orphaned files found!');
        return;
      }

      const message = `Found ${orphans.length} orphaned files:\\n${orphans.map(f => f.name).join('\\n')}`;
      new Notice(message, 15000);
    } catch (error) {
      new Notice(`Failed to find orphans: ${error.message}`);
    }
  }

  private async findBrokenLinks() {
    try {
      const brokenLinks = await this.helper.getBrokenLinks();
      
      if (brokenLinks.length === 0) {
        new Notice('No broken links found!');
        return;
      }

      const message = `Found ${brokenLinks.length} broken links:\\n${brokenLinks.map(l => `${l.target} in ${l.sourcePath}`).slice(0, 10).join('\\n')}`;
      new Notice(message, 15000);
    } catch (error) {
      new Notice(`Failed to find broken links: ${error.message}`);
    }
  }

  private async showHubFiles() {
    try {
      const hubs = await this.helper.getHubFiles(5);
      
      if (hubs.length === 0) {
        new Notice('No hub files found!');
        return;
      }

      const message = `**Top Hub Files:**\\n${hubs.map(h => `${h.name} (${h.linkCount} links)`).join('\\n')}`;
      new Notice(message, 10000);
    } catch (error) {
      new Notice(`Failed to find hubs: ${error.message}`);
    }
  }
}

class MDQuerySearchModal extends Modal {
  constructor(app: App, private helper: ObsidianPluginHelper) {
    super(app);
  }

  onOpen() {
    const { contentEl } = this;
    contentEl.createEl('h2', { text: 'MDQuery Search' });

    const inputEl = contentEl.createEl('input', {
      type: 'text',
      placeholder: 'Enter search query...'
    });
    inputEl.style.width = '100%';
    inputEl.style.marginBottom = '10px';

    const resultsEl = contentEl.createEl('div');
    resultsEl.style.maxHeight = '400px';
    resultsEl.style.overflowY = 'auto';

    const searchBtn = contentEl.createEl('button', { text: 'Search' });
    searchBtn.onclick = async () => {
      const query = inputEl.value.trim();
      if (!query) return;

      try {
        resultsEl.empty();
        resultsEl.createEl('p', { text: 'Searching...' });

        const results = await this.helper.search(query);
        resultsEl.empty();

        if (results.length === 0) {
          resultsEl.createEl('p', { text: 'No results found' });
          return;
        }

        resultsEl.createEl('h3', { text: `Found ${results.length} results:` });

        for (const result of results.slice(0, 20)) {
          const resultEl = resultsEl.createEl('div');
          resultEl.style.marginBottom = '10px';
          resultEl.style.padding = '10px';
          resultEl.style.border = '1px solid var(--background-modifier-border)';
          resultEl.style.borderRadius = '5px';

          const titleEl = resultEl.createEl('h4', { text: result.name });
          titleEl.style.margin = '0 0 5px 0';
          titleEl.style.cursor = 'pointer';
          titleEl.onclick = () => {
            this.app.workspace.openLinkText(result.path, '');
            this.close();
          };

          if (result.snippet) {
            const snippetEl = resultEl.createEl('p');
            snippetEl.innerHTML = result.snippet;
            snippetEl.style.margin = '0';
            snippetEl.style.fontSize = '0.9em';
            snippetEl.style.color = 'var(--text-muted)';
          }

          resultEl.createEl('small', { 
            text: result.path,
            cls: 'text-muted'
          });
        }
      } catch (error) {
        resultsEl.empty();
        resultsEl.createEl('p', { 
          text: `Search failed: ${error.message}`,
          cls: 'text-error'
        });
      }
    };

    // Search on Enter
    inputEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        searchBtn.click();
      }
    });

    inputEl.focus();
  }

  onClose() {
    const { contentEl } = this;
    contentEl.empty();
  }
}

class MDQuerySettingTab extends PluginSettingTab {
  plugin: MDQueryDemoPlugin;

  constructor(app: App, plugin: MDQueryDemoPlugin) {
    super(app, plugin);
    this.plugin = plugin;
  }

  display(): void {
    const { containerEl } = this;
    containerEl.empty();

    containerEl.createEl('h2', { text: 'MDQuery Settings' });

    new Setting(containerEl)
      .setName('Auto-index files')
      .setDesc('Automatically index files when they are created, modified, or deleted')
      .addToggle(toggle => toggle
        .setValue(this.plugin.settings.autoIndex)
        .onChange(async (value) => {
          this.plugin.settings.autoIndex = value;
          await this.plugin.saveSettings();
          
          if (value) {
            this.plugin.helper.setupAutoIndexing();
          }
        }));

    new Setting(containerEl)
      .setName('Show notifications')
      .setDesc('Show notifications for indexing and other operations')
      .addToggle(toggle => toggle
        .setValue(this.plugin.settings.showNotifications)
        .onChange(async (value) => {
          this.plugin.settings.showNotifications = value;
          await this.plugin.saveSettings();
        }));

    new Setting(containerEl)
      .setName('Index on startup')
      .setDesc('Automatically index the vault when Obsidian starts')
      .addToggle(toggle => toggle
        .setValue(this.plugin.settings.indexOnStartup)
        .onChange(async (value) => {
          this.plugin.settings.indexOnStartup = value;
          await this.plugin.saveSettings();
        }));

    new Setting(containerEl)
      .setName('Manual Actions')
      .setHeading();

    new Setting(containerEl)
      .setName('Index Vault')
      .setDesc('Manually trigger a full vault indexing')
      .addButton(button => button
        .setButtonText('Index Now')
        .onClick(async () => {
          await this.plugin.indexVault();
        }));

    new Setting(containerEl)
      .setName('Show Statistics')
      .setDesc('Display vault statistics')
      .addButton(button => button
        .setButtonText('Show Stats')
        .onClick(async () => {
          await this.plugin.showVaultStats();
        }));
  }
}