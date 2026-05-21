import { ChangeDetectorRef, Component } from '@angular/core';
import { NgIf } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

type FileName = 'system.md' | 'instructions.md' | 'examples.json';

interface CommandResult {
  code: number;
  stdout: string;
  stderr: string;
}

type MenuKey = 'menu1' | 'menu2' | 'menu3';

interface UiConfig {
  llm: {
    url: string;
    model: string;
    tokenConfigured: boolean;
    insecureSkipTlsVerify: boolean;
    temperature: number;
  };
  mcp: {
    command: string;
    args: string[];
    tools: {
      fetchTickets: string;
      updateTicket: string;
    };
  };
  jira: {
    project: string;
    query: string;
    fetchLimit: number;
  };
  actionsDir: string;
  auditLogFile: string;
  scheduleIntervalMs: number;
  logLevel: string;
}

@Component({
  selector: 'app-root',
  imports: [FormsModule, NgIf],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  menu1Tab: 'output' | 'audit' = 'output';
  menu2Tab: 'output' | 'audit' | 'exec' = 'output';
  activeMenu: MenuKey = 'menu1';

  actions: string[] = [];
  selectedAction = '';
  configView = '';
  config: UiConfig | null = null;
  mcpToolsJson = '';

  selectedFile: FileName = 'system.md';
  fileOrder: FileName[] = ['system.md', 'instructions.md', 'examples.json'];
  fileMap: Record<FileName, string> = {
    'system.md': '',
    'instructions.md': '',
    'examples.json': '[]\n'
  };
  fileDraft = '';

  commandOutput = '';
  schedulerLog = '';
  auditLog = '';

  newActionName = '';
  newSystem = 'You are an expert Jira assistant. Keep responses concise and actionable.';
  newInstructions = 'Analyze tickets and propose score updates as JSON array output.';

  busy = false;
  statusMessage = 'Idle';
  statusType: 'neutral' | 'running' | 'success' | 'error' = 'neutral';

  constructor(
    private readonly http: HttpClient,
    private readonly cdr: ChangeDetectorRef
  ) {}

  async ngOnInit(): Promise<void> {
    try {
      await this.refreshActions();
      await this.loadConfig();
      await this.refreshLogs();
      this.setStatus('Idle', 'neutral');
      this.cdr.detectChanges();
      setInterval(() => {
        this.refreshLogs()
          .then(() => this.cdr.detectChanges())
          .catch(() => undefined);
      }, 6000);
    } catch (error) {
      this.handleError(error);
      this.cdr.detectChanges();
    }
  }

  private async api<T>(url: string, method: 'GET' | 'POST' | 'PUT' = 'GET', body?: unknown): Promise<T> {
    if (method === 'GET') {
      return firstValueFrom(this.http.get<T>(url));
    }

    if (method === 'POST') {
      return firstValueFrom(this.http.post<T>(url, body || {}));
    }

    return firstValueFrom(this.http.put<T>(url, body || {}));
  }

  private setStatus(message: string, type: 'neutral' | 'running' | 'success' | 'error'): void {
    this.statusMessage = message;
    this.statusType = type;
  }

  private handleError(error: unknown): void {
    const message =
      typeof error === 'object' && error !== null && 'error' in error
        ? String((error as { error?: { error?: string } }).error?.error || 'Request failed')
        : error instanceof Error
          ? error.message
          : 'Request failed';
    this.commandOutput = `Error: ${message}`;
    this.setStatus(message, 'error');
  }

  private formatResult(result: CommandResult): void {
    this.commandOutput = [
      `exitCode: ${result.code}`,
      '',
      'STDOUT:',
      result.stdout || '(none)',
      '',
      'STDERR:',
      result.stderr || '(none)'
    ].join('\n');
  }

  async withBusy(action: () => Promise<void>): Promise<void> {
    try {
      this.busy = true;
      this.setStatus('Running...', 'running');
      await action();
      this.setStatus('Completed', 'success');
    } catch (error) {
      this.handleError(error);
    } finally {
      this.busy = false;
      await this.refreshLogs();
      this.cdr.detectChanges();
    }
  }

  async refreshActions(): Promise<void> {
    const payload = await this.api<{ actions: string[] }>('/api/actions');
    this.actions = payload.actions || [];
    if (!this.selectedAction || !this.actions.includes(this.selectedAction)) {
      this.selectedAction = this.actions[0] || '';
    }
    if (this.selectedAction) {
      await this.loadActionFiles();
    }
  }

  setActiveMenu(menu: MenuKey): void {
    this.activeMenu = menu;
  }

  async loadConfig(): Promise<void> {
    const payload = await this.api<UiConfig>('/api/config');
    this.configView = JSON.stringify(payload, null, 2);
    this.config = payload;
    this.mcpToolsJson = payload?.mcp?.tools ? JSON.stringify(payload.mcp.tools, null, 2) : '';
  }

  async saveConfig(): Promise<void> {
    if (!this.config) return;
    try {
      this.busy = true;
      // Parse MCP tools JSON
      try {
        this.config.mcp.tools = JSON.parse(this.mcpToolsJson);
      } catch (e) {
        alert('Invalid MCP tools JSON');
        return;
      }
      await this.api('/api/config', 'PUT', this.config);
      await this.loadConfig();
      this.setStatus('Config saved', 'success');
    } catch (e) {
      this.handleError(e);
    } finally {
      this.busy = false;
      this.cdr.detectChanges();
    }
  }

  async loadActionFiles(): Promise<void> {
    if (!this.selectedAction) {
      return;
    }
    const payload = await this.api<{ files: Record<FileName, string> }>(`/api/actions/${encodeURIComponent(this.selectedAction)}`);
    this.fileMap = payload.files || this.fileMap;
    this.fileDraft = this.fileMap[this.selectedFile] || '';
  }

  selectFile(fileName: FileName): void {
    this.fileMap[this.selectedFile] = this.fileDraft;
    this.selectedFile = fileName;
    this.fileDraft = this.fileMap[fileName] || '';
  }

  async saveFile(): Promise<void> {
    await this.withBusy(async () => {
      if (!this.selectedAction) {
        throw new Error('Select an action first');
      }
      this.fileMap[this.selectedFile] = this.fileDraft;
      await this.api(
        `/api/actions/${encodeURIComponent(this.selectedAction)}/files/${encodeURIComponent(this.selectedFile)}`,
        'PUT',
        { content: this.fileDraft }
      );
      this.setStatus(`${this.selectedFile} saved`, 'success');
    });
  }

  async createAction(): Promise<void> {
    await this.withBusy(async () => {
      const action = this.newActionName.trim();
      if (!action) {
        throw new Error('Action name is required');
      }
      await this.api('/api/actions', 'POST', {
        action,
        system: this.newSystem,
        instructions: this.newInstructions
      });
      this.newActionName = '';
      await this.refreshActions();
      this.selectedAction = action;
      await this.loadActionFiles();
    });
  }

  async runTest(type: 'test-llm' | 'test-mcp'): Promise<void> {
    await this.withBusy(async () => {
      const endpoint = type === 'test-mcp' ? '/api/run/test-mcp' : '/api/run/test-llm';
      const result = await this.api<CommandResult>(endpoint, 'POST');
      this.formatResult(result);
    });
  }

  async runAction(mode: 'dry-run' | 'execute'): Promise<void> {
    await this.withBusy(async () => {
      if (!this.selectedAction) {
        throw new Error('Select an action first');
      }
      const result = await this.api<CommandResult>('/api/run/action', 'POST', {
        action: this.selectedAction,
        mode
      });
      this.formatResult(result);
    });
  }

  async refreshLogs(): Promise<void> {
    const scheduler = await this.api<{ lines: string[] }>('/api/logs/scheduler');
    this.schedulerLog = (scheduler.lines || []).join('\n');

    const audit = await this.api<{ lines: string[] }>('/api/logs/audit');
    this.auditLog = (audit.lines || []).join('\n');
  }
}
