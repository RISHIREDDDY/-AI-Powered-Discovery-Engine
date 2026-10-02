# AI-Powered Discovery Engine Architecture

## 1. System Overview
This architecture outlines the AI-powered product discovery engine designed to analyze user feedback regarding Google Photos retrieval challenges. It focuses on identifying what users remember, what they forget, and where current search capabilities break down.

## 2. Tool Stack & Configuration

| Component | Tool | Role | Configuration / API Key |
| :--- | :--- | :--- | :--- |
| **Data Ingestion** | **Apify** | Scrape reviews from Google Play Store, App Store, and Reddit. | `YOUR_APIFY_API_KEY` |
| **Vector Search (RAG)** | **Pinecone** | Cloud vector database for semantic search over user complaints. | `YOUR_PINECONE_API_KEY` |
| **AI Reasoning** | **Google Gemini** | Extract cognitive memory anchors, information gaps, and retrieval failures. | `YOUR_GEMINI_API_KEY` |
| **Relational Storage** | **SQLite** | Local structured storage for raw reviews, metadata, and tags. | Local DB File |
| **Orchestration** | **LangChain** | Connects the LLM, Pinecone vector store, and SQLite database. | Python Library |
| **PM UI Dashboard** | **Streamlit** | Interactive interface for PMs to explore the 4 core questions. | Python Library |
| **Data Visualization**| **Plotly** | Renders interactive charts and opportunity comparison matrices. | Python Library |

## 3. Data Pipeline & Workflow

### Phase 1: Ingestion
- LangChain triggers Apify Actors to scrape publicly available discussions and reviews.
- Raw text data is ingested and batched for processing.

### Phase 2: Processing & Reasoning
- Batches of text are sent to the Google Gemini API.
- Gemini returns structured JSON mapping the cognitive elements (Target Photo Type, Remembered Anchors, Forgotten Elements, Failure Patterns).

### Phase 3: Storage & Indexing
- Structured records and metadata are persisted in the **SQLite** database.
- Text embeddings are generated and stored in **Pinecone** to enable semantic similarity search (RAG).

### Phase 4: Discovery & UI
- The **Streamlit** application connects to both SQLite (for aggregated metrics) and Pinecone (for semantic search).
- **Plotly** renders charts showing retrieval problem distributions.
- Product Managers can interactively explore the dashboard to uncover evidence-backed opportunity areas.
