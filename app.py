"""
DataOps & SRE Incident Remediation Copilot - Interactive Streamlit Dashboard
Integrates Log Extraction (NER), SLM Root-Cause Diagnosis (LoRA), 
Vector Search Runbooks (ChromaDB RAG), and Automated SQL Patch Generation.
"""

import streamlit as st
import time
from pathlib import Path
import json

# Internal system modules
from src.task1_log_parser import DataOpsLogParser
from src.task2_classifier import DataOpsIncidentClassifier
from src.rag_engine import DataOpsRAG
from src.task3_patch_generator import DataOpsRemediationEngine

# Page configuration
st.set_page_config(
    page_title="DataOps Incident Remediation Copilot",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom enterprise styling
st.markdown("""
<style>
    .metric-card {
        background-color: #1E222A;
        border: 1px solid #30363D;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 12px;
    }
    .badge-p1 {
        background-color: #8E1515;
        color: #FFFFFF;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
    .badge-p2 {
        background-color: #C25E00;
        color: #FFFFFF;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
    .badge-p3 {
        background-color: #1F6FEB;
        color: #FFFFFF;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


# --- Cached Resources (Loaded once into RAM) ---
@st.cache_resource(show_spinner="Initializing RAG ChromaDB & Embeddings...")
def get_rag_engine():
    return DataOpsRAG()

@st.cache_resource(show_spinner="Loading Fine-Tuned SLM (Qwen2.5-1.5B + LoRA)...")
def get_classifier():
    return DataOpsIncidentClassifier()

@st.cache_resource(show_spinner="Initializing Remediation Engine...")
def get_remediation_engine(_rag_instance):
    return DataOpsRemediationEngine(rag_engine=_rag_instance)


# Initialize components
parser = DataOpsLogParser()
rag = get_rag_engine()
classifier = get_classifier()
remediation_engine = get_remediation_engine(rag)


# --- Sidebar Navigation & Preset Scenarios ---
with st.sidebar:
    st.title("🛡️ DataOps AIOps Hub")
    st.caption("BITS Pilani M.Tech — API-driven Cloud Solutions")
    st.markdown("---")
    
    st.subheader("System Architecture")
    st.markdown("""
    - **Base Model**: `Qwen/Qwen2.5-1.5B-Instruct`
    - **PEFT**: QLoRA (r=16, alpha=32)
    - **Vector Store**: ChromaDB (MiniLM-L6)
    - **Interface**: Streamlit Cloud-Native UI
    """)
    st.markdown("---")
    
    st.subheader("Select Incident Preset")
    preset_choice = st.selectbox(
        "Load enterprise test logs:",
        [
            "Custom Log Entry",
            "Preset 1: Oracle Concurrency Deadlock (ORA-00060)",
            "Preset 2: Dimensional Schema Precision Overflow",
            "Preset 3: Foreign Key Constraint Failure"
        ]
    )

# Preset log data
preset_logs = {
    "Preset 1: Oracle Concurrency Deadlock (ORA-00060)": 
        "ERROR 2026-11-04 03:14:22 [Thread-14] ETL_LOAD_DAILY_TXNS: ORA-00060: Deadlock detected while waiting for resource on table STG_TRANSACTIONS_RAW. Session 412 held lock.",
    "Preset 2: Dimensional Schema Precision Overflow": 
        "FATAL 2026-11-04 14:02:11 [Stage-4] SYNC_INVOICE_LEDGER: Column 'billing_address_line2' value length exceeds target precision on table DIM_CUSTOMERS.",
    "Preset 3: Foreign Key Constraint Failure": 
        "ERROR 2026-11-04 18:22:05 [Worker-8] INGEST_ORDER_EVENTS: foreign key constraint failed on relation ORDERS_FACT referencing DIM_CUSTOMERS."
}

default_text = preset_logs.get(preset_choice, "")


# --- Main Dashboard Header ---
st.title("DataOps Incident Remediation Copilot")
st.markdown("Automated log triage, root-cause diagnostics, runbook retrieval, and SQL patch generation.")

# --- Step 1: Ingestion & Parsing ---
st.subheader("1. Incident Log Stream Ingestion")
log_input = st.text_area(
    "Paste raw execution log or stack trace below:",
    value=default_text,
    height=110,
    placeholder="Paste error logs here..."
)

col_btn1, col_btn2 = st.columns([1, 4])
run_triage = col_btn1.button("⚡ Run Full Incident Triage", type="primary")

if run_triage and log_input.strip():
    start_time = time.time()
    
    # --- Task 1: Log Extraction ---
    with st.spinner("Sub-Task 1: Parsing log entities and isolating signature..."):
        parsed_meta = parser.parse(log_input).model_dump()
        
    st.markdown("---")
    st.subheader("2. Structured Metadata Extraction (Sub-Task 1)")
    
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.metric("Pipeline Name", parsed_meta.get("pipeline_name", "UNKNOWN"))
    with m_col2:
        st.metric("Error Signature", parsed_meta.get("error_code", "UNKNOWN"))
    with m_col3:
        st.metric("Target Entity", parsed_meta.get("target_table") or "N/A")
    with m_col4:
        st.metric("Thread Context", parsed_meta.get("thread_worker") or "N/A")
        
    with st.expander("🔍 View Raw JSON Payload (Sub-Task 1 Contract)"):
        st.json(parsed_meta)

    # --- Task 2: SLM Root-Cause Classification ---
    st.markdown("---")
    st.subheader("3. SLM Root-Cause Diagnosis (Sub-Task 2)")
    with st.spinner("Sub-Task 2: Running fine-tuned Qwen2.5-1.5B LoRA model inference..."):
        diag_res = classifier.classify_and_diagnose(parsed_meta)
    
    severity = diag_res.get("severity_level", "P3-MEDIUM")
    badge_class = "badge-p1" if "P1" in severity else ("badge-p2" if "P2" in severity else "badge-p3")
    
    st.markdown(f"**Incident Severity:** <span class='{badge_class}'>{severity}</span>", unsafe_allow_html=True)
    st.info(f"**Diagnostic Analysis:**\n\n{diag_res.get('root_cause_diagnosis', 'No diagnosis generated.')}")

    # --- Part III: RAG Retrieval & Sub-Task 3 Remediation ---
    st.markdown("---")
    st.subheader("4. RAG Runbook Grounding & Patch Synthesis (Sub-Task 3)")
    with st.spinner("Sub-Task 3 & Part III: Querying ChromaDB runbooks and generating executable patch..."):
        remediation_plan = remediation_engine.generate_remediation_plan(parsed_meta, diag_res)

    rag_col, patch_col = st.columns([1, 1])
    
    with rag_col:
        st.markdown("#### 📖 Authoritative Enterprise SOP (RAG)")
        st.caption(f"**Retrieved Document:** `{remediation_plan['matched_sop']}`")
        st.text_area("SOP Reference Guidelines", value=remediation_plan["sop_excerpt"], height=230, disabled=True)
        
        st.markdown("#### 📋 Operational Procedure")
        for i, step in enumerate(remediation_plan["actionable_steps"], 1):
            st.markdown(f"**{i}.** {step}")

    with patch_col:
        st.markdown("#### 🛠️ Executable SQL Remediation Patch")
        st.code(remediation_plan["executable_sql_patch"], language="sql")
        
        st.markdown("#### 🔬 Post-Remediation Verification Query")
        st.code(remediation_plan["verification_query"], language="sql")
        
        st.markdown("#### ↩️ Rollback Protocol")
        st.code(remediation_plan["rollback_plan"], language="sql")

    elapsed = round(time.time() - start_time, 2)
    st.success(f"Incident triage and remediation plan synthesized successfully in {elapsed}s.")

elif run_triage and not log_input.strip():
    st.warning("Please provide or select an incident log before running triage.")