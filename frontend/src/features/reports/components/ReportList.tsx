import { Search } from "@mui/icons-material";
import {
  Box,
  Card,
  InputAdornment,
  MenuItem,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";

import { ReportListItem } from "./ReportListItem";
import type { Report } from "../types/report";


type ReportListProps = {
  reports: Report[];
  onSelect: (report: Report) => void;
};


const headerCellSx = {
  py: 1.5,
  px: 1,
  color: "text.secondary",
  fontSize: 12,
  fontWeight: 700,
  textAlign: "center",
  whiteSpace: "nowrap",
} as const;


export function ReportList({
  reports,
  onSelect,
}: ReportListProps) {
  return (
    <Card
      sx={{
        minHeight: 0,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Stack
        direction="row"
        spacing={1.5}
        sx={{
          minHeight: 74,
          px: 1.5,
          alignItems: "center",
          borderBottom: 1,
          borderColor: "divider",
        }}
      >
        <Typography
          variant="h6"
          sx={{
            fontWeight: 700,
            color: "primary.dark",
          }}
        >
          レポート一覧
        </Typography>

        <Box sx={{ flex: 1 }} />

        <TextField
          size="small"
          placeholder="レポート名、設備IDで検索"
          sx={{ width: 400 }}
          slotProps={{
            input: {
              startAdornment: (
                <InputAdornment position="start">
                  <Search color="action" />
                </InputAdornment>
              ),
            },
          }}
        />

        <Select
          size="small"
          value="all"
          sx={{ width: 168 }}
        >
          <MenuItem value="all">すべて</MenuItem>
        </Select>
      </Stack>

      <TableContainer sx={{ flex: 1 }}>
        <Table
          stickyHeader
          size="small"
          sx={{ tableLayout: "fixed" }}
        >
          <TableHead>
            <TableRow>
              <TableCell sx={{ ...headerCellSx, width: "12%" }}>
                作成日 ↓
              </TableCell>
              <TableCell sx={{ ...headerCellSx, width: "12%" }}>
                対象期間
              </TableCell>
              <TableCell sx={{ ...headerCellSx, width: "13%" }}>
                設備ID
              </TableCell>
              <TableCell sx={{ ...headerCellSx, width: "19%" }}>
                使用ファイル
              </TableCell>
              <TableCell sx={{ ...headerCellSx, width: "11%" }}>
                分析結果
              </TableCell>
              <TableCell sx={{ ...headerCellSx, width: "9%" }}>
                異常件数
              </TableCell>
              <TableCell sx={{ ...headerCellSx, width: "16%" }}>
                作成者
              </TableCell>
              <TableCell sx={{ ...headerCellSx, width: "8%" }}>
                操作
              </TableCell>
            </TableRow>
          </TableHead>

          <TableBody>
            {reports.map((report, index) => (
              <ReportListItem
                key={`${report.date}-${report.file}-${index}`}
                report={report}
                onSelect={onSelect}
              />
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <TablePagination
        component="div"
        count={reports.length}
        page={0}
        rowsPerPage={3}
        rowsPerPageOptions={[]}
        onPageChange={() => undefined}
        labelDisplayedRows={({ from, to, count }) =>
          `${count}件中 ${from}-${to}件`
        }
        sx={{
          borderTop: 1,
          borderColor: "divider",
          ".MuiTablePagination-toolbar": {
            justifyContent: "flex-end",
          },
          ".MuiTablePagination-spacer": {
            display: "none",
          },
        }}
      />
    </Card>
  );
}
