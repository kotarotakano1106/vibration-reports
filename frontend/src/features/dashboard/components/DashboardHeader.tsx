"use client";

import { Refresh, SensorsOutlined } from "@mui/icons-material";
import { Box, Button, FormControl, MenuItem, Select, Stack, Typography } from "@mui/material";

type DashboardHeaderProps = {
  equipmentIds: string[];
  periods: string[];
  selectedEquipmentId: string;
  selectedPeriod: string;
  isRefreshing: boolean;
  onEquipmentChange: (value: string) => void;
  onPeriodChange: (value: string) => void;
  onRefresh: () => void;
  onOpenUpload: () => void;
};

export function DashboardHeader(props: DashboardHeaderProps) {
  return (
    <Stack direction="row" spacing={1.5} sx={{ alignItems: "center" }}>
      <Typography variant="h6" color="primary.dark">振動モニタリング</Typography>
      <Box sx={{ flex: 1 }} />
      <FormControl size="small" sx={{ minWidth: 140 }}>
        <Select value={props.selectedEquipmentId} displayEmpty disabled={props.equipmentIds.length === 0} inputProps={{ "aria-label": "対象設備" }} onChange={(event) => props.onEquipmentChange(event.target.value)}>
          {props.equipmentIds.length === 0 ? <MenuItem value="">設備なし</MenuItem> : props.equipmentIds.map((value) => <MenuItem key={value} value={value}>{value}</MenuItem>)}
        </Select>
      </FormControl>
      <FormControl size="small" sx={{ minWidth: 130 }}>
        <Select value={props.selectedPeriod} displayEmpty disabled={props.periods.length === 0} inputProps={{ "aria-label": "対象年月" }} onChange={(event) => props.onPeriodChange(event.target.value)}>
          {props.periods.length === 0 ? <MenuItem value="">期間なし</MenuItem> : props.periods.map((value) => <MenuItem key={value} value={value}>{value}</MenuItem>)}
        </Select>
      </FormControl>
      <Button variant="outlined" startIcon={<Refresh />} disabled={props.isRefreshing} onClick={props.onRefresh}>{props.isRefreshing ? "更新中..." : "更新"}</Button>
      <Button variant="contained" startIcon={<SensorsOutlined />} onClick={props.onOpenUpload}>CSVアップロード</Button>
    </Stack>
  );
}
