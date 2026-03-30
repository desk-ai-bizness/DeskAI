# Infrastructure

AWS CDK package for DeskAI MVP infrastructure.

## Scope

- Cognito authentication
- HTTP and WebSocket APIs
- Lambda compute
- DynamoDB and S3 storage
- Step Functions orchestration
- Monitoring, security, and budgets

Task 003 provides stack scaffolding only. Concrete resources are added in Task 004+.

## Local Commands

```bash
make install
make lint
make synth
```

`make install` prepares both Python dependencies and the local CDK CLI dependency.
