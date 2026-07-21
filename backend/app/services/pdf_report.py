from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models import Incident


def generate_incident_pdf(context: dict) -> bytes:
    incident: Incident = context["incident"]
    format_dt = context["format_dt"]
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"Reporte Incidente INC-{incident.id:04d}",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=colors.HexColor("#0f766e"),
        alignment=TA_CENTER,
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#64748b"),
        alignment=TA_CENTER,
        spaceAfter=20,
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=14,
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        alignment=TA_LEFT,
    )

    story = []

    story.append(Paragraph("SecOps Hub", title_style))
    story.append(Paragraph("Executive Incident Report", subtitle_style))
    story.append(Spacer(1, 0.3 * cm))

    summary_data = [
        ["ID Incidente", f"INC-{incident.id:04d}"],
        ["Fecha/Hora deteccion", format_dt(incident.created_at)],
        ["Severidad", incident.severity.upper()],
        ["Estado", incident.status.upper()],
        ["Activo afectado", context["affected_asset"]],
        ["Origen", incident.source or "N/A"],
        ["Asignado a", incident.assigned_to or "N/A"],
        ["Titulo", incident.title],
    ]
    summary_table = Table(summary_data, colWidths=[5 * cm, 12 * cm])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#ecfdf5")),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#065f46")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(Paragraph("Resumen ejecutivo", section_style))
    story.append(summary_table)

    if incident.description:
        story.append(Spacer(1, 0.4 * cm))
        story.append(Paragraph("Descripcion", section_style))
        story.append(Paragraph(incident.description, body_style))

    story.append(Paragraph("Cronologia de eventos", section_style))
    timeline = context["timeline"]
    if timeline:
        timeline_rows = [["Fecha/Hora", "Evento", "Detalle"]]
        for event in timeline:
            timeline_rows.append(
                [
                    format_dt(event["timestamp"]),
                    event["label"],
                    (event["detail"] or "")[:120],
                ]
            )
        timeline_table = Table(timeline_rows, colWidths=[3.5 * cm, 4.5 * cm, 9 * cm])
        timeline_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(timeline_table)
    else:
        story.append(Paragraph("No hay eventos registrados.", body_style))

    story.append(Paragraph("Indicadores de Compromiso (IOCs)", section_style))
    iocs = context["iocs"]
    if iocs:
        ioc_rows = [["Valor", "Tipo", "Riesgo", "Veredicto", "Bloqueado"]]
        for ioc in iocs:
            ioc_rows.append(
                [
                    ioc.value,
                    ioc.ioc_type.upper(),
                    str(ioc.risk_score),
                    (ioc.verdict or "N/A").upper(),
                    "Si" if ioc.blocked else "No",
                ]
            )
        ioc_table = Table(ioc_rows, colWidths=[5 * cm, 2.5 * cm, 2 * cm, 3 * cm, 2.5 * cm])
        ioc_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#881337")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(ioc_table)
    else:
        story.append(
            Paragraph("No se encontraron IOCs asociados a este incidente.", body_style)
        )

    story.append(Paragraph("Medidas de contencion aplicadas", section_style))
    for measure in context["containment"]:
        story.append(Paragraph(f"• {measure}", body_style))
        story.append(Spacer(1, 0.15 * cm))

    story.append(Spacer(1, 0.8 * cm))
    story.append(Paragraph("Cierre y conformidad", section_style))
    closure_text = (
        f"Informe generado por el analista <b>{context['analyst_username']}</b> "
        f"mediante SecOps Hub. Documento emitido para fines de auditoria interna "
        f"y respuesta a incidentes de seguridad."
    )
    story.append(Paragraph(closure_text, body_style))
    story.append(Spacer(1, 1.2 * cm))

    signature_data = [
        ["Firma digital / Analista", context["analyst_username"]],
        ["Fecha de cierre", format_dt(context.get("generated_at"))],
        ["Estado del informe", "Emitido - Conforme"],
    ]
    signature_table = Table(signature_data, colWidths=[5 * cm, 12 * cm])
    signature_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(signature_table)

    doc.build(story)
    return buffer.getvalue()
