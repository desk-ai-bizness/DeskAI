interface BrandLogoProps {
  iconTestId?: string;
  size?: 'compact' | 'default';
}

export function BrandLogo({ iconTestId, size = 'default' }: BrandLogoProps) {
  const className = size === 'compact' ? 'brand-logo brand-logo-compact' : 'brand-logo';

  return (
    <span className={className}>
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
