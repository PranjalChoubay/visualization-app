import os
import json
import pickle
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import google.generativeai as genai
from sklearn.metrics.pairwise import cosine_similarity

# Load environment
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Flask app
app = Flask(__name__)
CORS(app)

# ---- File paths ----
CHAT_FILE = "whatsapp_chat_rohan_full.json"
VECTOR_STORE = "vector_store.pkl"

# ---- Embedding helper ----
def get_embedding(text: str):
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=text
    )
    return np.array(result["embedding"], dtype=np.float32)

# ---- Build embeddings & save to pickle ----
def build_vector_store():
    with open(CHAT_FILE, "r", encoding="utf-8") as f:
        messages = json.load(f)

    texts, embeddings, metadata = [], [], []
    for msg in messages:
        text = f"{msg['name']}: {msg['text']}"
        emb = get_embedding(text)
        texts.append(text)
        embeddings.append(emb)
        metadata.append({"timestamp": msg["time"], "side": msg["side"]})

    vectors = np.vstack(embeddings)

    with open(VECTOR_STORE, "wb") as f:
        pickle.dump((vectors, texts, metadata), f)

    print(f"✅ Vector store built with {len(texts)} messages.")

# ---- Load vector store ----
if not os.path.exists(VECTOR_STORE):
    print("Vector store missing — building...")
    build_vector_store()
else:
    print("Vector store found — loading...")

with open(VECTOR_STORE, "rb") as f:
    vectors, texts, metadata = pickle.load(f)

# ---- Routes ----
@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Backend running with pickle-based RAG!"})

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
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
            snippets.append(f"[{metadata[i]['timestamp']}] {texts[i]}")

    # Build prompt for Gemini
    if snippets:
        context_text = "\n".join(snippets)
        prompt = f"""
        You are a helpful assistant. You have access to the user's past conversations.

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
        # No strong matches, fallback to normal reasoning
        prompt = f"""
        You are a helpful assistant. 
        The user asked: {question}
        No relevant past conversation was found, so answer using your own knowledge.
        """

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)

    return jsonify({"answer": response.text})

# ---- Run ----
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
