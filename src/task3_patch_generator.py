"""
Sub-Task 3: Automated Remediation & SQL Patch Generator
Synthesizes structured metadata, SLM diagnostic root causes, and RAG SOP runbooks
to produce deterministic, production-grade remediation scripts and mitigation plans.
"""

from typing import Dict, Any, List
from pathlib import Path


class DataOpsRemediationEngine:
    def __init__(self, rag_engine=None):
        """
        Initializes the remediation engine with access to the ChromaDB RAG store.
        """
        if rag_engine is None:
            from rag_engine import DataOpsRAG
            self.rag = DataOpsRAG()
        else:
            self.rag = rag_engine

    def generate_remediation_plan(
        self,
        incident_meta: Dict[str, Any],
        diagnosis_meta: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Combines metadata, diagnosis, and RAG SOP retrieval to generate
        executable SQL patches and operational recovery steps.
        """
        error_code = incident_meta.get("error_code", "")
        target_table = incident_meta.get("target_table") or "TARGET_TABLE_PLACEHOLDER"
        pipeline_name = incident_meta.get("pipeline_name", "UNKNOWN_PIPELINE")
        
        # 1. Retrieve authoritative SOP from Vector Store
        # Ensure RAG query uses both the error code and the descriptive diagnosis for maximum semantic similarity
        cleaned_desc = incident_meta.get("cleaned_error_description", "")
        rag_query = f"{error_code} {cleaned_desc} deadlock concurrency schema remediation"
        rag_result = self.rag.query(rag_query, top_k=1)
        rag_result = self.rag.query(rag_query, top_k=1)
        
        sop_matched = "None"
        sop_content = ""
        if rag_result["retrieved_contexts"]:
            top_doc = rag_result["retrieved_contexts"][0]
            sop_matched = f"{top_doc['source']} (Relevance: {top_doc['relevance_score']})"
            sop_content = top_doc["content"]

        # 2. Rule-grounded deterministic patch generation
        remediation_steps: List[str] = []
        sql_patch: str = ""
        verification_sql: str = ""
        rollback_sql: str = ""

        if "ORA-00060" in error_code or "DEADLOCK" in error_code:
            remediation_steps = [
                f"Identify and terminate the lowest-priority holding session on '{target_table}'.",
                "Quarantine concurrent batch workers to eliminate write collision.",
                f"Enforce deterministic record ordering (ORDER BY primary_key) in {pipeline_name}.",
                "Resume pipeline with chunk size capped at 5,000 rows with exponential backoff."
            ]
            sql_patch = (
                f"-- [Mitigation] Identify and kill blocking sessions on {target_table}\n"
                f"SELECT blocking_session, sid, serial#, wait_class\n"
                f"FROM v$session\n"
                f"WHERE blocking_session IS NOT NULL;\n\n"
                f"-- Execute administrative session termination:\n"
                f"-- ALTER SYSTEM KILL SESSION '<sid>,<serial#>' IMMEDIATE;"
            )
            verification_sql = (
                f"SELECT COUNT(*) AS active_locks \n"
                f"FROM v$locked_object \n"
                f"WHERE object_id = OBJECT_ID('{target_table}');"
            )
            rollback_sql = f"-- No DDL modifications applied. Deadlock resolution is runtime session recovery."

        elif "SCHEMA" in error_code or "PRECISION" in error_code:
            remediation_steps = [
                f"Divert failing payload partition to STG_CORRUPT_BUFFER quarantine queue.",
                f"Execute non-blocking column width expansion on {target_table}.",
                "Replay quarantined partition records.",
                "Trigger downstream dimensional reconcile check."
            ]
            sql_patch = (
                f"-- [DDL Expansion] Expand target column width to prevent truncation\n"
                f"ALTER TABLE {target_table} MODIFY COLUMN payload_field VARCHAR(512);\n\n"
                f"-- Replay from Dead Letter Queue buffer\n"
                f"INSERT INTO {target_table}\n"
                f"SELECT * FROM STG_CORRUPT_BUFFER WHERE pipeline_id = '{pipeline_name}';"
            )
            verification_sql = (
                f"SELECT column_name, data_type, character_maximum_length\n"
                f"FROM information_schema.columns\n"
                f"WHERE table_name = '{target_table}';"
            )
            rollback_sql = (
                f"ALTER TABLE {target_table} MODIFY COLUMN payload_field VARCHAR(256);"
            )

        else:
            remediation_steps = [
                "Review application execution logs for unhandled edge-case exception.",
                f"Validate connectivity between {pipeline_name} and target datastore {target_table}.",
                "Re-execute pipeline in dry-run mode."
            ]
            sql_patch = f"-- Diagnostic inspection\nSELECT * FROM sys.pipeline_events WHERE pipeline_id = '{pipeline_name}' ORDER BY event_time DESC LIMIT 10;"
            verification_sql = f"SELECT status FROM sys.pipeline_runs WHERE pipeline_id = '{pipeline_name}' ORDER BY start_time DESC LIMIT 1;"
            rollback_sql = "-- No changes applied."

        return {
            "pipeline_name": pipeline_name,
            "target_table": target_table,
            "severity": diagnosis_meta.get("severity_level", "P3-MEDIUM"),
            "matched_sop": sop_matched,
            "sop_excerpt": sop_content,
            "actionable_steps": remediation_steps,
            "executable_sql_patch": sql_patch,
            "verification_query": verification_sql,
            "rollback_plan": rollback_sql
        }


if __name__ == "__main__":
    from task1_log_parser import DataOpsLogParser

    parser = DataOpsLogParser()
    remediation_engine = DataOpsRemediationEngine()

    test_log = "ERROR 2026-11-04 03:14:22 [Thread-14] ETL_LOAD_DAILY_TXNS: ORA-00060: Deadlock detected while waiting for resource on table STG_TRANSACTIONS_RAW. Session 412 held lock."
    parsed = parser.parse(test_log).model_dump()
    
    mock_diagnosis = {
        "severity_level": "P1-CRITICAL",
        "root_cause_diagnosis": "Deadlock detected between competing sessions on STG_TRANSACTIONS_RAW."
    }

    print("\n--- Running Sub-Task 3: Remediation & Patch Generation ---")
    plan = remediation_engine.generate_remediation_plan(parsed, mock_diagnosis)
    
    print(f"Matched Runbook: {plan['matched_sop']}")
    print("\nOperational Steps:")
    for i, step in enumerate(plan['actionable_steps'], 1):
        print(f"  {i}. {step}")
    
    print("\nExecutable SQL Patch:")
    print(plan["executable_sql_patch"])
    
    print("\nVerification SQL:")
    print(plan["verification_query"])