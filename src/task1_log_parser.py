"""
Sub-Task 1: Log Parser & Entity Extraction (NER / Information Extraction)
Extracts structured incident metadata (pipeline, table, error code, timestamp)
from raw unstructured database/ETL log streams.
"""

import re
from typing import Optional
from pydantic import BaseModel, Field


class IncidentMetadata(BaseModel):
    timestamp: Optional[str] = Field(None, description="Timestamp extracted from the log")
    pipeline_name: str = Field("UNKNOWN_PIPELINE", description="Name of the ETL/ELT pipeline")
    thread_worker: Optional[str] = Field(None, description="Worker or thread context")
    error_code: str = Field("UNKNOWN_ERROR", description="Database or system error code")
    target_table: Optional[str] = Field(None, description="Database table or entity affected")
    raw_message: str = Field(..., description="Original raw error log line")
    cleaned_error_description: str = Field(..., description="Extracted root error statement")


class DataOpsLogParser:
    def __init__(self):
        self.ts_pattern = re.compile(r"\b(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?)\b")
        self.thread_pattern = re.compile(r"\[(Thread-\d+|Stage-\d+|Pool-Worker-\d+|Worker-\d+)\]", re.IGNORECASE)
        
        # Extracts pipeline token appearing after thread tag or log level: e.g. [Stage-4] SYNC_INVOICE_LEDGER:
        self.pipeline_context_pattern = re.compile(r"\]\s*([A-Za-z0-9_]+):")
        self.pipeline_fallback_pattern = re.compile(r"\b([A-Z0-9_]+(?:_ETL|_LOAD|_INGEST|_SYNC|_STAGE|_JOB|_LEDGER)[A-Z0-9_]*)\b")
        
        # Error signatures
        self.error_code_patterns = [
            (re.compile(r"\b(ORA-\d{5})\b"), None),
            (re.compile(r"\b(SQLSTATE\[[A-Z0-9]+\])\b"), None),
            (re.compile(r"\b([0-9]{2}[A-Z0-9]{3}: [a-zA-Z_ ]+)\b"), None),
            (re.compile(r"\b(JDBC-[A-Z0-9_]+|CONNECTION_TIMED_OUT|DEADLOCK_DETECTED)\b", re.IGNORECASE), None),
            (re.compile(r"(value length exceeds target precision|string or binary data would be truncated)", re.IGNORECASE), "SCHEMA_PRECISION_OVERFLOW"),
            (re.compile(r"(foreign key constraint.*failed)", re.IGNORECASE), "INTEGRITY_CONSTRAINT_VIOLATION"),
            (re.compile(r"(no space left on device)", re.IGNORECASE), "STORAGE_QUOTA_EXHAUSTED"),
        ]
        
        self.table_pattern = re.compile(r"\b(?:table|relation|stage|into)\s+([A-Z0-9_\.]+)", re.IGNORECASE)

    def parse(self, raw_log: str) -> IncidentMetadata:
        cleaned_log = raw_log.strip()
        
        # 1. Timestamp
        ts_match = self.ts_pattern.search(cleaned_log)
        timestamp = ts_match.group(1) if ts_match else None
        
        # 2. Thread Context
        thread_match = self.thread_pattern.search(cleaned_log)
        thread_worker = thread_match.group(1) if thread_match else None
        
        # 3. Pipeline Name (contextual first, fallback second)
        pipe_match = self.pipeline_context_pattern.search(cleaned_log)
        if pipe_match:
            pipeline_name = pipe_match.group(1).strip()
        else:
            fallback = self.pipeline_fallback_pattern.search(cleaned_log)
            pipeline_name = fallback.group(1) if fallback else "UNKNOWN_PIPELINE"
        
        # 4. Error Code / Classification Tag
        error_code = "UNKNOWN_ERROR"
        for pattern, tag in self.error_code_patterns:
            code_match = pattern.search(cleaned_log)
            if code_match:
                error_code = tag if tag else code_match.group(1).strip()
                break
                
        # 5. Target Table
        table_match = self.table_pattern.search(cleaned_log)
        target_table = None
        if table_match:
            candidate_table = table_match.group(1).strip().strip(".,;:\"'")
            if candidate_table.upper() not in ["IS", "A", "THE", "LOCK"]:
                target_table = candidate_table
                
        # 6. Cleaned Error Description
        desc = cleaned_log
        if "ORA-" in cleaned_log:
            idx = cleaned_log.find("ORA-")
            desc = cleaned_log[idx:]
        elif ":" in cleaned_log:
            parts = cleaned_log.split(":", 2)
            desc = parts[-1].strip() if len(parts) >= 3 else parts[1].strip()
            
        return IncidentMetadata(
            timestamp=timestamp,
            pipeline_name=pipeline_name,
            thread_worker=thread_worker,
            error_code=error_code,
            target_table=target_table,
            raw_message=cleaned_log,
            cleaned_error_description=desc
        )


if __name__ == "__main__":
    parser = DataOpsLogParser()
    sample_log_1 = "ERROR 2026-11-04 03:14:22 [Thread-14] ETL_LOAD_DAILY_TXNS: ORA-00060: Deadlock detected while waiting for resource on table STG_TRANSACTIONS_RAW. Session 412 held lock."
    sample_log_2 = "FATAL 2026-11-04 14:02:11 [Stage-4] SYNC_INVOICE_LEDGER: Column 'billing_address_line2' value length exceeds target precision on table DIM_CUSTOMERS."
    
    print("--- Refined Test Log 1 ---")
    print(parser.parse(sample_log_1).model_dump_json(indent=2))
    
    print("\n--- Refined Test Log 2 ---")
    print(parser.parse(sample_log_2).model_dump_json(indent=2))