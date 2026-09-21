export const colorTokens = {
  brand: { primary: "#E52F4C", dark: "#9B1530", light: "#FF6476" },
  surface: { background: "#F5F7F9", paper: "#FFFFFF", subtle: "#FBFCFD", border: "#DCE5EB" },
  text: { primary: "#25323B", secondary: "#74838D" },
  status: { error: "#B33A45", warning: "#C58627", success: "#2E7D6B" },
  chart: { vibration: "#357493" },
} as const;

export const gradientTokens = {
  primary: "linear-gradient(135deg, #C51635 0%, #ED3653 58%, #FA6072 100%)",
  sidebar: "linear-gradient(180deg, #94152A 0%, #D32140 48%, #7B1022 100%)",
} as const;

export const layoutTokens = { headerHeight: 58, navigationWidth: 184, aiDrawerWidth: 420 } as const;