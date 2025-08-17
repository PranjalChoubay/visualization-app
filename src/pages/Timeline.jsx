import { useEffect, useState, useMemo } from "react"; // 1. Import useMemo
import {
  Container,
  Typography,
  CircularProgress,
  TextField,
  MenuItem,
  FormControl,
  Select,
  InputLabel,
  Box,
  Button,
  Paper,
} from "@mui/material";

// helper: get month name & week from timestamp
function extractMonthWeek(timestamp) {
  try {
    const date = new Date(timestamp);
    if (isNaN(date)) return { month: "Unknown", week: "Unknown" };

    const month = date.toLocaleString("default", { month: "long" });
    // Note: This is a simplified week calculation. For more accuracy, consider a date library.
    const week = `Week ${Math.ceil(date.getDate() / 7)}`;
    return { month, week };
  } catch {
    return { month: "Unknown", week: "Unknown" };
  }
}

export default function Timeline() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedMonth, setSelectedMonth] = useState("All Months");
  const [selectedWeek, setSelectedWeek] = useState("All Weeks");
  const [search, setSearch] = useState("");
  const [darkMode, setDarkMode] = useState(false);

  useEffect(() => {
    fetch("/whatsapp_chat_rohan_full.json")
      .then((res) => res.json())
      .then((data) => {
        // Enrich messages with month/week once on load
        const enriched = data.map((msg, index) => { // 2. Add a unique key
          const { month, week } = extractMonthWeek(msg.time);
          return { ...msg, month, week, id: `${msg.time}-${index}` }; // Use timestamp + index for a guaranteed unique ID
        });
        setMessages(enriched);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error loading conversation:", err);
        setLoading(false);
      });
  }, []);

  // 3. Memoize filtered messages for performance
  // This expensive filtering logic now only runs when its dependencies change
  const filteredMessages = useMemo(() => {
    return messages.filter((msg) => {
      const matchMonth =
        selectedMonth === "All Months" || msg.month === selectedMonth;
      const matchWeek =
        selectedWeek === "All Weeks" || msg.week === selectedWeek;
      const matchSearch = msg.text
        .toLowerCase()
        .includes(search.toLowerCase());
      return matchMonth && matchWeek && matchSearch;
    });
  }, [messages, selectedMonth, selectedWeek, search]);

  if (loading) {
    return (
      <Container sx={{ py: 3 }}>
        <CircularProgress />
      </Container>
    );
  }

  // derive unique months & weeks for filters
  const months = ["All Months", ...new Set(messages.map((m) => m.month))];
  
  // 4. Make the 'Week' filter context-aware
  // The available weeks now update based on the selected month for better UX
  const weeks = useMemo(() => {
    if (selectedMonth === "All Months") {
      return ["All Weeks", ...new Set(messages.map((m) => m.week))];
    }
    const weeksInMonth = messages
      .filter((m) => m.month === selectedMonth)
      .map((m) => m.week);
    return ["All Weeks", ...new Set(weeksInMonth)];
  }, [messages, selectedMonth]);

  // Reset week filter if it's no longer valid for the selected month
  useEffect(() => {
    if (!weeks.includes(selectedWeek)) {
      setSelectedWeek("All Weeks");
    }
  }, [weeks, selectedWeek]);


  return (
    <Container
      sx={{
        py: 3,
        maxHeight: "80vh",
        overflowY: "auto",
        bgcolor: darkMode ? "grey.900" : "grey.100",
        color: darkMode ? "grey.100" : "grey.900",
        borderRadius: 2,
      }}
    >
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h5">Timeline</Typography>
        <Button
          variant="outlined"
          size="small"
          onClick={() => setDarkMode(!darkMode)}
        >
          {darkMode ? "Light Mode" : "Dark Mode"}
        </Button>
      </Box>

      {/* Filters */}
      <Box display="flex" gap={2} flexWrap="wrap" mb={2}>
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Month</InputLabel>
          <Select
            value={selectedMonth}
            label="Month"
            onChange={(e) => setSelectedMonth(e.target.value)}
          >
            {months.map((m) => (
              <MenuItem key={m} value={m}>
                {m}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Week</InputLabel>
          <Select
            value={selectedWeek}
            label="Week"
            onChange={(e) => setSelectedWeek(e.target.value)}
          >
            {weeks.map((w) => (
              <MenuItem key={w} value={w}>
                {w}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <TextField
          size="small"
          label="Search"
          variant="outlined"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          sx={{ flex: 1, minWidth: 200 }}
        />
      </Box>

      {/* Messages */}
      <Box display="flex" flexDirection="column" gap={1}>
        {filteredMessages.map((msg) => ( // Use the unique 'id' we created
          <Box
            key={msg.id} // 2. Use a stable, unique key instead of the array index
            display="flex"
            justifyContent={msg.side === "right" ? "flex-end" : "flex-start"}
          >
            <Paper
              sx={{
                p: 1.5,
                maxWidth: "70%",
                bgcolor:
                  msg.side === "right"
                    ? darkMode
                      ? "green.800"
                      : "green.300"
                    : darkMode
                    ? "grey.800"
                    : "white",
                color: darkMode ? "grey.100" : "grey.900",
                borderRadius: 3,
              }}
              elevation={3}
            >
              <Typography variant="body2" fontWeight="bold">
                {msg.name}
              </Typography>
              <Typography variant="body1" sx={{ wordWrap: "break-word" }}>
                {msg.text}
              </Typography>
              <Typography
                variant="caption"
                sx={{ display: "block", textAlign: "right", mt: 0.5 }}
              >
                {new Date(msg.time).toLocaleString()} 
              </Typography>
            </Paper>
          </Box>
        ))}
      </Box>
    </Container>
  );
}