import { Container, Typography, Paper } from "@mui/material";

export default function Dashboard() {
  return (
    <Container sx={{ py: 3 }}>
      <Typography variant="h5" gutterBottom>Dashboard</Typography>
      <Paper sx={{ p: 2 }}>Charts & tables will go here.</Paper>
    </Container>
  );
}
