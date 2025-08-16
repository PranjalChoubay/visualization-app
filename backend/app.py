from flask import Flask, request, jsonify
import os
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# File path for vector store
VECTOR_STORE_FILE = "vector_store.pkl"

# Load or build embeddings
if os.path.exists(VECTOR_STORE_FILE):
    with open(VECTOR_STORE_FILE, "rb") as f:
        data = pickle.load(f)
        vectorizer = data["vectorizer"]
        vectors = data["vectors"]
        documents = data["documents"]
else:
    print("vector_store.pkl not found. Building embeddings...")
    documents = [
        "This is a sample document.",
        "Flask is a Python web framework.",
        "We are building a visualization app."
    ]
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(documents)
    with open(VECTOR_STORE_FILE, "wb") as f:
        pickle.dump({"vectorizer": vectorizer, "vectors": vectors, "documents": documents}, f)
    print("Embeddings built and saved to vector_store.pkl")

@app.route("/")
def home():
    return jsonify({"message": "Welcome to the Visualization App Backend! Use /status to check health or /ask to query."})

@app.route("/status", methods=["GET"])
def status():
    return jsonify({"status": "Flask backend is running!", "collection_size": len(documents)})

@app.route("/ask", methods=["POST"])
def ask():
    try:
        data = request.get_json()
        question = data.get("question", "")

        if not question.strip():
            return jsonify({"error": "No question provided"}), 400

        q_vector = vectorizer.transform([question])
        similarities = cosine_similarity(q_vector, vectors).flatten()
        idx = similarities.argmax()
        best_match = documents[idx]

        return jsonify({"question": question, "answer": best_match})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
