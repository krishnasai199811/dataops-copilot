# SOP-PIPE-109: Schema Drift & Column Precision Overflow Remediation

## Scope & Applicability
Applies to automated ETL/ELT pipelines loading semi-structured payloads into strongly typed dimensional models.

## Incident Detection Symptoms
- Log error signatures: `String or binary data would be truncated`, `column length exceeds target precision`, or `Value too long for character length`.
- Pipeline status: `FAILED_DURING_TRANSFORMATION`.

## Mandatory Triage Protocol
1. **Quarantine Ingestion**:
   - Divert the offending batch partition to the Dead Letter Queue (DLQ) or error staging table (`STG_CORRUPT_BUFFER`).
   - Allow downstream non-dependent pipeline stages to resume.
2. **Schema Alteration Approval**:
   - Verify if the field expansion complies with data governance guidelines.
   - Execute non-blocking column expansion:
     ```sql
     ALTER TABLE <schema>.<target_table> MODIFY COLUMN <column_name> VARCHAR(256);
     ```
3. **Backfill**:
   - Replay records from `STG_CORRUPT_BUFFER` using the corrected target schema mapping.