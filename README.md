# **ContextGuard** : Role-Based Access Control (RBAC) RAG System

An intelligent, secure retrieval-augmented generation (RAG) system built with **LangChain**, **Groq** (llama-3.3-70b-versatile), **ChromaDB**, and **Streamlit**. The application enforces strict Role-Based Access Control (RBAC) on company documents, ensuring users can only query information authorized for their specific organizational role. Full observability, run tracking, and chain monitoring are integrated via **LangSmith**.

## **Problem Background**

**FinSolve Technologies**, a leading FinTech company, was experiencing communication delays and fragmented document access across teams like Finance, HR, Marketing, Engineering, and C-Level Executives. These issues led to slower decision-making and operational inefficiencies, as teams lacked a centralized, secure way to access internal knowledge specific to their roles.

## **Solution Overview**

To address this issue, an internal AI chatbot was developed using Retrieval Augmented Generation (RAG) and Role-Based Access Control (RBAC). It ensures that every user receives accurate, secure, and role-relevant information instantly.

This chatbot solves FinSolve's data access problem using:

- **RAG (Retrieval-Augmented Generation)** via LLaMA model
- **Role-Based Filtering** at the vector search level
- **Streamlit** for interactive chat and login
- **Documents** stored per department with metadata

## **Features**

* **Role-Based Document Filtering**: Automatically processes Markdown (.md) and CSV files across department directories, tagging chunks with scalar metadata (allowed_role) to restrict retrieval based on user authorization.

* **Full Observability & Tracing**: Native LangSmith integration to monitor LLM generation latency, track retrieval performance, debug document routing, and log user chat interactions.

* **User Authentication & Session Management**: SQLite-backed authentication system handling secure logins, role assertions, and session state retention.

* **Streaming RAG Pipeline**: Low-latency, real-time token streaming powered by ChatGroq (llama-3.3-70b-versatile) and LangChain Runnable chains.

* **Interactive Streamlit UI**: User-friendly chat interface displaying role attributes, login forms, interactive session clearing, and live response rendering.

## **Tech Stack**

| Layer                        | Tool/Library                          |
|------------------------------|---------------------------------------|
| Frontend                     | Streamlit                             |
| Orchestration                | LangChain Core                        |
| Observability & Evaluation   | LangSmith                             |
| LLM Provider                 | Groq (llama-3.3-70b-versatile)        |
| Vector DB                    | ChromaDB (langchain-chroma / Chroma)  |
| Embedding Model              | HuggingFace (all-MiniLM-L6-v2)        |
| Authentication & Users       | SQLite (users.db)                     |

## **Setup Instructions**

### 1. Clone the Repository
```bash
git clone https://github.com/VishwarajsinhKher100/ContextGuard.git
```

### 2. Create Virtual Environment
```bash
uv venv
```

#### Activate the virtual environment:

```bash
.venv\Scripts\activate     # On Windows
# OR
source .venv/bin/activate  # On Linux/macOS:
```

### 3. Install Dependencies

```bash
uv sync
```

### 4. Configure Environment Variables

Create a .env file in the project root:

```bash
GROQ_API_KEY=your_groq_api_key_here

# LangSmith Configuration
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=OmniRAG
```

### 5. Running the Application

Launch the Streamlit web application:

```bash
streamlit run app/frontend.py
```

## **Query Samples**

1. Give me a summary about system architecture --  Engg
2. Give me the details of employees in Data department whose performance rating is 5 -- HR 
3. What percentage of the Vendor Services expense was allocated to marketing-related activities? -- finance
4. What is the Return on Investment (ROI) for FinSolve Technologies? -- finance 
5. Give me details about leave policies. -- General
6. What was the percentage increase in FinSolve Technologies's net income in 2024? - Finance