import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from './Button';

interface PageErrorBoundaryProps {
  title: string;
  description?: string;
  supportHint?: string;
  children: ReactNode;
  onReset?: () => void;
}

interface PageErrorBoundaryState {
  hasError: boolean;
  message: string;
}

export class PageErrorBoundary extends Component<PageErrorBoundaryProps, PageErrorBoundaryState> {
  override state: PageErrorBoundaryState = {
    hasError: false,
    message: '',
  };

  static getDerivedStateFromError(error: unknown): PageErrorBoundaryState {
    return {
      hasError: true,
      message: error instanceof Error ? error.message : String(error || ''),
    };
  }

  override componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error(`[${this.props.title}] page runtime error`, error, errorInfo);
  }

  private handleReset = () => {
    if (this.props.onReset) {
      this.props.onReset();
      return;
    }
    window.location.reload();
  };

  override render() {
    if (!this.state.hasError) {
      return this.props.children;
    }

    return (
      <div className="flex min-h-[60vh] items-center justify-center px-4 py-10">
        <section className="w-full max-w-2xl rounded-2xl border border-danger/30 bg-card/95 p-6 shadow-soft-card-strong">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-danger/30 bg-danger/10 text-danger">
              <AlertTriangle className="h-5 w-5" aria-hidden="true" />
            </div>
            <div className="min-w-0 flex-1 space-y-4">
              <div>
                <h1 className="text-lg font-semibold text-foreground">{this.props.title}加载失败</h1>
                <p className="mt-2 text-sm leading-6 text-secondary-text">
                  {this.props.description || '页面运行时发生异常，已阻止空白页继续扩散。'}
                </p>
              </div>

              {this.state.message ? (
                <pre className="max-h-32 overflow-auto rounded-xl border border-danger/20 bg-danger/5 px-3 py-2 text-xs leading-5 text-danger">
                  {this.state.message}
                </pre>
              ) : null}

              {this.props.supportHint ? (
                <p className="text-xs leading-6 text-muted-text">{this.props.supportHint}</p>
              ) : null}

              <Button type="button" variant="settings-secondary" onClick={this.handleReset}>
                <RefreshCw className="h-4 w-4" aria-hidden="true" />
                重新加载页面
              </Button>
            </div>
          </div>
        </section>
      </div>
    );
  }
}
