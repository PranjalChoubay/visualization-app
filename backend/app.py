import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings
import google.generativeai as genai
from concurrent.futures import ThreadPoolExecutor

# Load env
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Flask app
app = Flask(__name__)
CORS(app)

# Persistent ChromaDB
chroma_client = chromadb.PersistentClient(path="./chroma_data")
collection = chroma_client.get_or_create_collection(name="conversation")

# ---- Embedding helper ----
def get_embedding(text: str):
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=text
    )
    return result["embedding"]

# ---- Load and embed messages ----
def load_and_embed():
    with open("whatsapp_chat_rohan_full.json", "r", encoding="utf-8") as f:
        messages = json.load(f)

    def process_message(idx, msg):
        text = f"{msg['name']}: {msg['text']}"
        emb = get_embedding(text)
        return {
            "id": str(idx),
            "embedding": emb,
            "document": text,
            "metadata": {"timestamp": msg["time"], "side": msg["side"]}
        }

    with ThreadPoolExecutor() as executor:
        results = list(executor.map(lambda x: process_message(*x), enumerate(messages)))

    for r in results:
        collection.add(
            ids=[r["id"]],
            embeddings=[r["embedding"]],
            documents=[r["document"]],
            metadatas=[r["metadata"]],
        )

# Embed only once
if len(collection.get()["ids"]) == 0:
    print("Creating embeddings (first run)...")
    load_and_embed()
    print("Done embedding.")
else:
    print("Embeddings already exist — skipping embedding step.")

# ---- Health check ----
@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Backend is running with Gemini RAG!"})

# ---- Ask Why endpoint ----
@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    question = data.get("question", "")
    if not question.strip():
        return jsonify({"error": "No question provided"}), 400

    # Embed question
    q_emb = get_embedding(question)
    results = collection.query(query_embeddings=[q_emb], n_results=5)

    snippets = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        snippets.append(f"[{meta['timestamp']}] {doc}")

    # Build prompt
    prompt = f"""
    You are a helpful assistant.
    Based ONLY on the following conversation snippets, answer the user's question.
    Cite the timestamp for each fact you use.

    Conversation Snippets:
    {chr(10).join(snippets)}

    User's Question: {question}
    """

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)

    return jsonify({"answer": response.text})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
