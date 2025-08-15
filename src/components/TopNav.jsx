import { AppBar, Toolbar, Typography, Button, Box } from "@mui/material";
import { Link as RouterLink } from "react-router-dom";

export default function TopNav() {
  return (
    <AppBar position="sticky" elevation={0}>
      <Toolbar>
        <Typography variant="h6" sx={{ flexGrow: 1 }}>
          Viz App
        </Typography>
        <Box sx={{ display: "flex", gap: 1 }}>
          <Button color="inherit" component={RouterLink} to="/">Timeline</Button>
          <Button color="inherit" component={RouterLink} to="/why">Ask Why</Button>
          <Button color="inherit" component={RouterLink} to="/dashboard">Dashboard</Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
}
