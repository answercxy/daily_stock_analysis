import { render, screen, fireEvent } from '@testing-library/react';
import type { ReactElement } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { PageErrorBoundary } from '../PageErrorBoundary';

function BrokenPage(): ReactElement {
  throw new Error('settings panel crashed');
}

describe('PageErrorBoundary', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders children when no runtime error occurs', () => {
    render(
      <PageErrorBoundary title="系统设置">
        <div>设置内容</div>
      </PageErrorBoundary>,
    );

    expect(screen.getByText('设置内容')).toBeInTheDocument();
  });

  it('shows a diagnostic fallback instead of a blank page', () => {
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
    const onReset = vi.fn();

    render(
      <PageErrorBoundary
        title="系统设置"
        supportHint="请附上 logs/desktop.log。"
        onReset={onReset}
      >
        <BrokenPage />
      </PageErrorBoundary>,
    );

    expect(screen.getByText('系统设置加载失败')).toBeInTheDocument();
    expect(screen.getByText('settings panel crashed')).toBeInTheDocument();
    expect(screen.getByText('请附上 logs/desktop.log。')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: '重新加载页面' }));

    expect(onReset).toHaveBeenCalledTimes(1);
  });
});
