import { useState, useRef, useEffect } from "react";

export default function AskWhy() {
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleAsk = async () => {
    if (!question.trim()) return;

    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setLoading(true);

    try {
      const res = await fetch("https://visualization-app-9ill.onrender.com/ask", {
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
        display: "flex",
        flexDirection: "column",
        height: "calc(100vh - 64px)", // 👈 Adjust for TopNav height
        maxWidth: 700,
        margin: "auto",
      }}
    >
      {/* Chat messages */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          gap: "10px",
          padding: "10px",
          background: "#fafafa",
        }}
      >
        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
              background:
                msg.role === "user"
                  ? "linear-gradient(45deg, #d6249f, #285AEB)"
                  : "#efefef",
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
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div
        style={{
          display: "flex",
          gap: "10px",
          padding: "10px",
          borderTop: "1px solid #ddd",
          background: "white",
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
