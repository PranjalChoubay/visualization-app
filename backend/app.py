import os
import pickle
import numpy as np
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import google.generativeai as genai
from sklearn.metrics.pairwise import cosine_similarity

# ------------------ Setup ------------------
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)

# ------------------ Globals ------------------
embeddings = None
vectors = None
texts = None
VECTOR_FILE = "vector_store.pkl"

current_user = {
    "name": "Rohan",
    "team": "Fitness",
    "side": "left"
}

# ------------------ Utils ------------------
def get_embedding(text):
    """Generate embedding for a given text."""
    model = genai.embed_content(
        model="models/embedding-001",
        content=text
    )
    return np.array(model['embedding'])

def load_vector_store():
    """Load precomputed embeddings and texts if available."""
    global embeddings, vectors, texts
    try:
        with open(VECTOR_FILE, "rb") as f:
            data = pickle.load(f)
            embeddings = data["embeddings"]
            texts = data["texts"]
            vectors = np.array(embeddings)
            logging.info("Vector store loaded successfully")
    except Exception as e:
        logging.error(f"Failed to load vector store: {e}")
        embeddings, vectors, texts = [], None, []

def save_vector_store():
    """Save embeddings and texts to file."""
    global embeddings, texts
    try:
        with open(VECTOR_FILE, "wb") as f:
            pickle.dump({"embeddings": embeddings, "texts": texts}, f)
        logging.info("Vector store saved successfully")
    except Exception as e:
        logging.error(f"Failed to save vector store: {e}")

# ------------------ Routes ------------------
@app.route("/ask", methods=["POST"])
def ask():
    if vectors is None or len(vectors) == 0:
        return jsonify({"error": "Vector store not available. Please rebuild."}), 500

    data = request.get_json(force=True)
    question = data.get("question", "")
    if not question.strip():
        return jsonify({"error": "No question provided"}), 400

    # Embed question
    q_emb = get_embedding(question).reshape(1, -1)

    # Find most similar messages
    sims = cosine_similarity(q_emb, vectors).flatten()
    top_idx = np.argsort(sims)[::-1][:5]

    snippets = []
    for i in top_idx:
        if sims[i] > 0.45:  # threshold for relevance
            snippets.append(f"{texts[i]}")

    # ---- Inject user awareness ----
    user_context = f"""
    The current user is {current_user['name']}, 
    who is a member of the {current_user['team']} team. 
    In past conversations, this user always corresponds to messages with side='{current_user['side']}'.
    """

    # Build prompt for Gemini
    context_text = "\n".join(snippets) if snippets else ""
    if snippets:
        prompt = f"""
        You are a helpful assistant. You have access to the user's past conversations.

        {user_context}

        Rules:
        1. Use the past snippets if relevant.
        2. Provide a clear answer for the new question.
        3. Do not just repeat snippets, but integrate them naturally.

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

    return jsonify({
        "answer": answer,
        "past_context": snippets if snippets else []
    })

@app.route("/upload", methods=["POST"])
def upload_image():
    """Upload an image, extract text using Gemini Vision, and store embeddings."""
    global embeddings, texts, vectors

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    try:
        # Save temporarily
        filepath = os.path.join("uploads", file.filename)
        os.makedirs("uploads", exist_ok=True)
        file.save(filepath)

        # Use Gemini Vision to extract text
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            ["Extract all readable text from this chat screenshot.", {"image": filepath}]
        )
        extracted_text = response.text.strip()

        # Embed and store
        if extracted_text:
            emb = get_embedding(extracted_text)
            if embeddings is None:
                embeddings, texts = [], []
            embeddings.append(emb)
            texts.append(extracted_text)
            vectors = np.array(embeddings)
            save_vector_store()

        return jsonify({"message": "Image processed successfully", "extracted_text": extracted_text})
    except Exception as e:
        logging.error(f"Image processing failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

# ------------------ Init ------------------
if __name__ == "__main__":
    load_vector_store()
    app.run(host="0.0.0.0", port=5000)
