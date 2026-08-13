from typing import Generator
from langchain_groq import ChatGroq
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_chroma import Chroma
from config import CHROMA_PATH, EMBEDDING_MODEL, LLM_MODEL

def query_rag_pipeline(user_query: str, user_role: str) -> Generator[str, None, None]:
    """Retrieves role-specific context using ChromaDB metadata filters and streams LLM response chunks."""
    
    embeddings = SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL)
    
    vectorstore = Chroma(
        persist_directory=CHROMA_PATH, 
        embedding_function=embeddings
    )
    
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": 4,
            "filter": {"allowed_role": user_role.lower()}
        }
    )
    
    docs = retriever.invoke(user_query)
    context = "\n\n".join([doc.page_content for doc in docs])
    
    if not context:
        yield "I couldn't find any relevant documents authorized for your role."
        return

    prompt = ChatPromptTemplate.from_template(
        "You are an AI Assistant. Answer the question based ONLY on the provided context.\n\n"
        "Context:\n{context}\n\n"
        "Question: {question}"
    )
    
    llm = ChatGroq(model=LLM_MODEL, temperature=0, streaming=True)
    chain = prompt | llm | StrOutputParser()
    
    yield from chain.stream({"context": context, "question": user_query})