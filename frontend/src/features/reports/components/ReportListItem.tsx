import { MoreVert } from "@mui/icons-material";
import {
  alpha,
  Chip,
  IconButton,
  TableCell,
  TableRow,
} from "@mui/material";

import type {
  Report,
  ReportStatus,
} from "../types/report";


type ReportListItemProps = {
  report: Report;
  onSelect: (report: Report) => void;
};


const statusColors: Record<
  ReportStatus,
  "error" | "warning" | "success"
> = {
  異常: "error",
  注意: "warning",
  正常: "success",
};


const bodyCellSx = {
  py: 1.5,
  px: 1,
  textAlign: "center",
  verticalAlign: "middle",
  whiteSpace: "nowrap",
  overflow: "hidden",
  textOverflow: "ellipsis",
} as const;


export function ReportListItem({
  report,
  onSelect,
}: ReportListItemProps) {
  const color = statusColors[report.status];

  return (
    <TableRow hover>
      <TableCell sx={bodyCellSx}>
        {report.date}
      </TableCell>

      <TableCell sx={bodyCellSx}>
        {report.period}
      </TableCell>

      <TableCell sx={bodyCellSx}>
        {report.equipmentId ?? "MOTOR-001"}
      </TableCell>

      <TableCell
        sx={bodyCellSx}
        title={report.file}
      >
        {report.file}
      </TableCell>

      <TableCell sx={bodyCellSx}>
        <Chip
          label={report.status}
          color={color}
          size="small"
          variant="outlined"
          sx={{
            height: 22,
            minWidth: 46,
            border: 0,
            bgcolor: (theme) =>
              alpha(theme.palette[color].main, 0.1),
            "& .MuiChip-label": {
              px: 1,
              fontSize: 11,
              fontWeight: 700,
              lineHeight: 1,
            },
          }}
        />
      </TableCell>

      <TableCell sx={bodyCellSx}>
        {report.anomalyCount}
      </TableCell>

      <TableCell sx={bodyCellSx}>
        {report.createdBy ?? "開発ユーザー"}
      </TableCell>

      <TableCell sx={bodyCellSx}>
        <IconButton
          size="small"
          aria-label={`${report.date}の操作`}
          onClick={() => onSelect(report)}
          sx={{
            width: 28,
            height: 28,
          }}
        >
          <MoreVert sx={{ fontSize: 19 }} />
        </IconButton>
      </TableCell>
    </TableRow>
  );
}
