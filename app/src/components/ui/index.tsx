import {
  AlertTriangle,
  CheckCircle,
  Info,
  LoaderCircle,
  Search,
  XCircle,
} from 'lucide-react';
import type {
  AnchorHTMLAttributes,
  ButtonHTMLAttributes,
  HTMLAttributes,
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
  TextareaHTMLAttributes,
} from 'react';
import { useId } from 'react';

function classNames(...values: Array<string | false | null | undefined>): string {
  return values.filter(Boolean).join(' ');
}

type IconName = 'alert' | 'check' | 'info' | 'loader' | 'search' | 'x';

const icons = {
  alert: AlertTriangle,
  check: CheckCircle,
  info: Info,
  loader: LoaderCircle,
  search: Search,
  x: XCircle,
};

interface IconProps extends HTMLAttributes<SVGSVGElement> {
  name: IconName;
  label?: string;
  size?: number;
}

export function Icon({ name, label, size = 18, className, ...props }: IconProps) {
  const Component = icons[name];

  return (
    <Component
      {...props}
      aria-hidden={label ? undefined : true}
      aria-label={label}
      className={classNames('ds-icon', className)}
      data-icon-name={name}
      focusable="false"
      role={label ? 'img' : undefined}
      size={size}
    />
  );
}

interface LoaderProps extends HTMLAttributes<HTMLDivElement> {
  label?: string;
  size?: 'sm' | 'md';
}

export function Loader({ label = 'Carregando', size = 'md', className, ...props }: LoaderProps) {
  return (
    <div
      {...props}
      aria-label={label}
      className={classNames('ds-loader', `ds-loader-${size}`, className)}
      role="status"
    >
      <Icon name="loader" className="ds-loader-icon" />
      <span>{label}</span>
    </div>
  );
}

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  isLoading?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
}

export function Button({
  children,
  className,
  disabled,
  isLoading = false,
  leftIcon,
  rightIcon,
  type = 'button',
  variant = 'primary',
  ...props
}: ButtonProps) {
  const isDisabled = disabled || isLoading;

  return (
    <button
      {...props}
      aria-busy={isLoading ? 'true' : undefined}
      className={classNames('ds-button', `ds-button-${variant}`, className)}
      disabled={isDisabled}
      type={type}
    >
      {isLoading ? (
        <>
          <Icon name="loader" className="ds-button-loader" />
          <span aria-hidden="true" className="ds-sr-only">
            Carregando
          </span>
        </>
      ) : null}
      {leftIcon ? <span className="ds-button-icon">{leftIcon}</span> : null}
      <span className="ds-button-content">{children}</span>
      {rightIcon ? <span className="ds-button-icon">{rightIcon}</span> : null}
    </button>
  );
}

interface TextProps extends HTMLAttributes<HTMLParagraphElement> {
  tone?: 'default' | 'muted' | 'danger' | 'success' | 'warning';
}

export function Text({ className, tone = 'default', ...props }: TextProps) {
  return <p {...props} className={classNames('ds-text', `ds-text-${tone}`, className)} />;
}

interface HeadingProps extends HTMLAttributes<HTMLHeadingElement> {
  level?: 1 | 2 | 3 | 4;
}

export function Heading({ className, level = 2, ...props }: HeadingProps) {
  const Component = `h${level}` as const;

  return <Component {...props} className={classNames('ds-heading', `ds-heading-${level}`, className)} />;
}

export function Link({ className, ...props }: AnchorHTMLAttributes<HTMLAnchorElement>) {
  return <a {...props} className={classNames('ds-link', className)} />;
}

interface ChipBaseProps {
  children: ReactNode;
  className?: string;
  selected?: boolean;
  tone?: 'neutral' | 'info' | 'success' | 'warning' | 'danger';
}

type ChipProps = ChipBaseProps &
  (
    | ({ onClick?: undefined } & HTMLAttributes<HTMLSpanElement>)
    | ({ onClick: ButtonHTMLAttributes<HTMLButtonElement>['onClick'] } & ButtonHTMLAttributes<HTMLButtonElement>)
  );

export function Chip({ children, className, selected = false, tone = 'neutral', ...props }: ChipProps) {
  const chipClassName = classNames(
    'ds-chip',
    `ds-chip-${tone}`,
    selected && 'ds-chip-selected',
    className,
  );

  if ('onClick' in props && props.onClick) {
    return (
      <button
        {...props}
        aria-pressed={selected}
        className={chipClassName}
        type={props.type ?? 'button'}
      >
        {children}
      </button>
    );
  }

  return (
    <span {...(props as HTMLAttributes<HTMLSpanElement>)} className={chipClassName}>
      {children}
    </span>
  );
}

interface CardProps extends HTMLAttributes<HTMLElement> {
  actions?: ReactNode;
  children: ReactNode;
  eyebrow?: string;
  title?: string;
}

export function Card({ actions, children, className, eyebrow, title, ...props }: CardProps) {
  return (
    <section {...props} className={classNames('ds-card', className)}>
      {eyebrow || title || actions ? (
        <div className="ds-card-header">
          <div>
            {eyebrow ? <p className="ds-card-eyebrow">{eyebrow}</p> : null}
            {title ? <Heading level={2}>{title}</Heading> : null}
          </div>
          {actions ? <div className="ds-card-actions">{actions}</div> : null}
        </div>
      ) : null}
      <div className="ds-card-body">{children}</div>
    </section>
  );
}

interface FieldShellProps {
  children: ReactNode;
  errorId?: string;
  errorText?: string;
  helpId?: string;
  helpText?: string;
  id: string;
  label: string;
}

function FieldShell({
  children,
  errorId,
  errorText,
  helpId,
  helpText,
  id,
  label,
}: FieldShellProps) {
  return (
    <div className="ds-field">
      <label className="ds-field-label" htmlFor={id}>
        {label}
      </label>
      {children}
      {helpText ? (
        <p className="ds-field-help" id={helpId}>
          {helpText}
        </p>
      ) : null}
      {errorText ? (
        <p className="ds-field-error" id={errorId} role="alert">
          {errorText}
        </p>
      ) : null}
    </div>
  );
}

function useFieldIds(idProp: string | undefined, helpText?: string, errorText?: string) {
  const generatedId = useId();
  const id = idProp ?? generatedId;
  const helpId = helpText ? `${id}-help` : undefined;
  const errorId = errorText ? `${id}-error` : undefined;
  const describedBy = [helpId, errorId].filter(Boolean).join(' ') || undefined;

  return {
    describedBy,
    errorId,
    helpId,
    id,
  };
}

interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  errorText?: string;
  helpText?: string;
  label: string;
}

export function TextField({ className, errorText, helpText, id: idProp, label, ...props }: TextFieldProps) {
  const { describedBy, errorId, helpId, id } = useFieldIds(idProp, helpText, errorText);

  return (
    <FieldShell errorId={errorId} errorText={errorText} helpId={helpId} helpText={helpText} id={id} label={label}>
      <input
        {...props}
        aria-describedby={describedBy}
        aria-invalid={errorText ? true : undefined}
        className={classNames('ds-input', className)}
        id={id}
      />
    </FieldShell>
  );
}

interface TextAreaFieldProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  errorText?: string;
  helpText?: string;
  label: string;
}

export function TextAreaField({
  className,
  errorText,
  helpText,
  id: idProp,
  label,
  ...props
}: TextAreaFieldProps) {
  const { describedBy, errorId, helpId, id } = useFieldIds(idProp, helpText, errorText);

  return (
    <FieldShell errorId={errorId} errorText={errorText} helpId={helpId} helpText={helpText} id={id} label={label}>
      <textarea
        {...props}
        aria-describedby={describedBy}
        aria-invalid={errorText ? true : undefined}
        className={classNames('ds-input ds-textarea', className)}
        id={id}
      />
    </FieldShell>
  );
}

interface SelectFieldProps extends SelectHTMLAttributes<HTMLSelectElement> {
  errorText?: string;
  helpText?: string;
  label: string;
}

export function SelectField({
  children,
  className,
  errorText,
  helpText,
  id: idProp,
  label,
  ...props
}: SelectFieldProps) {
  const { describedBy, errorId, helpId, id } = useFieldIds(idProp, helpText, errorText);

  return (
    <FieldShell errorId={errorId} errorText={errorText} helpId={helpId} helpText={helpText} id={id} label={label}>
      <select
        {...props}
        aria-describedby={describedBy}
        aria-invalid={errorText ? true : undefined}
        className={classNames('ds-input ds-select', className)}
        id={id}
      >
        {children}
      </select>
    </FieldShell>
  );
}

interface AlertProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  title?: string;
  tone?: 'info' | 'success' | 'warning' | 'danger';
}

export function Alert({ children, className, title, tone = 'info', ...props }: AlertProps) {
  const iconName: IconName = tone === 'success' ? 'check' : tone === 'danger' ? 'x' : tone === 'warning' ? 'alert' : 'info';
  const role = tone === 'warning' || tone === 'danger' ? 'alert' : 'status';

  return (
    <div {...props} className={classNames('ds-alert', `ds-alert-${tone}`, className)} role={role}>
      <Icon name={iconName} className="ds-alert-icon" />
      <div>
        {title ? <p className="ds-alert-title">{title}</p> : null}
        <div className="ds-alert-content">{children}</div>
      </div>
    </div>
  );
}

interface EmptyStateProps extends HTMLAttributes<HTMLDivElement> {
  action?: ReactNode;
  description?: string;
  title: string;
}

export function EmptyState({ action, className, description, title, ...props }: EmptyStateProps) {
  return (
    <div {...props} className={classNames('ds-empty-state', className)}>
      <div className="ds-empty-state-icon" aria-hidden="true">
        <Icon name="search" />
      </div>
      <Heading level={2}>{title}</Heading>
      {description ? <Text tone="muted">{description}</Text> : null}
      {action ? <div className="ds-empty-state-action">{action}</div> : null}
    </div>
  );
}
