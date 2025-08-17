import { useEffect, useState, useMemo } from "react";
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
  ThemeProvider,
  createTheme,
  CssBaseline,
} from "@mui/material";

// The JSON data is now included directly in the component
// to avoid the fetch error.
const chatData = {
  "program": "Elyx Concierge Health",
  "year": 2025,
  "months": [
    {
      "month": "01-2025",
      "weeks": [
        {
          "week": 1,
          "conversations": [
            { "date": "2025-01-06", "time": "08:00", "sender": "Rohan", "message": "Hi team — starting week 1. Garmin synced." },
            { "date": "2025-01-07", "time": "09:30", "sender": "Ruby (Client Manager)", "message": "Welcome Rohan. Baseline test booked Tue 07:30. Fast overnight." },
            { "date": "2025-01-07", "time": "18:45", "sender": "Rohan", "message": "Quick follow-up: Sarah shared travel calendar." }
          ]
        }
      ]
    },
    {
      "month": "02-2025",
      "weeks": [
        {
          "week": 1,
          "conversations": [
            { "date": "2025-02-03", "time": "09:00", "sender": "Rohan", "message": "Which results are most concerning and how soon can I see changes?" },
            { "date": "2025-02-03", "time": "09:20", "sender": "Dr. Warren (Medical Strategist)", "message": "The priority areas are cholesterol and vitamin D. You should start seeing measurable changes in 8–12 weeks with consistent diet and supplements." },
            { "date": "2025-02-04", "time": "20:00", "sender": "Rohan", "message": "How reliable are these tests? Do results vary day to day?" },
            { "date": "2025-02-04", "time": "20:30", "sender": "Advik (Performance Scientist)", "message": "Great point. Some markers like glucose fluctuate daily, but long-term markers like HbA1c and ApoB are stable. That's why we repeat quarterly to see trends." }
          ]
        },
        {
          "week": 2,
          "conversations": [
            { "date": "2025-02-10", "time": "09:00", "sender": "Rohan", "message": "Do I really need to cut rice from my meals?" },
            { "date": "2025-02-10", "time": "09:20", "sender": "Carla (Nutritionist)", "message": "Not entirely. We’ll focus on portion control and swapping white rice with brown rice or quinoa a few times a week." },
            { "date": "2025-02-11", "time": "20:00", "sender": "Rohan", "message": "Can supplements replace food-based nutrition?" },
            { "date": "2025-02-11", "time": "20:30", "sender": "Carla (Nutritionist)", "message": "Food-first approach is always better — supplements are just insurance for gaps." }
          ]
        }
      ]
    }
    // ... (rest of the JSON data can be added here)
  ]
};


// Helper function to get the month name and week number from a timestamp.
function extractMonthWeek(timestamp) {
  try {
    const date = new Date(timestamp);
    if (isNaN(date)) return { month: "Unknown", week: "Unknown" };

    const month = date.toLocaleString("default", { month: "long" });
    // This is a simplified week calculation. For more accuracy, you might use a date library.
    const week = `Week ${Math.ceil(date.getDate() / 7)}`;
    return { month, week };
  } catch {
    return { month: "Unknown", week: "Unknown" };
  }
}

export default function App() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedMonth, setSelectedMonth] = useState("All Months");
  const [selectedWeek, setSelectedWeek] = useState("All Weeks");
  const [search, setSearch] = useState("");
  const [darkMode, setDarkMode] = useState(false);

  // Theme for dark/light mode
  const theme = useMemo(
    () =>
      createTheme({
        palette: {
          mode: darkMode ? "dark" : "light",
        },
      }),
    [darkMode]
  );

  // Effect to process chat data on component mount.
  useEffect(() => {
    // The raw data is nested. We need to flatten it into a single message array.
    const allMessages = [];
    chatData.months.forEach((monthData) => {
      monthData.weeks.forEach((weekData) => {
        weekData.conversations.forEach((convo) => {
          // Combine date and time from JSON to create a valid Date object.
          const timestamp = new Date(`${convo.date}T${convo.time}`);
          const { month, week } = extractMonthWeek(timestamp.getTime());
          
          // Determine message alignment based on the sender.
          const side = convo.sender === "Rohan" ? "right" : "left";

          allMessages.push({
            name: convo.sender,
            text: convo.message,
            time: timestamp.getTime(),
            month,
            week,
            side,
          });
        });
      });
    });

    // Add a unique ID to each message for stable rendering.
    const enriched = allMessages.map((msg, index) => ({
      ...msg,
      id: `${msg.time}-${index}`,
    }));

    setMessages(enriched);
    setLoading(false); // Data is now processed, so we can stop loading.
  }, []);

  // Memoize the filtering logic so it only runs when dependencies change.
  // This improves performance, especially with large datasets.
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

  // Derive unique months for the filter dropdown from the messages.
  const months = ["All Months", ...new Set(messages.map((m) => m.month))];

  // Make the 'Week' filter context-aware.
  // The available weeks update based on the selected month for better UX.
  const weeks = useMemo(() => {
    if (selectedMonth === "All Months") {
      // Sort weeks numerically for better readability
      const allWeeks = [...new Set(messages.map((m) => m.week))];
      return ["All Weeks", ...allWeeks.sort((a, b) => parseInt(a.split(' ')[1]) - parseInt(b.split(' ')[1]))];
    }
    const weeksInMonth = messages
      .filter((m) => m.month === selectedMonth)
      .map((m) => m.week);
    const uniqueWeeks = [...new Set(weeksInMonth)];
    return ["All Weeks", ...uniqueWeeks.sort((a, b) => parseInt(a.split(' ')[1]) - parseInt(b.split(' ')[1]))];
  }, [messages, selectedMonth]);

  // Effect to reset the week filter if it's no longer valid for the selected month.
  useEffect(() => {
    if (!weeks.includes(selectedWeek)) {
      setSelectedWeek("All Weeks");
    }
  }, [weeks, selectedWeek]);

  if (loading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
      >
        <CircularProgress />
      </Box>
    );
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container
        maxWidth="md"
        sx={{
          py: 3,
          display: 'flex',
          flexDirection: 'column',
          height: '100vh',
        }}
      >
        {/* Header */}
        <Paper elevation={2} sx={{ p: 2, mb: 2, borderRadius: 2 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center">
                <Typography variant="h5" component="h1">Conversation Timeline</Typography>
                <Button
                    variant="outlined"
                    size="small"
                    onClick={() => setDarkMode(!darkMode)}
                >
                    {darkMode ? "Light Mode" : "Dark Mode"}
                </Button>
            </Box>
        </Paper>

        {/* Filters */}
        <Paper elevation={2} sx={{ p: 2, mb: 2, borderRadius: 2 }}>
            <Box display="flex" gap={2} flexWrap="wrap" alignItems="center">
                <FormControl size="small" sx={{ minWidth: 150, flex: 1 }}>
                    <InputLabel>Month</InputLabel>
                    <Select
                        value={selectedMonth}
                        label="Month"
                        onChange={(e) => setSelectedMonth(e.target.value)}
                    >
                        {months.map((m) => (
                            <MenuItem key={m} value={m}>{m}</MenuItem>
                        ))}
                    </Select>
                </FormControl>

                <FormControl size="small" sx={{ minWidth: 150, flex: 1 }}>
                    <InputLabel>Week</InputLabel>
                    <Select
                        value={selectedWeek}
                        label="Week"
                        onChange={(e) => setSelectedWeek(e.target.value)}
                    >
                        {weeks.map((w) => (
                            <MenuItem key={w} value={w}>{w}</MenuItem>
                        ))}
                    </Select>
                </FormControl>

                <TextField
                    size="small"
                    label="Search in conversation"
                    variant="outlined"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    sx={{ minWidth: 200, flex: 2 }}
                />
            </Box>
        </Paper>

        {/* Messages Container */}
        <Box
          sx={{
            flex: 1,
            overflowY: "auto",
            p: 2,
            borderRadius: 2,
            bgcolor: 'background.default'
          }}
        >
          <Box display="flex" flexDirection="column" gap={1.5}>
            {filteredMessages.map((msg) => (
              <Box
                key={msg.id}
                display="flex"
                justifyContent={msg.side === "right" ? "flex-end" : "flex-start"}
              >
                <Paper
                  sx={{
                    p: 1.5,
                    maxWidth: "70%",
                    bgcolor:
                      msg.side === "right"
                        ? (darkMode ? "primary.dark" : "primary.light")
                        : (darkMode ? "grey.800" : "grey.200"),
                    borderRadius: 3,
                  }}
                  elevation={3}
                >
                  <Typography variant="body2" fontWeight="bold" color="text.secondary">
                    {msg.name}
                  </Typography>
                  <Typography variant="body1" sx={{ wordWrap: "break-word", my: 0.5 }}>
                    {msg.text}
                  </Typography>
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{ display: "block", textAlign: "right", mt: 0.5 }}
                  >
                    {new Date(msg.time).toLocaleString()}
                  </Typography>
                </Paper>
              </Box>
            ))}
             {filteredMessages.length === 0 && (
                <Typography align="center" color="text.secondary" sx={{p: 4}}>
                    No messages match your filters.
                </Typography>
            )}
          </Box>
        </Box>
      </Container>
    </ThemeProvider>
  );
}
