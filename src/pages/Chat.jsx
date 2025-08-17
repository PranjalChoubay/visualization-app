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

  useEffect(() => {
    const saved = localStorage.getItem("askwhy_messages");
    if (saved) {
      setMessages(JSON.parse(saved));
    }
  }, []);

  // ✅ Save messages to localStorage whenever they change
  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem("askwhy_messages", JSON.stringify(messages));
    }
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
        {
          role: "ai",
          text: data.answer || "No answer found.",
          context: data.past_context || [],
        },
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

  // ✅ NEW FUNCTION: clear chat
  const clearChat = () => {
    localStorage.removeItem("askwhy_messages");
    setMessages([]);
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "calc(100vh - 64px)",
        maxWidth: 700,
        margin: "auto",
        border: "1px solid #ddd",
        borderRadius: "10px",
        overflow: "hidden",
      }}
    >
      {/* ✅ Clear Chat button always visible */}
      <div
        style={{
          display: "flex",
          justifyContent: "flex-end",
          padding: "8px 12px",
          borderBottom: "1px solid #ddd",
          background: "#f9f9f9",
        }}
      >
        <button
          onClick={clearChat}
          style={{
            padding: "6px 12px",
            fontSize: "13px",
            border: "1px solid #ccc",
            borderRadius: "6px",
            cursor: "pointer",
            background: "#fff",
            transition: "all 0.2s ease",
          }}
          onMouseOver={(e) =>
            (e.target.style.background = "#f0f0f0")
          }
          onMouseOut={(e) =>
            (e.target.style.background = "#fff")
          }
        >
          🗑 Clear Chat
        </button>
      </div>

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
              position: "relative",
            }}
          >
            {msg.role === "ai" ? (
              <RichAIMessage text={msg.text} />
            ) : (
              msg.text
            )}
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

/**
 * Parses a string and splits it into ordered segments:
 * - plain text pieces
 * - context blocks found inside [PAST_CONTEXT]...[/PAST_CONTEXT]
 */
function parsePastContextSegments(text) {
  const segments = [];
  const re = /\[PAST_CONTEXT\]([\s\S]*?)\[\/PAST_CONTEXT\]/g;
  let lastIndex = 0;
  let match;

  while ((match = re.exec(text)) !== null) {
    const start = match.index;
    const end = re.lastIndex;

    if (start > lastIndex) {
      segments.push({
        type: "text",
        content: text.slice(lastIndex, start),
      });
    }

    segments.push({
      type: "context",
      content: (match[1] || "").trim(),
    });

    lastIndex = end;
  }

  if (lastIndex < text.length) {
    segments.push({
      type: "text",
      content: text.slice(lastIndex),
    });
  }

  if (segments.length === 0) {
    return [{ type: "text", content: text }];
  }

  return segments;
}

/** Renders the AI message preserving the exact position of context blocks */
function RichAIMessage({ text }) {
  const segments = parsePastContextSegments(text);

  return (
    <div style={{ whiteSpace: "pre-wrap" }}>
      {segments.map((seg, idx) =>
        seg.type === "context" ? (
          <PastContextBox key={`ctx-${idx}`} content={seg.content} />
        ) : (
          <span key={`txt-${idx}`}>{seg.content}</span>
        )
      )}
    </div>
  );
}

/** Styled inline box for past context */
function PastContextBox({ content }) {
  return (
    <div
      style={{
        marginTop: "8px",
        marginBottom: "8px",
        border: "1px solid #000",
        borderRadius: "10px",
        background: "#ffffff",
        padding: "8px 12px",
      }}
    >
      <div
        style={{
          fontSize: "12px",
          fontWeight: 700,
          marginBottom: "6px",
          color: "#000",
        }}
      >
        Context from past conversation
      </div>
      <div style={{ whiteSpace: "pre-wrap", color: "#333" }}>{content}</div>
    </div>
  );
}
