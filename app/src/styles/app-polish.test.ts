import { describe, expect, it } from 'vitest';
import appCss from '../index.css?raw';

describe('authenticated app polish styles', () => {
  it('uses stable surfaces instead of decorative gradient backgrounds', () => {
    expect(appCss).not.toContain('radial-gradient');
    expect(appCss).not.toContain('linear-gradient');
  });

  it('does not include the removed login ambient layer styles', () => {
    expect(appCss).not.toContain('.login-ambient');
    expect(appCss).not.toContain('login-ambient-drift');
  });
});
