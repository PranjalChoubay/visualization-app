import os
import pickle
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)
CORS(app)

VECTOR_STORE_FILE = "vector_store.pkl"
CHAT_FILE = "whatsapp_chat_rohan_full.json"

# Load embeddings if available, otherwise build them
if os.path.exists(VECTOR_STORE_FILE):
    with open(VECTOR_STORE_FILE, "rb") as f:
        vectorizer, vectors, messages = pickle.load(f)
    print("Loaded embeddings from vector_store.pkl")
else:
    print("vector_store.pkl not found. Building embeddings...")
    with open(CHAT_FILE, "r", encoding="utf-8") as f:
        messages = json.load(f)

    texts = [msg["text"] for msg in messages if msg.get("text")]
    vectorizer = TfidfVectorizer().fit(texts)
    vectors = vectorizer.transform(texts)

    with open(VECTOR_STORE_FILE, "wb") as f:
        pickle.dump((vectorizer, vectors, messages), f)
    print("Embeddings built and saved to vector_store.pkl")

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "collection_size": len(messages)})

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    question = data.get("question", "")
    if not question:
        return jsonify({"error": "No question provided"}), 400

    # Vectorize question and find most similar message
    q_vec = vectorizer.transform([question])
    sims = cosine_similarity(q_vec, vectors).flatten()
    idx = sims.argmax()
    answer = messages[idx]["text"]

    return jsonify({"answer": answer})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
