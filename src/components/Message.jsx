import { Box, Typography, Paper } from "@mui/material";

export default function Message({ sender, timestamp, content, side }) {
  const isRight = side?.toLowerCase() === "right";

  return (
    <Box
      sx={{
        my: 1,
        display: "flex",
        justifyContent: isRight ? "flex-end" : "flex-start",
      }}
    >
      <Paper
        sx={{
          p: 1.5,
          bgcolor: isRight ? "#DCF8C6" : "#FFFFFF", // WhatsApp style
          maxWidth: "70%",
          borderRadius: 2,
          boxShadow: 1,
        }}
      >
        <Typography
          variant="body2"
          sx={{ fontWeight: "bold", mb: 0.5, color: "text.secondary" }}
        >
          {sender}
        </Typography>
        <Typography variant="body1">{content}</Typography>
        <Typography
          variant="caption"
          sx={{ display: "block", mt: 0.5, textAlign: "right", color: "gray" }}
        >
          {new Date(timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </Typography>
      </Paper>
    </Box>
  );
}
