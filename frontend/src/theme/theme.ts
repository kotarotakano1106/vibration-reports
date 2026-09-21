import { createTheme } from "@mui/material/styles";
import { colorTokens } from "./tokens";

export const appTheme = createTheme({
  palette: {
    primary: { main: colorTokens.brand.primary, dark: colorTokens.brand.dark, light: colorTokens.brand.light, contrastText: colorTokens.surface.paper },
    background: { default: colorTokens.surface.background, paper: colorTokens.surface.paper },
    text: colorTokens.text,
    divider: colorTokens.surface.border,
    error: { main: colorTokens.status.error },
    warning: { main: colorTokens.status.warning },
    success: { main: colorTokens.status.success },
  },
  spacing: 8,
  shape: { borderRadius: 12 },
  typography: {
    fontFamily: '"Noto Sans JP", "Yu Gothic", sans-serif',
    h6: { fontSize: 15, fontWeight: 700 },
    subtitle1: { fontSize: 12, fontWeight: 700 },
    body2: { fontSize: 10 },
    caption: { fontSize: 8 },
    button: { fontSize: 10, fontWeight: 600, textTransform: "none" },
  },
  components: {
    MuiCssBaseline: { styleOverrides: { "html, body": { height: "100%" }, body: { overflow: "hidden" } } },
    MuiButton: { defaultProps: { disableElevation: true }, styleOverrides: { root: { minHeight: 30, borderRadius: 8, paddingInline: 12 } } },
    MuiCard: { styleOverrides: { root: { border: `1px solid ${colorTokens.surface.border}`, boxShadow: "0 6px 20px rgba(53, 63, 72, 0.06)" } } },
    MuiOutlinedInput: { styleOverrides: { root: { minHeight: 32, backgroundColor: colorTokens.surface.paper, fontSize: 10 }, notchedOutline: { borderColor: colorTokens.surface.border } } },
    MuiTableCell: { styleOverrides: { root: { borderBottomColor: colorTokens.surface.border, fontSize: 9, padding: "7px 14px" }, head: { color: colorTokens.text.secondary, fontSize: 8, fontWeight: 600, backgroundColor: colorTokens.surface.subtle } } },
  },
});