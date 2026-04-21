import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { ReviewPage } from './ReviewPage';

describe('ReviewPage', () => {
  it('redirects legacy review route back to the unified live workspace', async () => {
    render(
      <MemoryRouter initialEntries={['/consultations/cons-1/review']}>
        <Routes>
          <Route path="/consultations/:consultationId/review" element={<ReviewPage />} />
          <Route path="/consultations/:consultationId/live" element={<div>Workspace unificado</div>} />
        </Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByText('Workspace unificado')).toBeInTheDocument();
  });
});
