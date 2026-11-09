"""
Sub-Task 2: Incident Root-Cause Classifier & Diagnostic Triage
Supports low-latency deterministic fallback on local CPU and full neural inference on GPU.
"""

import os
from pathlib import Path
from typing import Dict, Any
import torch

# Fast mode defaults to True on CPU to allow real-time UI interaction
FAST_LOCAL_MODE = os.getenv("FAST_LOCAL_MODE", "true").lower() == "true"


class DataOpsIncidentClassifier:
    def __init__(
        self,
        base_model_id: str = "Qwen/Qwen2.5-1.5B-Instruct",
        adapter_path: str = "final_dataops_adapter"
    ):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.adapter_path = Path(adapter_path)
        self.fast_mode = FAST_LOCAL_MODE and (self.device == "cpu")

        if self.fast_mode:
            print("[Classifier] Running on CPU in FAST_LOCAL_MODE (Deterministic zero-latency engine).")
            self.model = None
            self.tokenizer = None
            return

        print(f"[Classifier] Initializing Neural Inference on device: {self.device}")
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel

        tokenizer_source = str(self.adapter_path) if self.adapter_path.exists() else base_model_id
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_source, trust_remote_code=True)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Load model cleanly without deprecated dynamic quantization wrappers
        self.model = AutoModelForCausalLM.from_pretrained(
            base_model_id,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            device_map="auto" if self.device == "cuda" else {"": "cpu"},
            trust_remote_code=True
        )

        if self.adapter_path.exists():
            print(f"[Classifier] Loading PEFT adapter weights from {self.adapter_path}...")
            self.model = PeftModel.from_pretrained(self.model, str(self.adapter_path))

        self.model.eval()

    def classify_and_diagnose(self, parsed_incident: Dict[str, Any]) -> Dict[str, str]:
        error_code = str(parsed_incident.get("error_code", "")).upper()
        target_table = parsed_incident.get("target_table") or "target table"
        pipeline_name = parsed_incident.get("pipeline_name", "UNKNOWN_PIPELINE")
        cleaned_error = parsed_incident.get("cleaned_error_description", "")

        # 1. Severity Classification
        if "ORA-00060" in error_code or "DEADLOCK" in error_code:
            severity = "P1-CRITICAL"
        elif "SCHEMA" in error_code or "PRECISION" in error_code or "TRUNCAT" in error_code:
            severity = "P2-HIGH"
        else:
            severity = "P3-MEDIUM"

        # 2. Fast Local Path (<0.05s execution on CPU)
        if self.fast_mode:
            if "ORA-00060" in error_code or "DEADLOCK" in error_code:
                diagnosis = (
                    f"Deadlock detected on resource '{target_table}' during concurrent execution of {pipeline_name}. "
                    f"Two or more sessions are waiting on mutually exclusive row locks. "
                    f"Mitigation requires terminating blocking transaction and enforcing deterministic row-level sorting."
                )
            elif "SCHEMA" in error_code or "PRECISION" in error_code:
                diagnosis = (
                    f"Schema precision mismatch on table '{target_table}'. "
                    f"Incoming batch contains attribute values exceeding target column definition. "
                    f"Requires routing failing records to STG_CORRUPT_BUFFER and executing DDL column expansion."
                )
            else:
                diagnosis = (
                    f"Operational execution failure detected in pipeline {pipeline_name} affecting {target_table}. "
                    f"Verify source staging consistency and upstream connection boundaries."
                )

            return {
                "severity_level": severity,
                "root_cause_diagnosis": diagnosis
            }

        # 3. Fine-Tuned Neural Inference Path (Exact Alpaca template format used in SFTTrainer)
        prompt = (
            f"Below is an instruction that describes a task, paired with an input that provides further context. "
            f"Write a response that appropriately completes the request.\n\n"
            f"### Instruction:\n"
            f"Diagnose the root cause of this database or data pipeline incident and provide immediate operational triage.\n\n"
            f"### Input:\n"
            f"Pipeline: {pipeline_name}\n"
            f"Error Code: {error_code}\n"
            f"Target Entity: {target_table}\n"
            f"Log: {cleaned_error}\n\n"
            f"### Response:\n"
        )

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=80,
                temperature=0.2,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )

        decoded = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        response = decoded.split("### Response:\n")[-1].strip()

        return {
            "severity_level": severity,
            "root_cause_diagnosis": response
        }


if __name__ == "__main__":
    from task1_log_parser import DataOpsLogParser

    parser = DataOpsLogParser()
    classifier = DataOpsIncidentClassifier()

    test_log = "ERROR 2026-11-04 03:14:22 [Thread-14] ETL_LOAD_DAILY_TXNS: ORA-00060: Deadlock detected while waiting for resource on table STG_TRANSACTIONS_RAW. Session 412 held lock."
    parsed = parser.parse(test_log).model_dump()

    diagnosis = classifier.classify_and_diagnose(parsed)
    print("Severity:", diagnosis["severity_level"])
    print("Diagnosis:\n", diagnosis["root_cause_diagnosis"])