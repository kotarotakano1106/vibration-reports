"use client";

import { useState } from "react";
import { CameraAltOutlined, DescriptionOutlined, ExpandLess, ExpandMore, FolderOutlined, MemoryOutlined, SensorsOutlined, SettingsOutlined, ThermostatOutlined, TuneOutlined } from "@mui/icons-material";
import { alpha, Box, Button, Collapse, Drawer, List, ListItemButton, ListItemIcon, ListItemText } from "@mui/material";
import { colorTokens, gradientTokens, layoutTokens } from "@/theme/tokens";

const groups = [
  ["services", "RASPBERRY PI SERVICES", [[SensorsOutlined, "振動モニタリング"], [ThermostatOutlined, "温度モニタリング"], [CameraAltOutlined, "カメラ監視"]]],
  ["workspace", "WORKSPACE", [[DescriptionOutlined, "レポート"], [FolderOutlined, "ファイル管理"]]],
  ["management", "MANAGEMENT", [[MemoryOutlined, "Raspberry Pi管理"], [TuneOutlined, "設備管理"]]],
] as const;

export function AppSidebar() {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({ services: true, workspace: true, management: true });
  return <Drawer variant="permanent" slotProps={{ paper: { sx: { top: layoutTokens.headerHeight, width: layoutTokens.navigationWidth, height: `calc(100% - ${layoutTokens.headerHeight}px)`, border: 0, color: "common.white", background: gradientTokens.sidebar, p: 1.25 } } }}>{groups.map(([id, title, items]) => <Box key={id} sx={{ mb: 1.25 }}><ListItemButton onClick={() => setExpanded((current) => ({ ...current, [id]: !current[id] }))} aria-expanded={expanded[id]} sx={{ minHeight: 34, px: 1, borderRadius: 1, color: alpha(colorTokens.surface.paper, 0.84) }}><ListItemText primary={title} slotProps={{ primary: { variant: "caption", sx: { fontWeight: 700 } } }} />{expanded[id] ? <ExpandLess fontSize="small" /> : <ExpandMore fontSize="small" />}</ListItemButton><Collapse in={expanded[id]} timeout="auto" unmountOnExit><List disablePadding sx={{ pt: 0.5 }}>{items.map(([Icon, label], index) => <ListItemButton key={label} selected={id === "services" && index === 0} sx={{ minHeight: 40, px: 1.25, mb: 0.4, borderRadius: 1, color: "common.white", "&.Mui-selected": { bgcolor: alpha(colorTokens.surface.paper, 0.92), color: "primary.dark" } }}><ListItemIcon sx={{ minWidth: 30, color: "inherit" }}><Icon sx={{ fontSize: 18 }} /></ListItemIcon><ListItemText primary={label} slotProps={{ primary: { variant: "body2", sx: { fontWeight: 600 } } }} /></ListItemButton>)}</List></Collapse></Box>)}<Button variant="outlined" color="inherit" fullWidth startIcon={<SettingsOutlined />} sx={{ position: "absolute", bottom: 48, left: 10, width: "calc(100% - 20px)", borderColor: alpha(colorTokens.surface.paper, 0.45), justifyContent: "flex-start" }}>設定</Button></Drawer>;
}
