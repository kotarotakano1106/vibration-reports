import { DescriptionOutlined } from "@mui/icons-material";
import { Box, Stack, Typography } from "@mui/material";

type CsvFilePreviewProps = { file: File };

export function CsvFilePreview({ file }: CsvFilePreviewProps) {
  return <Stack direction="row" spacing={1} sx={{ mt: 2, p: 1.5, bgcolor: "background.default", alignItems: "center" }}><DescriptionOutlined color="primary" /><Box><Typography variant="body2" sx={{ fontWeight: 700 }}>{file.name}</Typography><Typography variant="caption" color="text.secondary">{Math.ceil(file.size / 1024)} KB</Typography></Box></Stack>;
}
