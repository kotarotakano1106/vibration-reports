"""振動分析レポートをPDFとして生成するService。"""

from __future__ import annotations

import csv
from datetime import datetime
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    KeepTogether,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from backend.src.repositories.report_repository import ReportRepository
from backend.src.repositories.uploaded_file_repository import (
    UploadedFileRepository,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PDF_FONT = "HeiseiKakuGo-W5"


class ReportPdfServiceError(Exception):
    """PDF生成Serviceの共通エラー。"""


class ReportPdfNotFoundError(ReportPdfServiceError):
    """対象レポートが存在しない場合のエラー。"""


class ReportPdfSourceFileError(ReportPdfServiceError):
    """測定CSVを読み込めない場合のエラー。"""


class VibrationChart(Flowable):
    """ReportLab上に振動推移を描画するFlowable。"""

    def __init__(self, values: list[float], threshold: float | None):
        super().__init__()
        self.values = values
        self.threshold = threshold
        self.width = 174 * mm
        self.height = 47 * mm

    def draw(self):
        canvas = self.canv
        left = 12 * mm
        bottom = 9 * mm
        width = self.width - 18 * mm
        height = self.height - 15 * mm

        canvas.setStrokeColor(colors.HexColor("#D7DFEA"))
        canvas.setLineWidth(0.6)
        canvas.rect(left, bottom, width, height, stroke=1, fill=0)

        if not self.values:
            canvas.setFont(PDF_FONT, 9)
            canvas.drawCentredString(
                left + width / 2,
                bottom + height / 2,
                "測定データを取得できませんでした。",
            )
            return

        maximum = max(self.values)
        if self.threshold is not None:
            maximum = max(maximum, self.threshold)
        maximum = max(maximum * 1.15, 1.0)

        def point(index: int, value: float) -> tuple[float, float]:
            x = left if len(self.values) == 1 else (left + width * index / (len(self.values) - 1))
            y = bottom + height * value / maximum
            return x, y

        for ratio in (0.25, 0.5, 0.75):
            y = bottom + height * ratio
            canvas.setStrokeColor(colors.HexColor("#EEF2F7"))
            canvas.line(left, y, left + width, y)

        if self.threshold is not None:
            threshold_y = bottom + height * self.threshold / maximum
            canvas.setStrokeColor(colors.HexColor("#E53935"))
            canvas.setDash(4, 3)
            canvas.line(left, threshold_y, left + width, threshold_y)
            canvas.setDash()

        canvas.setStrokeColor(colors.HexColor("#1976D2"))
        canvas.setLineWidth(1.4)
        path = canvas.beginPath()
        first_x, first_y = point(0, self.values[0])
        path.moveTo(first_x, first_y)
        for index, value in enumerate(self.values[1:], start=1):
            x, y = point(index, value)
            path.lineTo(x, y)
        canvas.drawPath(path, stroke=1, fill=0)

        for index, value in enumerate(self.values):
            x, y = point(index, value)
            exceeded = self.threshold is not None and value > self.threshold
            canvas.setFillColor(
                colors.HexColor("#E53935") if exceeded else colors.HexColor("#1976D2")
            )
            canvas.circle(x, y, 1.6, stroke=0, fill=1)

        canvas.setFont(PDF_FONT, 7)
        canvas.setFillColor(colors.HexColor("#64748B"))
        canvas.drawString(left, 2 * mm, "測定開始")
        canvas.drawRightString(left + width, 2 * mm, "測定終了")
        canvas.drawRightString(left - 2 * mm, bottom, "0")
        canvas.drawRightString(left - 2 * mm, bottom + height, f"{maximum:.2f}")


class ReportPdfService:
    """保存済みReportとCSVからPDFを生成する。"""

    def __init__(self, session):
        self._report_repository = ReportRepository(session)
        self._file_repository = UploadedFileRepository(session)

        pdfmetrics.registerFont(UnicodeCIDFont(PDF_FONT))
        pdfmetrics.registerFontFamily(
            PDF_FONT,
            normal=PDF_FONT,
            bold=PDF_FONT,
            italic=PDF_FONT,
            boldItalic=PDF_FONT,
        )

    def generate(self, report_id) -> tuple[bytes, str]:
        report = self._report_repository.get_by_id(report_id)
        if report is None:
            raise ReportPdfNotFoundError(f"レポートが存在しません。 report_id={report_id}")

        uploaded_file = self._file_repository.get_by_id(report.uploaded_file_id)
        if uploaded_file is None:
            raise ReportPdfSourceFileError("レポートに対応するCSV管理情報が存在しません。")

        values = self._load_values(
            uploaded_file.file_path,
            uploaded_file.encoding,
        )
        buffer = BytesIO()
        self._build_pdf(buffer, report, uploaded_file, values)

        date_text = (
            report.measurement_date.isoformat()
            if report.measurement_date is not None
            else "date-unset"
        )
        safe_equipment_id = "".join(
            character if character.isalnum() or character in "-_" else "_"
            for character in report.equipment_id
        )
        filename = f"vibration-report_{safe_equipment_id}_{date_text}.pdf"
        return buffer.getvalue(), filename

    def _build_pdf(self, buffer, report, uploaded_file, values):
        page_width, page_height = A4
        frame = Frame(
            15 * mm,
            14 * mm,
            page_width - 30 * mm,
            page_height - 27 * mm,
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
        )
        document = BaseDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=15 * mm,
            rightMargin=15 * mm,
            topMargin=13 * mm,
            bottomMargin=14 * mm,
            title=report.title,
            author="振動AI日報生成アプリ",
        )
        document.addPageTemplates(
            PageTemplate(
                id="report",
                frames=[frame],
                onPage=self._draw_page_footer,
            )
        )

        styles = self._styles()
        story = []
        story.extend(self._header(report, uploaded_file, styles))
        story.extend(self._summary(report, styles))
        story.extend(
            [
                self._section_title("02", "振動値推移", styles),
                VibrationChart(values, report.threshold_value),
                Paragraph(
                    "青: 測定値　赤: 閾値超過　破線: 閾値",
                    styles["caption"],
                ),
                Spacer(1, 3 * mm),
            ]
        )
        story.extend(self._anomalies(report, styles))
        story.extend(self._analysis(report, styles))
        story.extend(self._recommendation(report, styles))
        document.build(story)

    @staticmethod
    def _draw_page_footer(canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#CBD5E1"))
        canvas.line(15 * mm, 10 * mm, 195 * mm, 10 * mm)
        canvas.setFont(PDF_FONT, 7)
        canvas.setFillColor(colors.HexColor("#64748B"))
        canvas.drawString(15 * mm, 6 * mm, "振動AI日報生成アプリ")
        canvas.drawRightString(
            195 * mm,
            6 * mm,
            f"{document.page}",
        )
        canvas.restoreState()

    @staticmethod
    def _styles():
        styles = getSampleStyleSheet()
        return {
            "eyebrow": ParagraphStyle(
                "eyebrow",
                parent=styles["Normal"],
                fontName=PDF_FONT,
                fontSize=7,
                textColor=colors.HexColor("#64748B"),
                leading=9,
            ),
            "title": ParagraphStyle(
                "title",
                parent=styles["Title"],
                fontName=PDF_FONT,
                fontSize=20,
                leading=24,
                alignment=TA_LEFT,
                textColor=colors.HexColor("#0F172A"),
                spaceAfter=4,
            ),
            "section": ParagraphStyle(
                "section",
                parent=styles["Heading2"],
                fontName=PDF_FONT,
                fontSize=11,
                leading=14,
                textColor=colors.HexColor("#0F172A"),
            ),
            "body": ParagraphStyle(
                "body",
                parent=styles["BodyText"],
                fontName=PDF_FONT,
                fontSize=8.5,
                leading=13,
                textColor=colors.HexColor("#334155"),
                wordWrap="CJK",
            ),
            "caption": ParagraphStyle(
                "caption",
                parent=styles["Normal"],
                fontName=PDF_FONT,
                fontSize=7,
                leading=10,
                textColor=colors.HexColor("#64748B"),
            ),
            "metric": ParagraphStyle(
                "metric",
                parent=styles["Normal"],
                fontName=PDF_FONT,
                fontSize=12,
                leading=15,
                alignment=TA_CENTER,
                textColor=colors.HexColor("#0F172A"),
            ),
        }

    def _header(self, report, uploaded_file, styles):
        status_label = self._status_label(report.status)
        status_color = (
            colors.HexColor("#C62828")
            if report.status == "requires_attention"
            else colors.HexColor("#2E7D32")
        )
        metadata = [
            ["STATUS", status_label, "天気", report.weather or "未設定"],
            ["測定日", self._date_text(report.measurement_date), "対象設備ID", report.equipment_id],
            [
                "使用ファイル",
                uploaded_file.original_filename,
                "作成日時",
                self._datetime_text(report.created_at),
            ],
        ]
        table = Table(
            metadata,
            colWidths=[23 * mm, 56 * mm, 27 * mm, 68 * mm],
        )
        table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), PDF_FONT),
                    ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#334155")),
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F1F5F9")),
                    ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#F1F5F9")),
                    ("TEXTCOLOR", (1, 0), (1, 0), status_color),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#D7DFEA")),
                ]
            )
        )
        return [
            Paragraph("VIBRATION MONITORING / DAILY REPORT", styles["eyebrow"]),
            Paragraph("振動測定結果報告書", styles["title"]),
            Paragraph(f"REPORT ID　{report.id}", styles["caption"]),
            Spacer(1, 3 * mm),
            table,
            Spacer(1, 4 * mm),
            Paragraph(self._paragraph_text(report.ai_summary), styles["body"]),
            Spacer(1, 4 * mm),
        ]

    def _summary(self, report, styles):
        table = Table(
            [
                ["MIN", "MAX", "AVERAGE", "EXCEEDANCES"],
                [
                    f"{report.minimum_value:.2f}",
                    f"{report.maximum_value:.2f}",
                    f"{report.average_value:.3f}",
                    f"{report.anomaly_count}件",
                ],
            ],
            colWidths=[43.5 * mm] * 4,
        )
        table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), PDF_FONT),
                    ("FONTNAME", (0, 1), (-1, 1), PDF_FONT),
                    ("FONTSIZE", (0, 0), (-1, 0), 7),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#64748B")),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                    ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#D7DFEA")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E2E8F0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        return [
            self._section_title("01", "測定サマリー", styles),
            table,
            Spacer(1, 4 * mm),
        ]

    def _anomalies(self, report, styles):
        rows = [["検出時刻", "振動値", "閾値との差", "判定"]]
        for detail in report.anomaly_details:
            rows.append(
                [
                    self._anomaly_time(detail.get("measured_at")),
                    f"{float(detail.get('value', 0)):.2f}",
                    f"+{float(detail.get('excess_value', 0)):.2f}",
                    "閾値超過",
                ]
            )
        if len(rows) == 1:
            rows.append(["-", "-", "-", "異常候補なし"])

        table = Table(rows, colWidths=[55 * mm, 35 * mm, 40 * mm, 44 * mm], repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), PDF_FONT),
                    ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("TEXTCOLOR", (3, 1), (3, -1), colors.HexColor("#C62828")),
                    ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#F8FAFC")],
                    ),
                    ("LINEBELOW", (0, 1), (-1, -1), 0.4, colors.HexColor("#E2E8F0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        return [
            self._section_title("03", "異常候補", styles),
            table,
            Spacer(1, 4 * mm),
        ]

    def _analysis(self, report, styles):
        assessment = self._status_label(report.status)
        return [
            self._section_title("04", "分析結果", styles),
            Paragraph(
                self._paragraph_text(report.ai_summary),
                styles["body"],
            ),
            Spacer(1, 2 * mm),
            Table(
                [["ASSESSMENT", assessment]],
                colWidths=[34 * mm, 140 * mm],
                style=TableStyle(
                    [
                        ("FONTNAME", (0, 0), (-1, -1), PDF_FONT),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#0F172A")),
                        ("TEXTCOLOR", (0, 0), (0, 0), colors.white),
                        ("TEXTCOLOR", (1, 0), (1, 0), colors.HexColor("#C62828")),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#CBD5E1")),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ]
                ),
            ),
            Spacer(1, 4 * mm),
        ]

    def _recommendation(self, report, styles):
        recommendation = report.recommendation or "推奨対応はありません。"
        lines = [line.strip(" -") for line in recommendation.splitlines() if line.strip()]
        if not lines:
            lines = [recommendation]
        items = []
        for index, line in enumerate(lines, start=1):
            items.append(
                Table(
                    [[f"{index:02d}", Paragraph(escape(line), styles["body"])]],
                    colWidths=[13 * mm, 161 * mm],
                    style=TableStyle(
                        [
                            ("FONTNAME", (0, 0), (0, 0), PDF_FONT),
                            ("FONTSIZE", (0, 0), (0, 0), 9),
                            ("TEXTCOLOR", (0, 0), (0, 0), colors.HexColor("#1976D2")),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                        ]
                    ),
                )
            )
        return [
            self._section_title("05", "推奨対応", styles),
            KeepTogether(items),
            Spacer(1, 2 * mm),
            Paragraph(
                "備考: AI分析結果は保全判断を補助する情報です。最終判断は現場で確認してください。",
                styles["caption"],
            ),
        ]

    @staticmethod
    def _section_title(number, title, styles):
        return Table(
            [[number, Paragraph(title, styles["section"])]],
            colWidths=[13 * mm, 161 * mm],
            style=TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, 0), PDF_FONT),
                    ("FONTSIZE", (0, 0), (0, 0), 12),
                    ("TEXTCOLOR", (0, 0), (0, 0), colors.HexColor("#1976D2")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LINEBELOW", (0, 0), (-1, -1), 0.8, colors.HexColor("#CBD5E1")),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                ]
            ),
        )

    @staticmethod
    def _load_values(stored_path, encoding):
        path = Path(stored_path)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        if not path.exists():
            raise ReportPdfSourceFileError(f"CSV実ファイルが存在しません。 path={path}")

        values = []
        try:
            with path.open(
                "r",
                encoding=encoding or "UTF-8",
                newline="",
            ) as file:
                for row in csv.DictReader(file):
                    values.append(float(row["vibration_value"]))
        except (OSError, KeyError, ValueError, UnicodeError) as exc:
            raise ReportPdfSourceFileError("PDF用の測定CSVを読み込めませんでした。") from exc
        return values

    @staticmethod
    def _paragraph_text(value):
        text = str(value or "AI分析はありません。")
        text = text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
        return "<br/>".join(escape(line.strip("# ")) for line in text.splitlines() if line.strip())

    @staticmethod
    def _status_label(status):
        return {
            "requires_attention": "要確認",
            "warning": "注意",
            "normal": "正常",
        }.get(status, status or "未設定")

    @staticmethod
    def _date_text(value):
        return value.strftime("%Y年%m月%d日") if value else "未設定"

    @staticmethod
    def _datetime_text(value):
        if value is None:
            return "未設定"
        return value.astimezone().strftime("%Y年%m月%d日 %H:%M")

    @staticmethod
    def _anomaly_time(value):
        if not value:
            return "-"
        try:
            return datetime.fromisoformat(str(value)).astimezone().strftime("%H:%M:%S")
        except ValueError:
            return str(value)
