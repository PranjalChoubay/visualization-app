import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings
import google.generativeai as genai

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = Flask(__name__)
CORS(app)

# Setup ChromaDB
chroma_client = chromadb.Client(Settings(persist_directory="./chroma_data"))
collection = chroma_client.get_or_create_collection(name="conversation")

# ---- Embedding helper ----
def get_embedding(text):
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=text
    )
    return result["embedding"]

# ---- Load and embed messages ----
def load_and_embed():
    with open("whatsapp_chat_rohan_full.json", "r", encoding="utf-8") as f:
        messages = json.load(f)

    for idx, msg in enumerate(messages):
        text = f"{msg['name']}: {msg['text']}"
        emb = get_embedding(text)

        collection.add(
            ids=[str(idx)],
            embeddings=[emb],
            documents=[text],
            metadatas={"timestamp": msg["time"], "side": msg["side"]}
        )

# Only embed once at start
if len(collection.get()["ids"]) == 0:
    print("Creating embeddings...")
    load_and_embed()
    print("Done.")

# ---- Ask Why endpoint ----
@app.route("/ask", methods=["POST"])
def ask():
    question = request.json.get("question", "")
    if not question:
        return jsonify({"error": "No question provided"}), 400

    q_emb = get_embedding(question)
    results = collection.query(query_embeddings=[q_emb], n_results=5)

    snippets = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        snippets.append(f"[{meta['timestamp']}] {doc}")

    # Use Gemini for final answer generation
    prompt = f"""
    You are a helpful assistant.
    Based ONLY on the following conversation snippets, answer the question.
    Cite the timestamp for each fact you use.

    Conversation Snippets:
    {chr(10).join(snippets)}

    Question: {question}
    """

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)

    return jsonify({"answer": response.text})

if __name__ == "__main__":
    app.run(debug=True)
