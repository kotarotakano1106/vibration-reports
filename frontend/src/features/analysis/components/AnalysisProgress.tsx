import { LinearProgress, Stack, Typography } from "@mui/material";

type AnalysisProgressProps = { active: boolean };

export function AnalysisProgress({ active }: AnalysisProgressProps) {
  if (!active) return null;
  return <Stack spacing={0.75} sx={{ mt: 2 }}><Typography variant="caption" color="text.secondary">CSVを確認しています...</Typography><LinearProgress /></Stack>;
}
