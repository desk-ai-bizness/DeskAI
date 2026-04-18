interface BrandLogoProps {
  iconTestId?: string;
  size?: 'compact' | 'default';
  tone?: 'default' | 'light';
}

export function BrandLogo({ iconTestId, size = 'default', tone = 'default' }: BrandLogoProps) {
  const classNames = ['brand-logo'];

  if (size === 'compact') {
    classNames.push('brand-logo-compact');
  }

  if (tone === 'light') {
    classNames.push('brand-logo-light');
  }

  return (
    <span className={classNames.join(' ')}>
      <img
        src="/logo-icon.png"
        alt=""
        aria-hidden="true"
        className="brand-logo-icon"
        data-testid={iconTestId}
        width="36"
        height="36"
      />
      <img
        src="/logo-text.png"
        alt="Notter"
        className="brand-logo-text"
        width="118"
        height="32"
      />
    </span>
  );
}
