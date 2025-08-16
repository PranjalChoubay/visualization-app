from flask import Flask, request, jsonify
import pickle
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# Load stored vectorizer and vectors
with open("vector_store.pkl", "rb") as f:
    vectorizer, vectors = pickle.load(f)

@app.route("/")
def home():
    return "Backend is running!"

@app.route("/query", methods=["POST"])
def query():
    data = request.get_json()
    user_input = data.get("query", "")

    if not user_input.strip():
        return jsonify({"error": "Query cannot be empty"}), 400

    # Transform query into vector
    query_vec = vectorizer.transform([user_input])

    # Compute cosine similarity
    similarities = cosine_similarity(query_vec, vectors).flatten()
    best_idx = np.argmax(similarities)

    return jsonify({
        "query": user_input,
        "best_match_index": int(best_idx),
        "similarity_score": float(similarities[best_idx])
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
