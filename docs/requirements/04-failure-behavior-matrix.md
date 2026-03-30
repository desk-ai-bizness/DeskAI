# Failure Behavior Matrix

## Purpose

This document defines expected system behavior when critical operations fail. Every failure path has a defined detection mechanism, user-visible behavior, recovery path, and data impact.

This ensures consistent handling across backend, BFF, and frontend without ad-hoc decisions during implementation.

---

## 1. Authentication Failures

| Failure | Detection | User Experience | Backend Behavior | Recovery | Data Impact |
|---------|-----------|----------------|-----------------|----------|-------------|
| Invalid credentials | Cognito returns `NotAuthorizedException` | "Email ou senha incorretos." | Log failed attempt (no PII in log) | User retries login | None |
| Account not verified | Cognito returns `UserNotConfirmedException` | "Verifique seu email antes de continuar." | Redirect to verification flow | User checks email for verification link | None |
| Account disabled | Cognito returns `UserDisabledException` | "Sua conta foi desativada. Entre em contato com o suporte." | Log event, return 403 | Contact support | None |
| Token expired | JWT validation fails | Silent redirect to login | BFF returns 401, frontend clears session | User logs in again | No data loss; in-progress edits in frontend may be lost |
| Cognito service outage | Connection timeout or 5xx from Cognito | "Servico temporariamente indisponivel. Tente novamente." | Return 503, log error with correlation ID | Automatic retry with backoff (max 3 attempts) | None |

---

## 2. Consultation Creation Failures

| Failure | Detection | User Experience | Backend Behavior | Recovery | Data Impact |
|---------|-----------|----------------|-----------------|----------|-------------|
| Plan limit exceeded | Backend count check | "Voce atingiu o limite de consultas do seu plano este mes." | Return 403 with `plan_limit_exceeded` | Upgrade plan or wait for next month | None |
| Trial expired | Backend date check | "Seu periodo de teste expirou." | Return 403 with `trial_expired` | Upgrade plan | None |
| Missing required fields | Pydantic validation | Field-level validation errors in form | Return 400 with field-specific errors | User corrects fields | None |
| Patient not found | DynamoDB lookup fails | "Paciente nao encontrado." | Return 404 | User creates patient first or corrects ID | None |
| DynamoDB write failure | boto3 exception | "Erro ao criar consulta. Tente novamente." | Return 500, log error with full context | User retries | None (write never committed) |

---

## 3. Real-Time Session Failures

| Failure | Detection | User Experience | Backend Behavior | Recovery | Data Impact |
|---------|-----------|----------------|-----------------|----------|-------------|
| WebSocket connection failure | `$connect` handler fails | "Nao foi possivel iniciar a sessao. Verifique sua conexao." | Log connection failure | User retries connection | None |
| WebSocket disconnect during recording | `$disconnect` event | "Conexao perdida. Reconectando..." | Preserve audio received so far; start grace period (5 min) | Auto-reconnect attempt by frontend; if successful, session resumes | Audio before disconnect preserved |
| Grace period expired | Timer expires without reconnect | "Sessao encerrada por desconexao. Processando audio disponivel." | Auto-end session, proceed to processing with available audio | Physician reviews partial results | Partial audio processed; artifacts may be incomplete |
| Audio chunk rejected | Lambda handler validation | Silent retry (frontend sends again) | Log malformed chunk, return error frame | Frontend retries chunk delivery | Single chunk lost if retry fails |
| Session start when already recording | Duplicate `session/start` | No visible change (idempotent) | Return existing session details | N/A | None |
| Session start for wrong consultation state | State guard check | "Esta consulta nao pode ser iniciada." | Return 409 with error code | User checks consultation status | None |

---

## 4. Transcription Provider Failures

| Failure | Detection | User Experience | Backend Behavior | Recovery | Data Impact |
|---------|-----------|----------------|-----------------|----------|-------------|
| Provider connection failure | Adapter timeout or connection error | Session pauses; "Conectando ao servico de transcricao..." | Retry connection with backoff (max 3 attempts) | Auto-retry; if all fail, end session and mark as failed | Audio preserved; no transcript |
| Provider returns empty transcript | Normalized transcript has no segments | "Audio insuficiente para gerar transcricao." | Store empty transcript, proceed to AI pipeline with warning flag | Physician sees incomplete results with warning | Consultation marked with `completeness_warning` |
| Provider returns partial transcript | Missing segments or low confidence overall | No special UI (partial data flows through) | Store as-is; AI pipeline handles low-confidence input | AI artifacts flagged as potentially incomplete | Artifacts generated with confidence warnings |
| Provider latency exceeds timeout | Step Functions timeout (configurable, default 5 min) | "Processamento demorou mais que o esperado." | Retry once; if still fails, mark as `processing_failed` | Manual retry available | Raw audio preserved |
| Provider outage (sustained) | Multiple consecutive failures | "Servico de transcricao temporariamente indisponivel." | Circuit breaker pattern; stop attempts, alert operations | Operations intervenes; manual retry when provider recovers | Audio preserved in S3 for later processing |

---

## 5. AI Pipeline Failures

| Failure | Detection | User Experience | Backend Behavior | Recovery | Data Impact |
|---------|-----------|----------------|-----------------|----------|-------------|
| LLM API connection failure | httpx timeout or connection error | "Geracao de documentos em andamento..." (stays in processing) | Retry with backoff (max 3 attempts via Step Functions) | Auto-retry | Transcript preserved; no AI artifacts yet |
| LLM returns invalid JSON | Schema validation fails | Not visible (backend handles) | Log error, retry with same input (max 2 retries) | Auto-retry; if persistent, mark artifact as failed | Transcript preserved; failed artifact logged |
| LLM returns partial artifacts | Some artifacts valid, some invalid | "Alguns documentos nao puderam ser gerados." | Store valid artifacts, mark failed ones, set status to `processing_failed` | Retry failed artifacts only | Valid artifacts preserved; failed ones absent |
| LLM rate limit | 429 response | "Processamento em fila. Aguarde." | Queue request, retry after rate limit window | Automatic backoff and retry | No data loss |
| LLM content safety refusal | LLM refuses to generate output | "Nao foi possivel gerar o documento. O conteudo sera revisado." | Log refusal, mark artifact as `generation_refused`, alert operations | Manual review by operations team | Transcript preserved; artifact not generated |
| Schema validation failure (post-generation) | Pydantic validation of LLM output | Not visible (backend handles) | Log validation error, retry once with stricter prompt | Auto-retry with adjusted prompt | Previous attempt logged for debugging |
| All AI artifacts fail | Step Functions detects all artifact steps failed | "Nao foi possivel gerar os documentos da consulta." | Set status to `processing_failed`, store error details | Manual retry available; operations alerted | Transcript preserved; no AI artifacts |

---

## 6. Review and Edit Failures

| Failure | Detection | User Experience | Backend Behavior | Recovery | Data Impact |
|---------|-----------|----------------|-----------------|----------|-------------|
| Review load fails | DynamoDB/S3 read error | "Erro ao carregar a revisao. Tente novamente." | Return 500, log error | User retries page load | None (read-only failure) |
| Edit save fails | DynamoDB write error | "Erro ao salvar alteracoes. Suas edicoes estao preservadas localmente." | Return 500, log error | Frontend preserves local edits; user retries save | Local edits preserved in frontend state; server state unchanged |
| Concurrent edit conflict | Version mismatch (optimistic locking) | "Suas alteracoes conflitam com uma versao mais recente." | Return 409 with current version | Frontend shows latest version; user re-applies edits | Server has latest; user's unsaved edits need re-application |
| Unauthorized review access | Ownership check fails | "Voce nao tem permissao para acessar esta consulta." | Return 403 | N/A (security boundary) | None |

---

## 7. Finalization Failures

| Failure | Detection | User Experience | Backend Behavior | Recovery | Data Impact |
|---------|-----------|----------------|-----------------|----------|-------------|
| Finalization on wrong state | State guard check | "Esta consulta ainda nao esta pronta para finalizacao." | Return 409 with current state | User completes review first | None |
| DynamoDB write failure during finalization | boto3 exception | "Erro ao finalizar. Tente novamente." | Return 500, log error; state remains `under_physician_review` | User retries finalization | No partial finalization; all-or-nothing |
| S3 artifact write failure during finalization | boto3 exception | "Erro ao finalizar. Tente novamente." | Return 500, log error; state remains `under_physician_review` | User retries finalization | No partial finalization |
| Duplicate finalization | State check shows already finalized | No visible change (idempotent) | Return existing finalized record | N/A | None |

---

## 8. Export Failures

| Failure | Detection | User Experience | Backend Behavior | Recovery | Data Impact |
|---------|-----------|----------------|-----------------|----------|-------------|
| Export on non-finalized consultation | State guard check | "Apenas consultas finalizadas podem ser exportadas." | Return 409 | User finalizes first | None |
| PDF generation failure | Lambda handler error | "Erro ao gerar exportacao. Tente novamente." | Return 500, log error | User retries export | None (export is regeneratable) |
| S3 upload failure for export | boto3 exception | "Erro ao gerar exportacao. Tente novamente." | Return 500, log error | User retries export | None (export is regeneratable) |
| Export download link expired | S3 presigned URL expired | "Link expirado. Gere uma nova exportacao." | Return 410 | User requests new export | None (can regenerate) |

---

## 9. Infrastructure-Level Failures

| Failure | Detection | User Experience | Backend Behavior | Recovery | Data Impact |
|---------|-----------|----------------|-----------------|----------|-------------|
| Lambda cold start latency | CloudWatch metrics | Slightly slower first response | N/A (expected behavior) | Provisioned concurrency if frequent (post-MVP) | None |
| DynamoDB throttling | `ProvisionedThroughputExceededException` | Slower responses | Automatic retry with backoff (DynamoDB on-demand reduces risk) | Auto-retry; on-demand scaling handles it | None |
| S3 service degradation | Elevated error rates | "Servico temporariamente lento." | Retry with backoff | Auto-retry | None (S3 is highly durable) |
| Step Functions execution timeout | Step Functions timeout | "Processamento expirou." | Mark as `processing_failed`, alert operations | Manual retry | Transcript preserved; artifacts need regeneration |
| EventBridge delivery failure | DLQ message count | Not user-visible | Alert operations, DLQ inspection | Replay events from DLQ | Events may be delayed |

---

## 10. Retry Budget Summary

| Operation | Max Retries | Backoff Strategy | Timeout | Fallback |
|-----------|-------------|-----------------|---------|----------|
| Cognito authentication | 3 | Exponential (1s, 2s, 4s) | 10s per attempt | Return 503 |
| DynamoDB read/write | 3 | Exponential (100ms, 200ms, 400ms) | 5s per attempt | Return 500 |
| S3 read/write | 3 | Exponential (200ms, 400ms, 800ms) | 30s per attempt | Return 500 |
| Transcription provider connection | 3 | Exponential (1s, 2s, 4s) | 30s per attempt | Mark as failed |
| LLM API call | 3 | Exponential (2s, 4s, 8s) | 60s per attempt | Mark artifact as failed |
| Step Functions workflow | 2 (overall) | Per-step retries within workflow | 15 min total | Mark as `processing_failed` |
| WebSocket reconnect (grace period) | N/A (time-based) | N/A | 5 min grace period | Auto-end session |
