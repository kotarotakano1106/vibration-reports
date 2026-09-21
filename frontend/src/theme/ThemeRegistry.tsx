"use client";

import type { PropsWithChildren } from "react";
import { CssBaseline, ThemeProvider } from "@mui/material";
import { appTheme } from "./theme";

export function ThemeRegistry({ children }: PropsWithChildren) {
  return <ThemeProvider theme={appTheme}><CssBaseline />{children}</ThemeProvider>;
}