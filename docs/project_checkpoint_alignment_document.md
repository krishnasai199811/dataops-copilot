# AIMLZG 549: API-driven Cloud Native Solutions
## Assignment II — Technical Progress Checkpoint & Rubric Cross-Check
**Domain**: Enterprise DataOps & SRE Incident Remediation  
**Academic Level**: M.Tech (Cloud Native & AI Track)  
**Date**: November 2026

---

## 1. What We Have Built So Far & Why

| Step / Artifact | What Was Done | Why It Was Done (Academic & Architectural Rationale) |
| :--- | :--- | :--- |
| **Workspace & Git Architecture** | Initialized standard Git tree (`notebooks/`, `data/`, `src/`), configured `.gitignore`, and pinned `requirements.txt`. | Enables seamless group collaboration, prevents OS-specific environment divergence, and ensures teammates can clone and run immediately without missing dependencies. |
| **Model Selection** | Selected `Qwen/Qwen2.5-1.5B-Instruct` as the foundational Small Language Model (SLM). | Fulfills Assignment Part I (item 4: SLM identification). At 1.5B parameters, it offers superior technical reasoning for code/logs while remaining lightweight enough to fine-tune on free GPU tiers. |
| **Dataset Selection** | Selected `TokenBender/code_instructions_122k_alpaca_style` from Hugging Face and sampled **5,000 rigorous technical rows** (4,500 train / 500 validation). | Fulfills Part II (Fine-Tuning on an existing domain dataset). Avoids toy-dataset penalties (100 rows is insufficient for M.Tech evaluation); provides statistically smooth loss curves without GPU timeouts. |
| **Quantization Strategy** | Configured 4-bit NormalFloat (`nf4`) quantization with strict FP16 compute via `bitsandbytes`. | Solves CUDA driver AMP unscaling incompatibilities on Tesla T4 hardware while slashing model VRAM footprint from ~6.2 GB to ~1.8 GB. |
| **PEFT / QLoRA Implementation** | Attached low-rank adapters ($r=16, \alpha=32$) across all linear projection layers (`q_proj`, `k_proj`, `v_proj`, `o_proj`, etc.). | Freezes 98.82% of base model weights, preserving general language reasoning while updating only 18.4M parameters (1.18% trainable) specifically for incident remediation. |
| **Training Execution & Metrics** | Completed 1 full epoch (282 update steps). Validation loss converged from **0.5757 to 0.5608**; Mean Token Accuracy reached **84.42%**. | Yields empirical metrics and smooth loss curves required for the final evaluation report and grading rubric. |
| **Adapter Serialization & Git Tracking** | Saved final LoRA weights (`adapter_model.safetensors`, 35.27 MB) and synced them to Git. | GitHub permits files under 100 MB. Committing the 35.3 MB adapter directly ensures group members get the trained checkpoint upon `git clone` without manual downloads. |
| **Enterprise SOP Knowledge Base** | Authored initial domain runbooks in `data/runbooks/` (`SOP-DB-042` for deadlocks, `SOP-PIPE-109` for schema drift). | Establishes domain grounding documents for the Part III Retrieval-Augmented Generation (RAG) vector database. |

---

## 2. Rubric Cross-Check Matrix (Assignment II)

| Rubric Component | Assignment Requirement | Current Status | Next Required Actions |
| :--- | :--- | :--- | :--- |
| **Part I: Cohesive AI Application** (4 Marks) | Domain selection, NLP category, $\ge 3$ cohesive sub-tasks, SLM/LLM identification, interactive demonstrable UI/API. | **In Progress (60%)** | Sub-tasks 1 (NER Log Parser), 2 (Classifier), and 3 (Patch Generator) defined. Next: wrap in Streamlit UI (`src/app.py`). |
| **Part II: Fine-Tuning** (2 Marks) | Select domain dataset and fine-tune model with verifiable training results. | **COMPLETED (100%)** | QLoRA executed with full training trace, 84.42% accuracy, loss curves, and verified adapter weights committed. |
| **Part III: RAG Model** (4 Marks) | Domain documents (PDFs/manuals), vector store retrieval, interactive chatbot grounded in context. | **In Progress (30%)** | Enterprise SOPs written in `data/runbooks/`. Next: build `src/rag_engine.py` (ChromaDB + LangChain embeddings). |
| **Part IV: Situated Learning** (5 Marks) | Anchor (1m), Apply (2m), Analyse (1m), Reflect (1m) addressing enterprise deployment constraints. | **Planned (10%)** | Problem domain anchored in DataOps batch pipeline operations. Next: author comprehensive report section with latency/security analysis. |

---

## 3. Immediate Next Steps (Phase 3 Execution)

1. **Step 8: Vector RAG Pipeline (`src/rag_engine.py`)**
   - Implement document loader (Markdown/PDF recursive character text splitter).
   - Ingest runbooks into local **ChromaDB** using `sentence-transformers/all-MiniLM-L6-v2`.
   - Implement context retrieval query engine with strict grounded prompt guardrails.
2. **Step 9: Cohesive NLP Sub-Tasks (`src/task1_log_parser.py`, `src/task3_patch_generator.py`)**
   - Connect log parsing (Task 1), fine-tuned inference (Task 2), and SQL/code mitigation (Task 3).
3. **Step 10: Streamlit Dashboard UI (`src/app.py`)**
   - Build unified web interface linking the 3 sub-tasks and the interactive RAG Copilot chat.