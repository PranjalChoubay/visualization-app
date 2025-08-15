import { useState } from "react";

export default function AskWhy() {
  const [messages, setMessages] = useState([]); // stores { role: "user"|"ai", text: "" }
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);

  const handleAsk = async () => {
    if (!question.trim()) return;

    // Add user message
    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setLoading(true);

    try {
      const res = await fetch("http://127.0.0.1:5000/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });

      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        { role: "ai", text: data.answer || "No answer found." },
      ]);
    } catch (err) {
      console.error(err);
      setMessages((prev) => [
        ...prev,
        { role: "ai", text: "⚠️ Error fetching answer." },
      ]);
    } finally {
      setQuestion("");
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        maxWidth: 700,
        margin: "auto",
        padding: "20px 10px",
        display: "flex",
        flexDirection: "column",
        height: "100vh",
      }}
    >
      {/* Chat area */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          gap: "10px",
          padding: "10px",
        }}
      >
        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
              background:
                msg.role === "user" ? "linear-gradient(45deg, #d6249f, #285AEB)" : "#efefef",
              color: msg.role === "user" ? "white" : "black",
              padding: "10px 14px",
              borderRadius: "18px",
              maxWidth: "80%",
              whiteSpace: "pre-wrap",
              wordWrap: "break-word",
              boxShadow: "0 2px 5px rgba(0,0,0,0.1)",
            }}
          >
            {msg.text}
          </div>
        ))}
      </div>

      {/* Input area */}
      <div
        style={{
          display: "flex",
          gap: "10px",
          padding: "10px",
          borderTop: "1px solid #ddd",
        }}
      >
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Type a message..."
          style={{
            flex: 1,
            padding: "10px 14px",
            fontSize: "14px",
            borderRadius: "20px",
            border: "1px solid #ccc",
            outline: "none",
          }}
          onKeyDown={(e) => e.key === "Enter" && handleAsk()}
        />
        <button
          onClick={handleAsk}
          disabled={loading}
          style={{
            background: "linear-gradient(45deg, #d6249f, #285AEB)",
            color: "white",
            border: "none",
            padding: "0 16px",
            borderRadius: "20px",
            cursor: "pointer",
          }}
        >
          {loading ? "..." : "Send"}
        </button>
      </div>
    </div>
  );
}
