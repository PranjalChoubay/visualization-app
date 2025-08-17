import { Routes, Route } from "react-router-dom";
import TopNav from "./components/TopNav";
import Timeline from "./pages/Timeline";
import AskWhy from "./pages/Chat";
import Dashboard from "./pages/Dashboard";
import { Box } from "@mui/material";

export default function App() {
  return (
    <Box sx={{ minHeight: "100dvh", bgcolor: "background.default" }}>
      <TopNav />
      <Routes>
        <Route path="/" element={<Chat />} />
        <Route path="/why" element={<Timeline />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </Box>
  );
}
