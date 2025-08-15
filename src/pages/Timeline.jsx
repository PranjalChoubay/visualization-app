import { Container, Typography, Paper } from "@mui/material";

export default function Timeline() {
  return (
    <Container sx={{ py: 3 }}>
      <Typography variant="h5" gutterBottom>Timeline</Typography>
      <Paper sx={{ p: 2 }}>Your conversation will render here.</Paper>
    </Container>
  );
}
