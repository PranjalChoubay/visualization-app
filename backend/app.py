import os
import json
import pickle
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import google.generativeai as genai
from sklearn.metrics.pairwise import cosine_similarity
import logging

# ---- Logging ----
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Load environment
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Flask app
app = Flask(__name__)
CORS(app)

# ---- File paths ----
CHAT_FILE = "whatsapp_chat_rohan_full.json"
VECTOR_STORE = "vector_store.pkl"

# ---- Current user metadata ----
current_user = {
    "name": "Rohan",
    "team": "Elyx",
    "side": "right"
}

# ---- Embedding helper ----
def get_embedding(text: str):
    try:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text
        )
        return np.array(result["embedding"], dtype=np.float32)
    except Exception as e:
        logging.error(f"Embedding failed: {e}")
        return np.zeros((768,), dtype=np.float32)  # fallback dimension for safety

# ---- Build embeddings & save to pickle ----
def build_vector_store():
    global vectors, texts, metadata
    
    if not os.path.exists(CHAT_FILE):
        logging.error(f"Chat file '{CHAT_FILE}' not found.")
        return False

    try:
        with open(CHAT_FILE, "r", encoding="utf-8") as f:
            messages = json.load(f)
    except Exception as e:
        logging.error(f"Failed to load chat JSON: {e}")
        return False

    texts, embeddings, metadata = [], [], []
    for msg in messages:
        text = f"{msg['name']}: {msg['text']}"
        emb = get_embedding(text)
        texts.append(text)
        embeddings.append(emb)
        metadata.append({"timestamp": msg.get("time", ""), "side": msg.get("side", "")})

    vectors = np.vstack(embeddings)

    with open(VECTOR_STORE, "wb") as f:
        pickle.dump((vectors, texts, metadata), f)

    logging.info(f"✅ Vector store built with {len(texts)} messages.")
    return True

# ---- Load vector store ----
# Initialize variables first
vectors = np.array([])
texts = []
metadata = []

if not os.path.exists(VECTOR_STORE):
    logging.info("Vector store missing — building...")
    success = build_vector_store()
    if not success:
        logging.warning("Failed to build vector store, using empty arrays")
else:
    logging.info("Vector store found — loading...")
    try:
        with open(VECTOR_STORE, "rb") as f:
            loaded_vectors, loaded_texts, loaded_metadata = pickle.load(f)
            vectors = loaded_vectors
            texts = loaded_texts
            metadata = loaded_metadata
    except Exception as e:
        logging.error(f"Failed to load vector store: {e}")
        logging.warning("Using empty arrays due to load failure")

# Ensure vectors is always a numpy array
if not isinstance(vectors, np.ndarray):
    vectors = np.array([])
if not isinstance(texts, list):
    texts = []
if not isinstance(metadata, list):
    metadata = []

# Log the final state
logging.info(f"Vector store initialized - vectors: {vectors.shape if vectors is not None else 'None'}, texts: {len(texts)}, metadata: {len(metadata)}")

# ---- Routes ----
@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Backend running with pickle-based RAG!"})

@app.route("/status", methods=["GET"])
def status():
    """Get the current status of the vector store"""
    try:
        vector_count = len(vectors) if vectors is not None else 0
        text_count = len(texts) if texts is not None else 0
        metadata_count = len(metadata) if metadata is not None else 0
        
        return jsonify({
            "status": "success",
            "vector_store": {
                "vectors_shape": vectors.shape if vectors is not None else None,
                "vector_count": vector_count,
                "text_count": text_count,
                "metadata_count": metadata_count,
                "has_vector_store_file": os.path.exists(VECTOR_STORE),
                "has_chat_file": os.path.exists(CHAT_FILE)
            }
        })
    except Exception as e:
        logging.error(f"Status check failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/rebuild", methods=["POST"])
def rebuild_vector_store():
    """Force rebuild the vector store from the current JSON file"""
    try:
        success = build_vector_store()
        if success:
            # Reload the vectors into memory
            global vectors, texts, metadata
            with open(VECTOR_STORE, "rb") as f:
                vectors, texts, metadata = pickle.load(f)
            return jsonify({"status": "success", "message": f"Vector store rebuilt with {len(texts)} messages"})
        else:
            return jsonify({"status": "error", "message": "Failed to rebuild vector store"}), 500
    except Exception as e:
        logging.error(f"Rebuild failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/ask", methods=["POST"])
def ask():
    try:
        # Check if vector store is available
        if vectors is None or len(vectors) == 0:
            logging.warning("Vector store is empty or None")
            return jsonify({"error": "Vector store not available. Please rebuild."}), 500

        data = request.get_json(force=True)
        question = data.get("question", "")
        if not question.strip():
            return jsonify({"error": "No question provided"}), 400

        # Embed question
        q_emb = get_embedding(question).reshape(1, -1)
        
        # Validate vectors shape
        if vectors.shape[1] != q_emb.shape[1]:
            logging.error(f"Vector dimension mismatch: vectors shape {vectors.shape}, question embedding shape {q_emb.shape}")
            return jsonify({"error": "Vector store dimension mismatch. Please rebuild."}), 500

        # Find most similar messages
        sims = cosine_similarity(q_emb, vectors).flatten()
        top_idx = np.argsort(sims)[::-1][:5]

        snippets = []
        for i in top_idx:
            if sims[i] > 0.45:  # threshold for relevance
                if i < len(metadata) and i < len(texts):
                    snippets.append(f"[{metadata[i]['timestamp']}] {texts[i]}")
                else:
                    logging.warning(f"Index {i} out of bounds for metadata/texts")

        # ---- Inject user awareness ----
        user_context = f"""
        The current user is {current_user['name']}, 
        who is a member of the {current_user['team']} team. 
        In past conversations, this user always corresponds to messages with side='{current_user['side']}'.
        """

        # Build prompt for Gemini
        if snippets:
            context_text = "\n".join(snippets)
            prompt = f"""
            You are a helpful assistant. You have access to the user's past conversations.

            {user_context}

            Rules:
            1. If the past snippets are useful, include them in your answer. 
            2. Wrap them inside [PAST_CONTEXT] ... [/PAST_CONTEXT] so the frontend can render separately.
            3. If they are not enough to fully answer, combine them with your own reasoning.
            4. Do not overuse exact timestamps. Instead, rephrase them naturally (e.g., 'earlier this year').

            Conversation Snippets:
            {context_text}

            User's Question: {question}
            """
        else:
            prompt = f"""
            You are a helpful assistant. 

            {user_context}

            The user asked: {question}
            No relevant past conversation was found, so answer using your own knowledge.
            """

        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            answer = response.text.strip()
        except Exception as e:
            logging.error(f"Gemini generation failed: {e}")
            answer = "⚠️ Sorry, I had trouble generating a response."

        return jsonify({"answer": answer})
        
    except Exception as e:
        logging.error(f"Unexpected error in /ask endpoint: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

# ---- Run ----
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
