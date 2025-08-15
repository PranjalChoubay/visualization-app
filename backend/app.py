import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings
import google.generativeai as genai
from concurrent.futures import ThreadPoolExecutor

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = Flask(__name__)
CORS(app)

# Setup persistent ChromaDB (saves data in ./chroma_data)
chroma_client = chromadb.PersistentClient(path="./chroma_data")
collection = chroma_client.get_or_create_collection(name="conversation")

# Preload Gemini model once
model = genai.GenerativeModel("gemini-1.5-flash")

# ---- Embedding helper ----
def get_embedding(text):
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=text
    )
    return result["embedding"]

# ---- Load and embed messages in parallel ----
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

    with ThreadPoolExecutor(max_workers=8) as executor:  # Adjust workers if needed
        results = list(executor.map(lambda x: process_message(*x), enumerate(messages)))

    # Add all at once to ChromaDB
    collection.add(
        ids=[r["id"] for r in results],
        embeddings=[r["embedding"] for r in results],
        documents=[r["document"] for r in results],
        metadatas=[r["metadata"] for r in results]
    )

# Only embed once if collection is empty
if len(collection.get()["ids"]) == 0:
    print("Creating embeddings for the first time (parallelized)...")
    load_and_embed()
    print("Embeddings created and saved in ./chroma_data")
else:
    print("Embeddings already exist — skipping embedding step.")

# ---- Ask Why endpoint ----
@app.route("/ask", methods=["POST"])
def ask():
    try:
        question = request.json.get("question", "").strip()
        if not question:
            return jsonify({"error": "No question provided"}), 400

        # Embed the question
        q_emb = get_embedding(question)
        results = collection.query(query_embeddings=[q_emb], n_results=3)

        snippets = []
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            snippets.append(f"[{meta['timestamp']}] {doc}")

        # Create prompt
        prompt = f"""
        You are a helpful assistant.
        Based ONLY on the following conversation snippets, answer the question.
        Cite the timestamp for each fact you use.

        Conversation Snippets:
        {chr(10).join(snippets)}

        Question: {question}
        """

        # Use preloaded Gemini model
        response = model.generate_content(prompt)

        return jsonify({"answer": response.text})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
