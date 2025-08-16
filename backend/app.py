import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings
import google.generativeai as genai
from concurrent.futures import ThreadPoolExecutor
import logging

# Configure logging for production
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load local .env (optional, ignored on deployment platforms)
load_dotenv()

# Configure Gemini API
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    logger.error("GEMINI_API_KEY environment variable not set")
    raise ValueError("GEMINI_API_KEY environment variable is required")

genai.configure(api_key=gemini_api_key)

app = Flask(__name__)
CORS(app)

# ---- Setup ChromaDB ----
# Use in-memory client for Render (ephemeral filesystem)
try:
    # Try to use persistent client if possible (for local development)
    chroma_client = chromadb.PersistentClient(path="./chroma_data")
    logger.info("Using persistent ChromaDB client")
except Exception as e:
    logger.warning(f"Could not create persistent client: {e}")
    # Fallback to in-memory client for production
    chroma_client = chromadb.Client()
    logger.info("Using in-memory ChromaDB client")

collection = chroma_client.get_or_create_collection(name="conversation")

# ---- Preload Gemini model once ----
try:
    model = genai.GenerativeModel("gemini-1.5-flash")
    logger.info("Gemini model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load Gemini model: {e}")
    raise

# ---- Embedding helper ----
def get_embedding(text):
    try:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text
        )
        return result["embedding"]
    except Exception as e:
        logger.error(f"Failed to get embedding: {e}")
        raise

# ---- Load and embed messages in parallel ----
def load_and_embed():
    try:
        # Try to load from current directory first
        json_file_path = "whatsapp_chat_rohan_full.json"
        if not os.path.exists(json_file_path):
            # Try to load from parent directory (for Render deployment)
            json_file_path = "../whatsapp_chat_rohan_full.json"
            if not os.path.exists(json_file_path):
                raise FileNotFoundError("whatsapp_chat_rohan_full.json not found")

        with open(json_file_path, "r", encoding="utf-8") as f:
            messages = json.load(f)

        logger.info(f"Loaded {len(messages)} messages from {json_file_path}")

        def process_message(idx, msg):
            try:
                text = f"{msg['name']}: {msg['text']}"
                emb = get_embedding(text)
                return {
                    "id": str(idx),
                    "embedding": emb,
                    "document": text,
                    "metadata": {"timestamp": msg["time"], "side": msg["side"]}
                }
            except Exception as e:
                logger.error(f"Failed to process message {idx}: {e}")
                return None

        with ThreadPoolExecutor(max_workers=4) as executor:  # Reduced workers for production
            results = list(executor.map(lambda x: process_message(*x), enumerate(messages)))
        
        # Filter out failed results
        valid_results = [r for r in results if r is not None]
        
        if not valid_results:
            raise ValueError("No valid messages could be processed")

        # Clear existing collection before adding new data
        collection.delete(where={})
        
        collection.add(
            ids=[r["id"] for r in valid_results],
            embeddings=[r["embedding"] for r in valid_results],
            documents=[r["document"] for r in valid_results],
            metadatas=[r["metadata"] for r in valid_results]
        )
        
        logger.info(f"Successfully embedded {len(valid_results)} messages")
        
    except Exception as e:
        logger.error(f"Failed to load and embed messages: {e}")
        raise

# ---- Initialize embeddings if collection is empty ----
try:
    if len(collection.get()["ids"]) == 0:
        logger.info("Creating embeddings for the first time (parallelized)...")
        load_and_embed()
        logger.info("Embeddings created successfully")
    else:
        logger.info("Embeddings already exist — skipping embedding step.")
except Exception as e:
    logger.error(f"Failed to initialize embeddings: {e}")
    # Don't raise here - let the app start but log the error

# ---- Root route for testing ----
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "Flask backend is running!",
        "collection_size": len(collection.get()["ids"]) if collection else 0
    })

# ---- Health check endpoint for Render ----
@app.route("/health", methods=["GET"])
def health():
    try:
        # Test basic functionality
        collection_size = len(collection.get()["ids"]) if collection else 0
        return jsonify({
            "status": "healthy",
            "collection_size": collection_size,
            "gemini_configured": bool(gemini_api_key)
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

# ---- Ask endpoint ----
@app.route("/ask", methods=["POST"])
def ask():
    try:
        question = request.json.get("question", "").strip()
        if not question:
            return jsonify({"error": "No question provided"}), 400

        if not collection or len(collection.get()["ids"]) == 0:
            return jsonify({"error": "No conversation data available"}), 503

        q_emb = get_embedding(question)
        results = collection.query(query_embeddings=[q_emb], n_results=3)

        if not results["documents"] or not results["documents"][0]:
            return jsonify({"error": "No relevant conversation snippets found"}), 404

        snippets = []
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            snippets.append(f"[{meta['timestamp']}] {doc}")

        prompt = f"""
You are a helpful assistant.
Based ONLY on the following conversation snippets, answer the question.
Cite the timestamp for each fact you use.

Conversation Snippets:
{chr(10).join(snippets)}

Question: {question}
"""

        response = model.generate_content(prompt)

        return jsonify({"answer": response.text})

    except Exception as e:
        logger.error(f"Error in ask endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

# ---- Production server ----
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)
