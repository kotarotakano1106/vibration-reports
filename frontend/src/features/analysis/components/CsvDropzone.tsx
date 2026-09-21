import { CloudUploadOutlined } from "@mui/icons-material";
import { Button, Stack, Typography } from "@mui/material";

type CsvDropzoneProps = { onSelect: (file: File) => void };

export function CsvDropzone({ onSelect }: CsvDropzoneProps) {
  return <Stack spacing={1} sx={{ p: 3, border: 1, borderColor: "divider", borderStyle: "dashed", borderRadius: 1.5, alignItems: "center" }}><CloudUploadOutlined color="primary" /><Typography variant="body2">CSVファイルを選択してください</Typography><Button variant="outlined" component="label">ファイルを選択<input hidden type="file" accept=".csv,text/csv" onChange={(event) => { const file = event.target.files?.[0]; if (file) onSelect(file); }} /></Button></Stack>;
}
