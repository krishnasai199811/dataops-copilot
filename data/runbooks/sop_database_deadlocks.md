# SOP-DB-042: Database Deadlock & Concurrency Remediation Runbook

## Scope & Applicability
This standard operating procedure applies to all high-throughput batch ingestion pipelines targeting staging and operational datastores (e.g., Oracle, PostgreSQL, Snowflake).

## Incident Detection Symptoms
- Log error signatures: `ORA-00060`, `40P01: deadlock detected`, or `deadlock detected while waiting for resource`.
- Thread status: Blocked in `EXCLUSIVE` lock acquisition state.
- Latency spike exceeding the 15-minute pipeline SLA.

## Mandatory Triage Protocol
1. **Identify Blocking Transactions**: Query active sessions to pinpoint the parent session ID holding the mutual exclusion lock.
2. **Immediate Mitigation**: 
   - Terminate the lowest-priority holding session using administrative kill signals.
   - Do not restart batch pipelines concurrently on unindexed foreign key tables.
3. **Permanent Resolution**:
   - Refactor DML statements to access staging tables in strict alphabetical or hierarchical order.
   - Enforce row-level batching (chunk size ≤ 5,000 rows) with random exponential backoff retries.