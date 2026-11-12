# 🛡️ DataOps Incident Remediation Copilot
> **Cloud-Native AI System for Autonomous Database SRE Triage, Root-Cause Diagnostics, and SQL Patch Generation**  
> *BITS Pilani — M.Tech in AI & ML / API-driven Cloud Solutions (Assignment 2)*

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Model: Qwen2.5-1.5B](https://img.shields.io/badge/Base_SLM-Qwen2.5--1.5B--Instruct-orange.svg)](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct)
[![PEFT: LoRA](https://img.shields.io/badge/PEFT-QLoRA_(r%3D16)-green.svg)](https://github.com/huggingface/peft)
[![Vector DB: Chroma](https://img.shields.io/badge/Vector_Store-ChromaDB-purple.svg)](https://www.trychroma.com/)
[![UI: Streamlit](https://img.shields.io/badge/Interface-Streamlit-red.svg)](https://streamlit.io/)

---

## 📌 Executive Overview

In modern cloud data platforms and distributed ETL topologies, transient data engineering failures—such as **Oracle deadlocks (`ORA-00060`)**, **schema drift precision overflows**, and **distributed lock contention**—cause severe pipeline stalls. Traditional SRE playbooks require manual log parsing, log correlation, manual knowledge base lookups, and ad-hoc SQL mitigation.

The **DataOps Incident Remediation Copilot** automates this lifecycle by orchestrating three cohesive NLP tasks with Retrieval-Augmented Generation (RAG):
1. **Sub-Task 1: Log Parsing & Named Entity Recognition (NER)** via typed Pydantic contracts.
2. **Sub-Task 2: SLM Root-Cause Diagnostics & Triage** powered by a fine-tuned `Qwen2.5-1.5B-Instruct` model trained via QLoRA.
3. **Sub-Task 3: Deterministic Patch Synthesis & Verification** grounded in enterprise Standard Operating Procedures (SOPs) indexed within a local `ChromaDB` vector store.

---

## 🏛️ System Architecture

```text
       RAW UNSTRUCTURED INCIDENT LOGS (Text Stream)
                          │
                          ▼
 ┌─────────────────────────────────────────────────────────┐
 │ Sub-Task 1: Log Entity Parser & Tokenizer (Regex + NER)  │
 │  - Extracts: Timestamp, Pipeline ID, Error Code, Entity │
 │  - Outputs: Validated Pydantic Schema Contract         │
 └────────────────────────┬────────────────────────────────┘
                          │
        Structured Metadata Context Payload
                          │
        ┌─────────────────┴─────────────────┐
        ▼                                   ▼
┌───────────────────────────────┐   ┌───────────────────────────────┐
│ Sub-Task 2: SLM Root-Cause    │   │ Part III: ChromaDB RAG Engine │
│ Classifier (Qwen2.5-1.5B LoRA)│   │ (sentence-transformers MiniLM)│
│  - Severity: P1 / P2 / P3     │   │  - Semantic SOP Retrieval     │
│  - Deep Technical Diagnosis   │   │  - Authoritative Runbook Ref  │
└───────────────┬───────────────┘   └───────────────┬───────────────┘
                │                                   │
                └─────────────────┬─────────────────┘
                                  │
                                  ▼
 ┌─────────────────────────────────────────────────────────┐
 │ Sub-Task 3: Automated Remediation & SQL Patch Generator  │
 │  - Synthesizes Diagnosis + SOP Context                  │
 │  - Produces: Administrative Mitigation SQL (KILL / DDL) │
 │  - Generates: Post-Remediation Verification & Rollback  │
 └────────────────────────┬────────────────────────────────┘
                          │
                          ▼
 ┌─────────────────────────────────────────────────────────┐
 │ Part IV: Unified Streamlit Cloud-Native Web Dashboard   │
 │  - Real-time Log Stream Ingestion & Triage Inspection    │
 └─────────────────────────────────────────────────────────┘