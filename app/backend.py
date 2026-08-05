import os
from typing import Generator
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import TextLoader, CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

# Constants
CHROMA_PATH = "./chroma_db"
DATA_DIR = "./resources/data"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# -------------------------------------------------------------------
# 1. Document Ingestion Pipeline
# -------------------------------------------------------------------
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

    # Iterate through folder structure in resources/data/
    for dept_folder in os.listdir(DATA_DIR):
        dept_path = os.path.join(DATA_DIR, dept_folder)
        
        if os.path.isdir(dept_path):
            role_tag = dept_folder.lower()  # Folder name (e.g., 'engineering', 'finance', 'general')

            for root, _, files in os.walk(dept_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    docs = []

                    # Process Markdown / Text files
                    if file.endswith(".md"):
                        loader = TextLoader(file_path, encoding="utf-8")
                        raw_docs = loader.load()
                        docs = text_splitter.split_documents(raw_docs)

                    # Process CSV files
                    elif file.endswith(".csv"):
                        loader = CSVLoader(file_path)
                        docs = loader.load()

                    # Attach RBAC Metadata as scalar tags
                    for doc in docs:
                        if role_tag == "general":
                            allowed = ["employee", "c-levelexecutives", "engineering", "finance", "hr", "marketing"]
                        else:
                            allowed = [role_tag, "c-levelexecutives"]

                        # Create a chunk record for each allowed role
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
        # Build vector store with indexed chunks
        Chroma.from_documents(
            documents=all_chunks,
            embedding=embeddings,
            persist_directory=CHROMA_PATH
        )
        print(f"Successfully indexed {len(all_chunks)} chunks into ChromaDB!")

# -------------------------------------------------------------------
# 2. RAG Query Pipeline (Streamed)
# -------------------------------------------------------------------
def query_rag_pipeline(user_query: str, user_role: str) -> Generator[str, None, None]:
    """Retrieves role-specific context using ChromaDB metadata filters and streams LLM response chunks."""
    
    embeddings = SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL)
    
    # Connect to persistent Chroma database
    vectorstore = Chroma(
        persist_directory=CHROMA_PATH, 
        embedding_function=embeddings
    )
    
    # Filter documents where user's role exists inside 'allowed_role' metadata
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": 4,
            "filter": {"allowed_role": user_role.lower()}
        }
    )
    
    # Retrieve authorized documents
    docs = retriever.invoke(user_query)
    context = "\n\n".join([doc.page_content for doc in docs])
    
    if not context:
        yield "I couldn't find any relevant documents authorized for your role."
        return

    # Prompt Setup
    prompt = ChatPromptTemplate.from_template(
        "You are an AI Assistant. Answer the question based ONLY on the provided context.\n\n"
        "Context:\n{context}\n\n"
        "Question: {question}"
    )
    
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0, streaming=True)
    chain = prompt | llm | StrOutputParser()
    
    # Yield tokens as they are generated
    yield from chain.stream({"context": context, "question": user_query})


# Execute ingestion once on script run if ChromaDB directory doesn't exist
if __name__ == "__main__":
    if not os.path.exists(CHROMA_PATH):
        print("Initializing ChromaDB ingestion...")
        ingest_documents()
    else:
        print("ChromaDB already exists. Ready to query!")