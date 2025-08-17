import { createTheme } from "@mui/material/styles";

const theme = createTheme({
  palette: {
    mode: "light",
    primary: { main: "#6c1dc7ff" },
    background: { default: "#ffffffff" }
  },
  shape: { borderRadius: 14 }
});

export default theme;
