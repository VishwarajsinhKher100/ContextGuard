"""Document Ingestion and Vector Store Pipeline.

This module processes raw document files (.md, .csv) organized in department-level
directory trees, enriches them with Role-Based Access Control (RBAC) metadata tags,
and populates a local ChromaDB collection using HuggingFace BGE embeddings.
"""

import os
import logging
from typing import List, Optional
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader, CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# Set up standard logging to avoid using bare print statements in production
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Global Configuration Parameters
CHROMA_PATH: str = "./chroma_db"
DATA_DIR: str = "./resources/data"

# Choose BGE Model:
# - "BAAI/bge-m3" (8192 context window, 1024-dim, multilingual/multi-function)
# - "BAAI/bge-base-en-v1.5" (512 context window, 768-dim, lightweight English)
EMBEDDING_MODEL: str = "BAAI/bge-m3"
COLLECTION_NAME: str = "enterprise_knowledge_base"
BATCH_SIZE: int = 128  # Slightly smaller batch size for larger high-dim BGE embeddings


def process_file(
    file_path: str, 
    text_splitter: RecursiveCharacterTextSplitter
) -> List[Document]:
    """Loads and splits a document based on its extension type.

    Args:
        file_path (str): Absolute or relative filesystem path to the file.
        text_splitter (RecursiveCharacterTextSplitter): Configured text splitter instance.

    Returns:
        List[Document]: A list of loaded and chunked LangChain Document objects.
            Returns an empty list if loading fails or file format is unsupported.
    """
    docs: List[Document] = []
    try:
        if file_path.endswith(".md"):
            # Enforce UTF-8 to prevent cross-platform file encoding corruption
            loader = TextLoader(file_path, encoding="utf-8")
            raw_docs = loader.load()
            docs = text_splitter.split_documents(raw_docs)
            
        elif file_path.endswith(".csv"):
            # CSV loader inherently converts row items into structured document units
            loader = CSVLoader(file_path, encoding="utf-8")
            docs = loader.load()
            
    except Exception as err:
        logging.error("Failed to parse document at %s: %s", file_path, str(err))

    return docs


def ingest_documents(
    data_dir: str = DATA_DIR, 
    chroma_path: str = CHROMA_PATH, 
    model_name: str = EMBEDDING_MODEL
) -> None:
    """Scans local directories, parses files, attaches RBAC metadata, and populates ChromaDB."""
    if not os.path.exists(data_dir):
        logging.warning("Data directory '%s' does not exist. Halting ingestion.", data_dir)
        return

    # Configure BGE model parameters
    # Note: BGE models do not require passage prefixes during ingestion when using standard cosine similarity,
    # but encode_kwargs can be adjusted for GPU execution if available.
    model_kwargs = {"device": "cuda" if os.environ.get("USE_CUDA") else "cpu"}
    encode_kwargs = {"normalize_embeddings": True}  # BGE requires normalized embeddings for cosine similarity

    logging.info("Initializing embedding model: %s", model_name)
    embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )
    
    # BGE models handle larger contexts (bge-m3 supports 8k tokens; bge-base supports 512).
    # Increased chunk size to 1000 chars (~200-250 words) to provide richer enterprise context.
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    all_chunks: List[Document] = []

    # Iterate through top-level directories to establish department boundaries
    for dept_folder in os.listdir(data_dir):
        dept_path = os.path.join(data_dir, dept_folder)
        
        if os.path.isdir(dept_path):
            role_tag = dept_folder.lower()

            # Recursively walk subfolders inside department directories
            for root, _, files in os.walk(dept_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    docs = process_file(file_path, text_splitter)

                    # Determine RBAC role permissions
                    if role_tag == "general":
                        allowed_roles = ["employee", "c-levelexecutives", "engineering", "finance", "hr", "marketing"]
                    else:
                        allowed_roles = [role_tag, "c-levelexecutives"]

                    for doc in docs:
                        chunk_copy = doc.model_copy(
                            update={
                                "metadata": {
                                    **doc.metadata,
                                    "allowed_roles": ",".join(allowed_roles),
                                    "department": role_tag,
                                }
                            }
                        )
                        all_chunks.append(chunk_copy)

    if not all_chunks:
        logging.warning("No valid chunks generated from data directory.")
        return

    # Initialize Chroma vector store handle
    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=chroma_path
    )

    # Ingest in defined batch sizes
    total_chunks = len(all_chunks)
    logging.info("Indexing %d chunks into ChromaDB in batches of %d...", total_chunks, BATCH_SIZE)

    for i in range(0, total_chunks, BATCH_SIZE):
        batch = all_chunks[i : i + BATCH_SIZE]
        vector_store.add_documents(documents=batch)
        logging.info("Processed batch %d / %d", (i // BATCH_SIZE) + 1, ((total_chunks - 1) // BATCH_SIZE) + 1)

    logging.info("Successfully completed ingestion for collection '%s'.", COLLECTION_NAME)


if __name__ == "__main__":
    if not os.path.exists(CHROMA_PATH):
        logging.info("Starting initial document ingestion workflow...")
        ingest_documents()
    else:
        logging.info("Existing ChromaDB detected at '%s'. Ingestion skipped.", CHROMA_PATH)