import os
import json
import time
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Load environment variables
load_dotenv()
pinecone_api_key = os.getenv("PINECONE_API_KEY")
gemini_api_key = os.getenv("GEMINI_API_KEY")

if not pinecone_api_key or not gemini_api_key:
    raise ValueError("Missing PINECONE_API_KEY or GEMINI_API_KEY in .env file.")

def index_data():
    input_path = "data/structured_reviews.json"
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Missing {input_path}. Run 2_process_reviews.py first.")
        
    with open(input_path, "r", encoding="utf-8") as f:
        reviews = json.load(f)
        
    # Initialize Pinecone
    print("Initializing Pinecone client...")
    pc = Pinecone(api_key=pinecone_api_key)
    
    index_name = "google-photos-discovery-v3"
    dimension = 3072 # Standard dimension for gemini-embedding-001
    
    # Check if index exists, create if not
    existing_indexes = [index_info["name"] for index_info in pc.list_indexes()]
    if index_name not in existing_indexes:
        print(f"Creating Pinecone index '{index_name}'...")
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
        # Wait for index to be ready
        while not pc.describe_index(index_name).status['ready']:
            time.sleep(1)
            
    print(f"Index '{index_name}' is ready.")
    index = pc.Index(index_name)
    
    # Clear the index if it exists (for a fresh run)
    try:
        index.delete(delete_all=True)
        time.sleep(2) # Give it a moment to clear
    except Exception as e:
        print(f"Delete all failed/skipped: {e}")
    
    # Initialize Embeddings
    print("Initializing Google Gemini Embeddings...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    
    # Prepare data for upsert
    print(f"Generating embeddings and indexing {len(reviews)} reviews...")
    vectors = []
    
    for i, review in enumerate(reviews):
        # We want to embed the original text along with the structured context
        text_to_embed = f"""
        User Review: {review['original_text']}
        Memory Anchors: {review['remembered_anchors']}
        Forgotten Elements: {review['forgotten_elements']}
        Opportunity Area: {review['opportunity_area']}
        """
        
        # Generate embedding
        vector_vals = embeddings.embed_query(text_to_embed)
        
        # Prepare metadata (can't have nested dicts or complex types in pinecone metadata easily, keep it flat)
        metadata = {
            "original_text": review['original_text'],
            "photo_type": review['photo_type'],
            "opportunity_area": review['opportunity_area'],
            "summary": review['summary'],
            "rating": review['rating'],
            "source": review['source'],
            "source_url": review.get('source_url', '')
        }
        
        vectors.append({
            "id": f"review_{i}",
            "values": vector_vals,
            "metadata": metadata
        })
        
    # Batch upsert
    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i+batch_size]
        index.upsert(vectors=batch)
        print(f"Upserted batch {i} to {i+len(batch)}")
        
    print("Indexing complete! Data is ready for RAG.")

if __name__ == "__main__":
    index_data()
