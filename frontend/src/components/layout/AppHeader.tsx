"use client";

import { AddCommentOutlined, AutoAwesome, Menu as MenuIcon, NotificationsNone } from "@mui/icons-material";
import { AppBar, Avatar, Box, Button, IconButton, Toolbar, Typography } from "@mui/material";
import { layoutTokens } from "@/theme/tokens";

type AppHeaderProps = { onOpenChat: () => void };

export function AppHeader({ onOpenChat }: AppHeaderProps) {
  return <AppBar position="fixed" color="inherit" elevation={0} sx={{ height: layoutTokens.headerHeight, borderBottom: 1, borderColor: "divider", zIndex: (theme) => theme.zIndex.drawer + 1 }}><Toolbar sx={{ minHeight: `${layoutTokens.headerHeight}px !important`, px: 2.5 }}><IconButton aria-label="ナビゲーションメニュー"><MenuIcon /></IconButton><AutoAwesome color="primary" sx={{ ml: 2, mr: 1 }} /><Typography variant="h6" color="primary.dark">RASPI AI</Typography><Box sx={{ flex: 1 }} /><Button variant="contained" startIcon={<AddCommentOutlined />} onClick={onOpenChat}>AIに相談</Button><IconButton aria-label="通知" sx={{ ml: 1 }}><NotificationsNone /></IconButton><Avatar sx={{ ml: 1.5, width: 32, height: 32, bgcolor: "primary.main", fontSize: 11 }}>KT</Avatar><Typography variant="body2" sx={{ ml: 1, fontWeight: 700 }}>髙野 洸太郎</Typography></Toolbar></AppBar>;
}
