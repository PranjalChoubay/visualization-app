return (
  <div
    style={{
      maxWidth: 700,
      margin: "auto",
      display: "flex",
      flexDirection: "column",
      height: "100vh", // full screen height
    }}
  >
    {/* Chat area */}
    <div
      style={{
        flex: 1,                  // fills available space above the input
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
        background: "white",     // keep visible even when scrolling
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
