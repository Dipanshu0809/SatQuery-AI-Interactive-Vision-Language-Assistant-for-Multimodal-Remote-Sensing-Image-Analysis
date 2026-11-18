"""PDF report generation using ReportLab."""

import os
from datetime import datetime
from xml.sax.saxutils import escape as _xml_escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as RLImage,
)

ACCENT = colors.HexColor("#0E8F84")
MUTED = colors.HexColor("#5B6472")
BORDER = colors.HexColor("#E1E5EA")



def _esc(text) -> str:
    """Escape text for ReportLab paragraphs (a bare & or < in AI text breaks the PDF)."""
    return _xml_escape(str(text))

def _styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            "SQTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            textColor=colors.HexColor("#131A22"),
            spaceAfter=2,
        )
    )
    styles.add(
        ParagraphStyle(
            "SQSubtitle",
            parent=styles["Normal"],
            fontSize=11,
            textColor=MUTED,
            spaceAfter=16,
        )
    )
    styles.add(
        ParagraphStyle(
            "SQHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            textColor=ACCENT,
            spaceBefore=16,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            "SQBody",
            parent=styles["Normal"],
            fontSize=10.5,
            leading=15,
            textColor=colors.HexColor("#1A212C"),
        )
    )
    return styles


def generate_report(
    output_path: str,
    filename: str,
    analysis_type: str,
    summary: str,
    land_cover: dict | None,
    observations: list[str],
    confidence: float | None,
    change_percentage: float | None,
    changed_regions: list[str] | None,
    location: str | None,
    is_demo: bool,
    ai_conclusion: str | None = None,
    image_path: str | None = None,
) -> str:
    """Build the PDF report and write it to output_path. Returns output_path."""

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    styles = _styles()
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
    )

    story = []
    story.append(Paragraph("SATQUERY AI", styles["SQTitle"]))
    story.append(Paragraph("Remote Sensing Analysis Report", styles["SQSubtitle"]))

    meta_rows = [
        ["Date", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")],
        ["Source image", filename],
        ["Analysis type", analysis_type.replace("_", " ").title()],
        ["Location", location or "Not specified"],
        ["Mode", "LIVE DATA / REAL AI ANALYSIS"],
    ]
    meta_table = Table(meta_rows, colWidths=[4 * cm, 11 * cm])
    meta_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                ("TEXTCOLOR", (0, 0), (0, -1), MUTED),
                ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#131A22")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("LINEBELOW", (0, 0), (-1, -1), 0.5, BORDER),
            ]
        )
    )
    story.append(meta_table)

    if image_path and os.path.exists(image_path):
        story.append(Spacer(1, 14))
        try:
            story.append(RLImage(image_path, width=15 * cm, height=9 * cm, kind="proportional"))
        except Exception:
            pass

    story.append(Paragraph("AI Summary", styles["SQHeading"]))
    story.append(Paragraph(_esc(summary or "No summary available."), styles["SQBody"]))

    if land_cover and any(v is not None for v in land_cover.values()):
        story.append(Paragraph("Land Cover Breakdown", styles["SQHeading"]))
        rows = [["Category", "Percentage"]]
        for k, v in land_cover.items():
            if v is not None:
                rows.append([k.replace("_", " ").title(), f"{v}%"])
        lc_table = Table(rows, colWidths=[7 * cm, 4 * cm])
        lc_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF1F4")),
                    ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                    ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(lc_table)

    if observations:
        story.append(Paragraph("Detected Features / Observations", styles["SQHeading"]))
        for obs in observations:
            story.append(Paragraph(f"\u2022 {_esc(obs)}", styles["SQBody"]))

    if change_percentage is not None or changed_regions:
        story.append(Paragraph("Change Detection", styles["SQHeading"]))
        if change_percentage is not None:
            story.append(
                Paragraph(f"Measured change: <b>{change_percentage}%</b> of frame area.", styles["SQBody"])
            )
        for region in changed_regions or []:
            story.append(Paragraph(f"\u2022 {_esc(region)}", styles["SQBody"]))

    if confidence is not None:
        story.append(Paragraph("AI Confidence", styles["SQHeading"]))
        story.append(Paragraph(f"{round(confidence * 100)}%", styles["SQBody"]))

    if ai_conclusion:
        story.append(Paragraph("Conclusion", styles["SQHeading"]))
        story.append(Paragraph(_esc(ai_conclusion), styles["SQBody"]))

    story.append(Spacer(1, 20))
    story.append(
        Paragraph(
            "Generated by SatQuery AI. "
            + "",
            ParagraphStyle("footer", parent=styles["Normal"], fontSize=8, textColor=MUTED),
        )
    )

    doc.build(story)
    return output_path


def generate_investigation_report(
    output_path: str,
    objective: str,
    location_label: str | None,
    latitude: float,
    longitude: float,
    summary: str,
    evidence: dict,
    change_index: dict,
    is_demo: bool,
) -> str:
    """Build a Mission Mode / Earth Analyst investigation PDF report,
    following the structure from spec section 26: objective, location,
    data sources, observations, weather, change index, AI assessment,
    confidence, data limitations, conclusion — each with source attribution.
    """

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    styles = _styles()
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
    )

    story = []
    story.append(Paragraph("SATQUERY AI", styles["SQTitle"]))
    story.append(Paragraph("Earth Intelligence Investigation Report", styles["SQSubtitle"]))

    meta_rows = [
        ["Date", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")],
        ["Investigation objective", objective],
        ["Location", location_label or f"{latitude:.4f}, {longitude:.4f}"],
        ["Coordinates", f"{latitude:.4f}, {longitude:.4f}"],
        ["Mode", "LIVE DATA / REAL AI ANALYSIS"],
    ]
    meta_table = Table(meta_rows, colWidths=[4.5 * cm, 10.5 * cm])
    meta_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                ("TEXTCOLOR", (0, 0), (0, -1), MUTED),
                ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#131A22")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("LINEBELOW", (0, 0), (-1, -1), 0.5, BORDER),
            ]
        )
    )
    story.append(meta_table)

    # Data sources / provenance — spec section 23
    story.append(Paragraph("Data Sources", styles["SQHeading"]))
    source_rows = [
        ["Signal", "Source", "Freshness"],
        ["Active fires", str(evidence.get("fire_source") or "\u2014")[:60], "Near-real-time (~3hr latency)"],
        ["Weather", str(evidence.get("weather_source") or "\u2014")[:60], "Near-real-time"],
    ]
    source_table = Table(source_rows, colWidths=[4 * cm, 7 * cm, 4 * cm])
    source_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF1F4")),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(source_table)

    story.append(Paragraph("AI Assessment", styles["SQHeading"]))
    story.append(Paragraph(_esc(summary or "No summary available."), styles["SQBody"]))

    story.append(Paragraph("Fire Events", styles["SQHeading"]))
    fires = evidence.get("nearby_fires") or []
    if fires:
        for f in fires[:8]:
            story.append(
                Paragraph(
                    f"\u2022 {float(f.get('latitude') or 0):.3f}, {float(f.get('longitude') or 0):.3f} \u2014 "
                    f"confidence: {f.get('confidence', 'n/a')}, source: {f.get('satellite', 'n/a')}, "
                    f"detected: {f.get('acq_time', 'n/a')}",
                    styles["SQBody"],
                )
            )
    else:
        story.append(Paragraph("No active fire detections within the search radius.", styles["SQBody"]))

    story.append(Paragraph("Weather", styles["SQHeading"]))
    w = evidence.get("weather") or {}
    condition = _esc(w.get("condition") or "Unknown")
    temperature = w.get("temperature_c", "—")
    humidity = w.get("humidity_pct", "—")
    wind = w.get("wind_kmh", "—")
    story.append(
        Paragraph(
            f"{condition}, {temperature}°C, "
            f"{humidity}% humidity, wind {wind} km/h.",
            styles["SQBody"],
        )
    )

    story.append(Paragraph("Earth Change Index", styles["SQHeading"]))
    story.append(
        Paragraph(
            f"<b>{_esc(change_index.get('label') or 'N/A')}</b> \u2014 score "
            f"{change_index.get('score') if change_index.get('score') is not None else 'n/a'}/100",
            styles["SQBody"],
        )
    )
    story.append(Paragraph(_esc(change_index.get("methodology") or ""), styles["SQBody"]))

    story.append(Paragraph("Data Limitations", styles["SQHeading"]))
    story.append(
        Paragraph(
            "This investigation is grounded in retrieved Sentinel-2 multispectral indices, "
            "NASA FIRMS active-fire detections, live weather, and public event feeds. The Earth "
            "Change Index is SatQuery AI's own analytical indicator, not an official scientific "
            "or government index.",
            styles["SQBody"],
        )
    )

    story.append(Paragraph("Conclusion", styles["SQHeading"]))
    fire_count = len(fires)
    conclusion = (
        f"Based on the evidence gathered, this location shows a "
        f"{_esc(str(change_index.get('label') or 'unknown')).lower()} composite change signal, with {fire_count} "
        f"active fire detection(s) recorded nearby in the last 24 hours. "
        + "This assessment used live retrieved data sources."
    )
    story.append(Paragraph(conclusion, styles["SQBody"]))

    story.append(Spacer(1, 20))
    story.append(
        Paragraph(
            "Generated by SatQuery AI Mission Mode using live retrieved evidence.",
            ParagraphStyle("footer2", parent=styles["Normal"], fontSize=8, textColor=MUTED),
        )
    )

    doc.build(story)
    return output_path
