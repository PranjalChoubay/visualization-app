from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Initialize app
app = Flask(__name__)
CORS(app)

# Load vectorizer + vectors
with open("vector_store.pkl", "rb") as f:
    vectorizer, vectors, texts = pickle.load(f)  
    # texts = original sentences/documents

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Backend is running!"})

# ✅ Old endpoint (still works for debugging)
@app.route("/query", methods=["POST"])
def query():
    data = request.get_json()
    user_query = data.get("query", "")

    if not user_query.strip():
        return jsonify({"error": "Query cannot be empty"}), 400

    query_vec = vectorizer.transform([user_query])
    similarities = cosine_similarity(query_vec, vectors).flatten()
    best_idx = int(np.argmax(similarities))

    return jsonify({
        "best_match_index": best_idx,
        "query": user_query,
        "similarity_score": float(similarities[best_idx])
    })

# ✅ New endpoint for frontend (AskWhy.jsx)
@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    question = data.get("question", "")

    if not question.strip():
        return jsonify({"error": "Question cannot be empty"}), 400

    query_vec = vectorizer.transform([question])
    similarities = cosine_similarity(query_vec, vectors).flatten()
    best_idx = int(np.argmax(similarities))

    # Instead of just index, return text answer
    return jsonify({
        "answer": texts[best_idx],   # best matching text from your dataset
        "similarity_score": float(similarities[best_idx])
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
