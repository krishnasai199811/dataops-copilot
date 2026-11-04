"""
RAG Engine for Enterprise DataOps & SRE Incident Remediation.
Handles document ingestion, vector embedding storage (ChromaDB), 
similarity search, and context-grounded prompt synthesis.
"""

import os
from pathlib import Path
from typing import List, Dict, Any

from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma


class DataOpsRAG:
    def __init__(
        self,
        docs_dir: str = "data/runbooks",
        persist_dir: str = "chroma_db",
        embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        self.docs_dir = Path(docs_dir)
        self.persist_dir = Path(persist_dir)
        
        # Initialize open-source embedding model
        print(f"[RAG] Loading embedding model: {embedding_model_name}...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model_name,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
        self.vector_store = None
        self._init_vector_store()

    def _init_vector_store(self):
        """Initializes or loads existing persistent ChromaDB index."""
        if self.persist_dir.exists() and any(self.persist_dir.iterdir()):
            print(f"[RAG] Loading existing ChromaDB from {self.persist_dir}")
            self.vector_store = Chroma(
                persist_directory=str(self.persist_dir),
                embedding_function=self.embeddings
            )
        else:
            print(f"[RAG] No existing vector store found. Ingesting from {self.docs_dir}...")
            self.build_index()

    def build_index(self):
        """Loads runbook Markdown/PDF files, chunks them, and builds ChromaDB vector store."""
        if not self.docs_dir.exists():
            raise FileNotFoundError(f"Runbooks directory '{self.docs_dir}' does not exist.")

        raw_docs = []
        # Support both Markdown/text and PDF SOP runbooks
        for filepath in self.docs_dir.glob("**/*"):
            if filepath.suffix.lower() in [".md", ".txt"]:
                loader = TextLoader(str(filepath), encoding="utf-8")
                raw_docs.extend(loader.load())
            elif filepath.suffix.lower() == ".pdf":
                loader = PyPDFLoader(str(filepath))
                raw_docs.extend(loader.load())

        if not raw_docs:
            print(f"[RAG Warning] No documents found in {self.docs_dir}.")
            return

        # Recursive semantic chunking preserving heading boundaries
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n## ", "\n### ", "\n\n", "\n", " "]
        )
        chunked_docs = splitter.split_documents(raw_docs)
        print(f"[RAG] Ingested {len(raw_docs)} documents into {len(chunked_docs)} chunks.")

        self.vector_store = Chroma.from_documents(
            documents=chunked_docs,
            embedding=self.embeddings,
            persist_directory=str(self.persist_dir)
        )
        print(f"[RAG] Successfully indexed and persisted to {self.persist_dir}")

    def query(self, query_text: str, top_k: int = 2) -> Dict[str, Any]:
        """
        Retrieves top-k most relevant SOP chunks with similarity scores
        and builds a strictly grounded prompt context.
        """
        if not self.vector_store:
            raise RuntimeError("Vector store not initialized. Call build_index() first.")

        # Similarity search with cosine distance
        results = self.vector_store.similarity_search_with_relevance_scores(query_text, k=top_k)
        
        retrieved_contexts = []
        for doc, score in results:
            retrieved_contexts.append({
                "source": Path(doc.metadata.get("source", "Unknown")).name,
                "relevance_score": round(float(score), 4),
                "content": doc.page_content.strip()
            })

        context_block = "\n\n---\n\n".join(
            [f"[{item['source']} | Confidence: {item['relevance_score']}]\n{item['content']}"
             for item in retrieved_contexts]
        )

        return {
            "query": query_text,
            "retrieved_contexts": retrieved_contexts,
            "context_prompt": context_block
        }


if __name__ == "__main__":
    rag = DataOpsRAG()
    sample_query = "How to resolve ORA-00060 deadlock on staging tables?"
    print(f"\n[Test Query]: {sample_query}\n")
    output = rag.query(sample_query, top_k=1)
    
    for idx, ctx in enumerate(output["retrieved_contexts"], 1):
        print(f"Match #{idx} from {ctx['source']} (Score: {ctx['relevance_score']}):")
        print(ctx["content"])