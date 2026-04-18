import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import {
  Alert,
  Button,
  Card,
  Chip,
  EmptyState,
  Heading,
  Icon,
  Link,
  Loader,
  SelectField,
  Text,
  TextAreaField,
  TextField,
} from './index';

describe('design-system primitives', () => {
  it('renders a loading button without losing its accessible label', async () => {
    const onClick = vi.fn();

    render(
      <Button isLoading onClick={onClick}>
        Salvar revisão
      </Button>,
    );

    const button = screen.getByRole('button', { name: 'Salvar revisão' });

    expect(button).toBeDisabled();
    expect(button).toHaveAttribute('aria-busy', 'true');
    expect(screen.getByText('Carregando')).toHaveClass('ds-sr-only');

    await userEvent.click(button);
    expect(onClick).not.toHaveBeenCalled();
  });

  it('associates form fields with labels, help text, and errors', () => {
    render(
      <>
        <TextField
          label="Email"
          name="email"
          type="email"
          helpText="Use seu email profissional."
          errorText="Informe um email válido."
        />
        <TextAreaField
          label="Observações"
          name="notes"
          helpText="Inclua apenas informações ditas na consulta."
        />
        <SelectField label="Plano" name="plan">
          <option value="plus">Plus</option>
        </SelectField>
      </>,
    );

    expect(screen.getByLabelText('Email')).toHaveAccessibleDescription(
      'Use seu email profissional. Informe um email válido.',
    );
    expect(screen.getByRole('alert')).toHaveTextContent('Informe um email válido.');
    expect(screen.getByLabelText('Observações')).toHaveAccessibleDescription(
      'Inclua apenas informações ditas na consulta.',
    );
    expect(screen.getByLabelText('Plano')).toBeInTheDocument();
  });

  it('renders chips, cards, typography, links, alerts, and empty states with stable variants', () => {
    render(
      <Card title="Resumo" eyebrow="Revisão" actions={<Button variant="ghost">Editar</Button>}>
        <Heading level={3}>Conteúdo draft</Heading>
        <Text tone="muted">Texto sujeito a revisão médica.</Text>
        <Chip tone="success">Finalizado</Chip>
        <Link href="/consultations">Ver consultas</Link>
        <Alert tone="warning" title="Revisão obrigatória">
          Confira os trechos de evidência antes de finalizar.
        </Alert>
        <EmptyState
          title="Nenhuma consulta"
          description="Crie uma consulta para iniciar a documentação."
          action={<Button>Nova consulta</Button>}
        />
      </Card>,
    );

    expect(screen.getByText('Revisão')).toHaveClass('ds-card-eyebrow');
    expect(screen.getByRole('heading', { name: 'Resumo', level: 2 })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Conteúdo draft', level: 3 })).toBeInTheDocument();
    expect(screen.getByText('Texto sujeito a revisão médica.')).toHaveClass('ds-text-muted');
    expect(screen.getByText('Finalizado')).toHaveClass('ds-chip-success');
    expect(screen.getByRole('link', { name: 'Ver consultas' })).toHaveClass('ds-link');
    expect(screen.getByRole('alert')).toHaveTextContent('Revisão obrigatória');
    expect(screen.getByRole('heading', { name: 'Nenhuma consulta', level: 2 })).toBeInTheDocument();
  });

  it('supports loader and icon accessibility defaults', () => {
    const { container } = render(
      <>
        <Loader label="Carregando consultas" />
        <Icon name="alert" />
        <Icon name="check" label="Consulta finalizada" />
      </>,
    );

    expect(screen.getByRole('status', { name: 'Carregando consultas' })).toBeInTheDocument();
    expect(container.querySelector('[data-icon-name="alert"]')).toHaveAttribute('aria-hidden', 'true');
    expect(screen.getByRole('img', { name: 'Consulta finalizada' })).toHaveAttribute(
      'data-icon-name',
      'check',
    );
  });
});
