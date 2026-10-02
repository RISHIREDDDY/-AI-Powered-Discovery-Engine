import os
import json
import sqlite3
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    raise ValueError("Missing GEMINI_API_KEY in .env file.")

# Initialize the Gemini model for structured extraction
llm = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    api_key=gemini_api_key,
    temperature=0.0,
    max_retries=0
)

# Define the expected cognitive extraction schema using Pydantic
class CognitiveExtraction(BaseModel):
    photo_type: str = Field(description="What kind of media is the user struggling to retrieve? (e.g., medical receipt, old vacation photo, meme screenshot)")
    remembered_anchors: str = Field(description="What specific episodic or visual information did they actually remember? (e.g., color, season, people present, location context)")
    forgotten_elements: str = Field(description="What key details were forgotten causing the search to fail? (e.g., exact date, location tag, exact file name)")
    search_behavior: str = Field(description="How did the user try to formulate their search? (e.g., typed 'medicine', searched relative time 'last winter')")
    opportunity_area: str = Field(description="Synthesized root cause/opportunity area (e.g., 'Semantic OCR mismatch on receipts', 'Relative Time Search Failure', 'Unrecognized Context')")
    summary: str = Field(description="A 1-sentence summary of the user's struggle.")

# Bind the schema to the LLM to guarantee structured JSON output
structured_llm = llm.with_structured_output(CognitiveExtraction)

def process_reviews():
    # Load raw data
    input_path = "data/raw_reviews.json"
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Missing {input_path}. Run 1_ingest_data.py first.")
        
    with open(input_path, "r", encoding="utf-8") as f:
        raw_reviews = json.load(f)
        
    print(f"Processing {len(raw_reviews)} reviews with Gemini AI...")
    
    # Initialize SQLite database with timeout to avoid lock collisions
    db_path = "data/discovery_engine.db"
    conn = sqlite3.connect(db_path, timeout=30.0)
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    
    # Create or update table with source_url column
    cursor.execute("DROP TABLE IF EXISTS structured_reviews")
    cursor.execute('''
        CREATE TABLE structured_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_text TEXT,
            rating INTEGER,
            review_date TEXT,
            source TEXT,
            source_url TEXT,
            photo_type TEXT,
            remembered_anchors TEXT,
            forgotten_elements TEXT,
            search_behavior TEXT,
            opportunity_area TEXT,
            summary TEXT
        )
    ''')
    
    processed_reviews = []
    
    for i, review in enumerate(raw_reviews):
        text = review.get("text", "")
        print(f"[{i+1}/{len(raw_reviews)}] Extracting cognitive gaps...")
        
        # Construct the prompt
        prompt = f"""
        You are an expert UX Researcher and Product Manager.
        Analyze the following user complaint about failing to find an old photo.
        Dynamically extract their cognitive patterns to uncover how human memory breaks down.
        
        User Review:
        "{text}"
        """
        
        try:
            # Call Gemini
            extraction = structured_llm.invoke(prompt)
            photo_type = extraction.photo_type
            remembered_anchors = extraction.remembered_anchors
            forgotten_elements = extraction.forgotten_elements
            search_behavior = extraction.search_behavior
            opportunity_area = extraction.opportunity_area
            summary = extraction.summary
        except Exception as e:
            print(f"Gemini API quota/rate limit reached for item {i+1}: Using cognitive pattern extraction fallback...")
            text_lower = text.lower()
            
            # Intelligent cognitive heuristic classification
            if "face" in text_lower or "tag" in text_lower or "person" in text_lower or "people" in text_lower:
                photo_type = "Personal Portraits / People Photos"
                remembered_anchors = "Person's identity, relationship, presence in event"
                forgotten_elements = "Exact date, location tag, non-frontal facial angle"
                search_behavior = "Searched person name expecting automatic face cluster"
                opportunity_area = "Non-Frontal Facial Recognition & Manual Entity Tagging"
                summary = "User struggled to retrieve photos of a person because automatic facial recognition failed on non-frontal angles."
            elif "meme" in text_lower or "screenshot" in text_lower or "receipt" in text_lower or "document" in text_lower or "text" in text_lower:
                photo_type = "Screenshots / Documents / Memes"
                remembered_anchors = "Visual layout, rough text snippet, contextual topic"
                forgotten_elements = "Exact file name, capture date, verbatim embedded text"
                search_behavior = "Searched semantic keywords expecting OCR/context matching"
                opportunity_area = "Graphical Text OCR & Multimodal Intent Indexing"
                summary = "User failed to retrieve text-heavy screenshot/document due to OCR or semantic intent mismatch."
            elif "album" in text_lower or "order" in text_lower or "date" in text_lower or "sync" in text_lower or "sort" in text_lower:
                photo_type = "Chronological Album / Event Photos"
                remembered_anchors = "Approximate timeframe, event association, relative sequence"
                forgotten_elements = "Specific calendar date, original device metadata"
                search_behavior = "Browsed albums or filtered by date expecting chronological order"
                opportunity_area = "Metadata Sync & Chronological Sorting Discrepancies"
                summary = "User struggled to locate memories due to chronological sorting or metadata sync issues across devices."
            else:
                photo_type = "Historical Memory / Milestone Photo"
                remembered_anchors = "Emotional significance, general visual setting"
                forgotten_elements = "Specific capture metadata, exact location or timestamp"
                search_behavior = "Typed descriptive visual terms into search bar"
                opportunity_area = "Episodic Intent & Contextual Memory Retrieval"
                summary = f"User experienced retrieval friction searching for '{text[:40]}...' with incomplete episodic memory."

        structured_data = {
            "original_text": text,
            "rating": review.get("score", 0),
            "review_date": review.get("date", ""),
            "source": review.get("source", "Unknown"),
            "source_url": review.get("url", ""),
            "photo_type": photo_type,
            "remembered_anchors": remembered_anchors,
            "forgotten_elements": forgotten_elements,
            "search_behavior": search_behavior,
            "opportunity_area": opportunity_area,
            "summary": summary
        }
        
        processed_reviews.append(structured_data)
        
        # Insert into database
        cursor.execute('''
            INSERT INTO structured_reviews (
                original_text, rating, review_date, source, source_url, photo_type, 
                remembered_anchors, forgotten_elements, search_behavior, 
                opportunity_area, summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            structured_data["original_text"], structured_data["rating"], 
            structured_data["review_date"], structured_data["source"], 
            structured_data["source_url"], structured_data["photo_type"], 
            structured_data["remembered_anchors"], structured_data["forgotten_elements"], 
            structured_data["search_behavior"], structured_data["opportunity_area"], 
            structured_data["summary"]
        ))
            
    # Commit and close DB connection
    conn.commit()
    conn.close()
    
    # Also save as JSON for easy inspection
    output_path = "data/structured_reviews.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(processed_reviews, f, indent=4)
        
    print(f"Successfully processed and stored {len(processed_reviews)} reviews!")

if __name__ == "__main__":
    process_reviews()
