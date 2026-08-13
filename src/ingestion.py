import os
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import TextLoader, CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import CHROMA_PATH, DATA_DIR, EMBEDDING_MODEL

def ingest_documents():
    """
    Scans resources/data subdirectories, processes .md and .csv files,
    attaches role-based metadata, and populates ChromaDB.
    """
    embeddings = SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    all_chunks = []

    if not os.path.exists(DATA_DIR):
        print(f"Directory {DATA_DIR} not found. Skipping ingestion.")
        return

    for dept_folder in os.listdir(DATA_DIR):
        dept_path = os.path.join(DATA_DIR, dept_folder)
        
        if os.path.isdir(dept_path):
            role_tag = dept_folder.lower()

            for root, _, files in os.walk(dept_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    docs = []

                    if file.endswith(".md"):
                        loader = TextLoader(file_path, encoding="utf-8")
                        raw_docs = loader.load()
                        docs = text_splitter.split_documents(raw_docs)

                    elif file.endswith(".csv"):
                        loader = CSVLoader(file_path)
                        docs = loader.load()

                    for doc in docs:
                        if role_tag == "general":
                            allowed = ["employee", "clevelexecutive", "engineering", "finance", "hr", "marketing"]
                        else:
                            allowed = [role_tag, "clevelexecutive"]

                        for role in allowed:
                            chunk_copy = doc.model_copy(
                                update={
                                    "metadata": {
                                        **doc.metadata,
                                        "allowed_role": role,
                                        "department": role_tag,
                                    }
                                }
                            )
                            all_chunks.append(chunk_copy)

    if all_chunks:
        Chroma.from_documents(
            documents=all_chunks,
            embedding=embeddings,
            persist_directory=CHROMA_PATH
        )
        print(f"Successfully indexed {len(all_chunks)} chunks into ChromaDB!")

if __name__ == "__main__":
    if not os.path.exists(CHROMA_PATH):
        print("Initializing ChromaDB ingestion...")
        ingest_documents()
    else:
        print("ChromaDB already exists. Ready to query!")