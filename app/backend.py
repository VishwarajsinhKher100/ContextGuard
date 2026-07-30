from langchain_community.vectorstores import Chroma
from langchain_groq import ChatGroq
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv()

# RAG Helper Function
def query_rag_pipeline(user_query: str, user_role: str) -> str:
    """Retrieves role-specific context and generates an LLM response."""
    
    # Connect to your existing vector DB
    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = Chroma(
        persist_directory="./chroma_db", 
        embedding_function=embeddings
    )
    
    # Filter documents where metadata 'role' matches the authenticated user's role
    retriever = vectorstore.as_retriever(
        search_kwargs={
            "k": 3,
            "filter": {"role": user_role}  # ContextGuard RBAC Filter
        }
    )
    
    # Retrieve relevant documents
    docs = retriever.invoke(user_query)
    context = "\n\n".join([doc.page_content for doc in docs])
    
    if not context:
        return "I couldn't find any relevant documents authorized for your role."

    # Generate response
    prompt = ChatPromptTemplate.from_template(
        "You are an AI Assistant. Answer the question based ONLY on the provided context.\n\n"
        "Context:\n{context}\n\n"
        "Question: {question}"
    )
    
    llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)
    chain = prompt | llm | StrOutputParser()
    
    return chain.invoke({"context": context, "question": user_query})

# Example documents with metadata tags matching user roles
docs = [
    Document(page_content="Engineering roadmap: Migrating microservices to Kubernetes in Q3.", metadata={"role": "engineering"}),
    Document(page_content="Q2 Marketing campaign budget is capped at $50,000 for ad spend.", metadata={"role": "marketing"}),
    Document(page_content="Finance report: Net revenue increased by 14% year-over-year.", metadata={"role": "finance"}),
    Document(page_content="HR Policy: Employees receive 20 days of paid leave per year.", metadata={"role": "hr"}),
]

vectorstore = Chroma.from_documents(
    documents=docs,
    embedding=SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2"),
    persist_directory="./chroma_db"
)