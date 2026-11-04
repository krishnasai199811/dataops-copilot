"""
Sub-Task 2: Incident Root-Cause Classifier & Diagnostic Triage
Uses the fine-tuned Small Language Model (SLM) with LoRA adapter weights
to perform root-cause classification and incident impact assessment.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel


class DataOpsIncidentClassifier:
    def __init__(
        self,
        base_model_id: str = "Qwen/Qwen2.5-1.5B-Instruct",
        adapter_path: str = "final_dataops_adapter"
    ):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.adapter_path = Path(adapter_path)
        print(f"[Classifier] Initializing inference device: {self.device}")
        
        # Load Tokenizer
        tokenizer_source = str(self.adapter_path) if self.adapter_path.exists() else base_model_id
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_source, trust_remote_code=True)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Load Base Model + LoRA Adapter
        print(f"[Classifier] Loading base model: {base_model_id}...")
        if self.device == "cuda":
            self.model = AutoModelForCausalLM.from_pretrained(
                base_model_id,
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True
            )
        else:
            # CPU fallback for local machines without NVIDIA GPU
            self.model = AutoModelForCausalLM.from_pretrained(
                base_model_id,
                torch_dtype=torch.float32,
                device_map={"": "cpu"},
                trust_remote_code=True
            )

        # Attach LoRA weights if adapter directory exists
        if self.adapter_path.exists():
            print(f"[Classifier] Loading fine-tuned LoRA adapter from {self.adapter_path}...")
            self.model = PeftModel.from_pretrained(self.model, str(self.adapter_path))
        else:
            print(f"[Classifier Warning] Adapter path {self.adapter_path} not found. Running base model.")
            
        self.model.eval()

    def classify_and_diagnose(self, parsed_incident: Dict[str, Any]) -> Dict[str, str]:
        """
        Takes structured metadata from Sub-Task 1 and runs SLM inference
        to produce a root cause diagnosis and severity classification.
        """
        prompt = (
            f"<|im_start|>system\n"
            f"You are an enterprise DataOps & SRE Incident Copilot. Analyze the operational failure "
            f"and diagnose the root cause and recommended remediation.<|im_end|>\n"
            f"<|im_start|>user\n"
            f"Pipeline: {parsed_incident.get('pipeline_name', 'UNKNOWN')}\n"
            f"Target Entity: {parsed_incident.get('target_table', 'N/A')}\n"
            f"Error Code: {parsed_incident.get('error_code', 'N/A')}\n"
            f"Log Message: {parsed_incident.get('raw_message', '')}<|im_end|>\n"
            f"<|im_start|>assistant\n"
        )

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=160,
                temperature=0.2,
                do_sample=True,
                top_p=0.9,
                pad_token_id=self.tokenizer.eos_token_id
            )

        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        response_part = generated_text.split("assistant\n")[-1].strip()

        # Heuristic severity tagging based on extracted metadata & diagnostic keywords
        error_code = parsed_incident.get("error_code", "")
        if "ORA-00060" in error_code or "DEADLOCK" in error_code:
            severity = "P1-CRITICAL"
        elif "SCHEMA" in error_code or "PRECISION" in error_code:
            severity = "P2-HIGH"
        else:
            severity = "P3-MEDIUM"

        return {
            "severity_level": severity,
            "root_cause_diagnosis": response_part
        }


if __name__ == "__main__":
    from task1_log_parser import DataOpsLogParser

    parser = DataOpsLogParser()
    classifier = DataOpsIncidentClassifier()

    test_log = "ERROR 2026-11-04 03:14:22 [Thread-14] ETL_LOAD_DAILY_TXNS: ORA-00060: Deadlock detected while waiting for resource on table STG_TRANSACTIONS_RAW. Session 412 held lock."
    parsed = parser.parse(test_log).model_dump()

    print("\n--- Sub-Task 1 Output (Metadata) ---")
    print(parsed)

    print("\n--- Running Sub-Task 2 (Fine-Tuned SLM Inference) ---")
    diagnosis = classifier.classify_and_diagnose(parsed)
    print("Severity:", diagnosis["severity_level"])
    print("Diagnosis:\n", diagnosis["root_cause_diagnosis"])