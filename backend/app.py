from flask import Flask, request, jsonify
import pickle
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# ---- Load stored embeddings safely ----
with open("vector_store.pkl", "rb") as f:
    data = pickle.load(f)

# Handle both dict-style and tuple/list-style storage
if isinstance(data, dict):
    vectorizer = data.get("vectorizer")
    vectors = data.get("vectors")
elif isinstance(data, (list, tuple)):
    if len(data) >= 2:
        vectorizer, vectors = data[0], data[1]
    else:
        raise ValueError("vector_store.pkl does not have enough items")
else:
    raise ValueError("Unrecognized format in vector_store.pkl")

@app.route("/")
def home():
    return jsonify({"status": "Backend is running!"})

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
    best_idx = int(np.argmax(similarities))

    return jsonify({
        "query": user_input,
        "best_match_index": best_idx,
        "similarity_score": float(similarities[best_idx])
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
