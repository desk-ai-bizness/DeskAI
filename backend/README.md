# Backend

Python backend for DeskAI MVP using a hexagonal architecture.

## Structure

- `src/deskai/domain`: pure domain entities, value objects, services, rules
- `src/deskai/application`: use cases and orchestration
- `src/deskai/ports`: abstract interfaces for repositories and providers
- `src/deskai/adapters`: concrete infrastructure implementations
- `src/deskai/handlers`: inbound Lambda entrypoints
- `src/deskai/bff`: frontend-facing view model assembly
- `src/deskai/shared`: cross-cutting utilities

## Local Commands

```bash
make install
make lint
make test
```

## Security Notes

- Do not log raw medical transcript content.
- Do not log CPF or direct PII.
- Log only diagnostic metadata needed for troubleshooting.
