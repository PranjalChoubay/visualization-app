import { useEffect, useState } from "react";
import { Container, Typography, CircularProgress } from "@mui/material";
import Message from "../components/Message";

export default function Timeline() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/whatsapp_chat_rohan_full.json")
      .then((res) => res.json())
      .then((data) => {
        setMessages(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error loading conversation:", err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <Container sx={{ py: 3 }}>
        <CircularProgress />
      </Container>
    );
  }

  return (
    <Container sx={{ py: 3, maxHeight: "80vh", overflowY: "auto" }}>
      <Typography variant="h5" gutterBottom>Timeline</Typography>
      {messages.map((msg, i) => (
        <Message
          key={i}
          sender={msg.name}        // UPDATED
          timestamp={msg.time}     // UPDATED
          content={msg.text}       // UPDATED
          side={msg.side}          // same
        />
      ))}
    </Container>
  );
}
