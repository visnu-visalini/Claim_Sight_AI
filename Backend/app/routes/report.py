import io
import os
from datetime import datetime

from flask import Blueprint, request, send_file, jsonify

from app.models.claim import Claim
from app.models.claim_image import ClaimImage
from app.models.user import User
from app.cost_estimation import estimate_claim
from app.routes.generate import build_summary

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image as RLImage,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER


report_bp = Blueprint("report", __name__)

# ── Design tokens (match ClaimSightAI dark navy + blue palette) ───────────
NAVY  = colors.HexColor("#0f172a")
BLUE  = colors.HexColor("#2563eb")
SLATE = colors.HexColor("#64748b")
LIGHT = colors.HexColor("#f1f5f9")
WHITE = colors.white
RED   = colors.HexColor("#dc2626")
GREEN = colors.HexColor("#16a34a")

PAGE_W, PAGE_H = A4
MARGIN = 20 * mm


def _fmt_date(iso):
    if not iso:
        return "—"
    try:
        return datetime.fromisoformat(iso).strftime("%d %b %Y")
    except Exception:
        return str(iso)


def _fmt_inr(value):
    if value is None:
        return "—"
    return f"\u20b9{value:,}"


def _val(v):
    return str(v) if v not in (None, "", 0) else "—"


def _status_color(status):
    return {
        "draft":     BLUE,
        "submitted": GREEN,
        "approved":  GREEN,
        "rejected":  RED,
    }.get((status or "").lower(), SLATE)


# ── Styles ────────────────────────────────────────────────────────────────

def _build_styles():
    base = getSampleStyleSheet()

    styles = {
        "title": ParagraphStyle(
            "title",
            fontSize=22, fontName="Helvetica-Bold",
            textColor=WHITE, alignment=TA_CENTER, spaceAfter=2,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            fontSize=10, fontName="Helvetica",
            textColor=colors.HexColor("#cbd5e1"),
            alignment=TA_CENTER, spaceAfter=0,
        ),
        "section": ParagraphStyle(
            "section",
            fontSize=11, fontName="Helvetica-Bold",
            textColor=NAVY, spaceBefore=10, spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "body",
            fontSize=9, fontName="Helvetica",
            textColor=NAVY, leading=14,
        ),
        "small": ParagraphStyle(
            "small",
            fontSize=8, fontName="Helvetica",
            textColor=SLATE, leading=12,
        ),
        "summary": ParagraphStyle(
            "summary",
            fontSize=9, fontName="Helvetica",
            textColor=colors.HexColor("#334155"),
            leading=15, spaceBefore=4,
        ),
        "disclaimer": ParagraphStyle(
            "disclaimer",
            fontSize=8, fontName="Helvetica-Oblique",
            textColor=SLATE, leading=12, spaceBefore=4,
        ),
    }
    return styles


# ── Table helpers ─────────────────────────────────────────────────────────

def _info_table(rows, styles):
    """Two-column label/value table used throughout the report."""
    data = [
        [
            Paragraph(label, styles["small"]),
            Paragraph(str(value), styles["body"]),
        ]
        for label, value in rows
    ]
    t = Table(data, colWidths=[45 * mm, PAGE_W - 2 * MARGIN - 45 * mm])
    t.setStyle(TableStyle([
        ("VALIGN",      (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING",  (0, 0), (-1, -1), 3),
        ("LINEBELOW",   (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0")),
    ]))
    return t


def _damage_table(images, styles):
    """One row per damaged image."""
    header = [
        Paragraph("View", styles["small"]),
        Paragraph("Image", styles["small"]),
        Paragraph("Damage Type", styles["small"]),
        Paragraph("Confidence", styles["small"]),
        Paragraph("Detected", styles["small"]),
    ]
    rows = [header]
    for img in images:
        conf     = f"{round(img.confidence * 100)}%" if img.confidence is not None else "—"
        detected = "Yes" if img.damage_detected else "No"
        view     = (img.vehicle_view or "—").capitalize()
        rows.append([
            Paragraph(view, styles["body"]),
            Paragraph(img.filename or "—", styles["small"]),
            Paragraph(_val(img.damage_type).capitalize(), styles["body"]),
            Paragraph(conf, styles["body"]),
            Paragraph(detected, styles["body"]),
        ])

    col_w = (PAGE_W - 2 * MARGIN) / 5
    t = Table(rows, colWidths=[col_w] * 5)
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), LIGHT),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 8),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, colors.HexColor("#f8fafc")]),
        ("GRID",        (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0")),
        ("TOPPADDING",  (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def _cost_table(cost, styles):
    """Cost estimation summary table."""
    rows_data = [
        ["Estimated Min",     _fmt_inr(cost["total_estimated_min"])],
        ["Estimated Max",     _fmt_inr(cost["total_estimated_max"])],
        ["Estimated Average", _fmt_inr(cost["total_estimated_average"])],
    ]
    data = [
        [Paragraph(r[0], styles["small"]), Paragraph(r[1], styles["body"])]
        for r in rows_data
    ]
    t = Table(data, colWidths=[60 * mm, 60 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 2), (-1, 2), LIGHT),
        ("FONTNAME",      (0, 2), (-1, 2), "Helvetica-Bold"),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0")),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


# ── Header banner ─────────────────────────────────────────────────────────

def _header_banner(claim, claimant, styles):
    """Dark navy banner drawn as a single-cell table."""
    status      = (claim.status or "unknown").upper()
    status_col  = _status_color(claim.status)

    title_para    = Paragraph("ClaimSightAI", styles["title"])
    subtitle_para = Paragraph(
        "AI-Powered Vehicle Insurance Claim Report", styles["subtitle"]
    )

    banner = Table(
        [[title_para], [subtitle_para]],
        colWidths=[PAGE_W - 2 * MARGIN],
    )
    banner.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), NAVY),
        ("TOPPADDING",    (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
    ]))
    return banner


# ── PDF builder ───────────────────────────────────────────────────────────

def generate_pdf(claim, claimant, images, cost):
    buf    = io.BytesIO()
    styles = _build_styles()

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN,  bottomMargin=MARGIN,
        title=f"ClaimSightAI Report — Claim #{claim.id}",
        author="ClaimSightAI",
    )

    story = []

    # ── Banner ──
    story.append(_header_banner(claim, claimant, styles))
    story.append(Spacer(1, 6 * mm))

    # ── Claim overview ──
    story.append(Paragraph("Claim Overview", styles["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT))
    story.append(Spacer(1, 2 * mm))

    created  = _fmt_date(claim.created_at.isoformat()  if claim.created_at  else None)
    submitted = _fmt_date(claim.submitted_at.isoformat() if claim.submitted_at else None)

    story.append(_info_table([
        ("Claim ID",       f"#{claim.id}"),
        ("Status",         (claim.status or "—").upper()),
        ("Created",        created),
        ("Submitted",      submitted),
        ("Claimant Name",  claimant.name  if claimant else "—"),
        ("Claimant Email", claimant.email if claimant else "—"),
    ], styles))

    story.append(Spacer(1, 5 * mm))

    # ── Vehicle ──
    story.append(Paragraph("Vehicle Information", styles["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT))
    story.append(Spacer(1, 2 * mm))

    story.append(_info_table([
        ("Registration",  _val(claim.vehicle_number)),
        ("Make",          _val(claim.vehicle_make)),
        ("Model",         _val(claim.vehicle_model)),
        ("Year",          _val(claim.vehicle_year)),
    ], styles))

    story.append(Spacer(1, 5 * mm))

    # ── Accident ──
    story.append(Paragraph("Accident Details", styles["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT))
    story.append(Spacer(1, 2 * mm))

    acc_date = _fmt_date(
        claim.accident_date.isoformat() if claim.accident_date else None
    )
    story.append(_info_table([
        ("Date",        acc_date),
        ("Location",    _val(claim.accident_location)),
        ("Description", _val(claim.accident_description)),
    ], styles))

    story.append(Spacer(1, 5 * mm))

    # ── AI Damage Detection ──
    story.append(Paragraph("AI Damage Detection Results", styles["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT))
    story.append(Spacer(1, 2 * mm))

    damaged = [img for img in images if img.damage_detected]
    story.append(_info_table([
        ("Total Images Uploaded", str(len(images))),
        ("Images with Damage",    str(len(damaged))),
        ("Damage Detected",       "Yes" if cost["has_damage"] else "No"),
    ], styles))

    story.append(Spacer(1, 3 * mm))

    if images:
        story.append(_damage_table(images, styles))

    # Embed up to 3 damage images if files exist on disk
    if damaged:
        story.append(Spacer(1, 4 * mm))
        story.append(Paragraph("Damage Images", styles["section"]))
        story.append(Spacer(1, 2 * mm))

        img_row = []
        for img in damaged[:3]:
            if img.file_path and os.path.exists(img.file_path):
                try:
                    rl_img = RLImage(img.file_path, width=55 * mm, height=42 * mm)
                    rl_img.hAlign = "LEFT"
                    img_row.append(rl_img)
                except Exception:
                    pass

        if img_row:
            # Pad row to 3 cells so the table stays balanced
            while len(img_row) < 3:
                img_row.append("")
            img_table = Table([img_row], colWidths=[(PAGE_W - 2 * MARGIN) / 3] * 3)
            img_table.setStyle(TableStyle([
                ("VALIGN",  (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 3),
            ]))
            story.append(img_table)

    story.append(Spacer(1, 5 * mm))

    # ── Cost Estimation ──
    story.append(Paragraph("Cost Estimation", styles["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT))
    story.append(Spacer(1, 2 * mm))

    if cost["has_damage"]:
        story.append(_cost_table(cost, styles))
        if cost.get("has_unknown_damage"):
            story.append(Spacer(1, 2 * mm))
            story.append(Paragraph(
                "Note: One or more damage types could not be estimated. "
                "Manual assessment is recommended.",
                styles["disclaimer"],
            ))
    else:
        story.append(Paragraph("No damage detected — no cost estimate applicable.", styles["body"]))

    story.append(Spacer(1, 5 * mm))

    # ── AI Summary ──
    story.append(Paragraph("AI Claim Summary", styles["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT))
    story.append(Spacer(1, 2 * mm))

    summary_text = build_summary(claim, images, cost)
    for para in summary_text.split("\n\n"):
        para = para.strip()
        if para:
            story.append(Paragraph(para, styles["summary"]))
            story.append(Spacer(1, 2 * mm))

    story.append(Spacer(1, 5 * mm))

    # ── Footer disclaimer ──
    story.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(
        "This report was generated by ClaimSightAI, an AI-assisted prototype "
        "for research and demonstration purposes. AI-generated assessments, "
        "repair estimates, and recommendations must be validated by qualified "
        "insurance professionals before use in real-world claim decisions. "
        f"Generated: {datetime.utcnow().strftime('%d %b %Y %H:%M UTC')}",
        styles["disclaimer"],
    ))

    doc.build(story)
    buf.seek(0)
    return buf


# ── Endpoint ──────────────────────────────────────────────────────────────

@report_bp.route("/<int:claim_id>/report", methods=["GET"])
def download_report(claim_id):

    user_id = request.args.get("user_id", type=int)

    if not user_id:
        return jsonify({"success": False, "message": "user_id is required"}), 400

    claim = Claim.query.get(claim_id)

    if not claim:
        return jsonify({"success": False, "message": "Claim not found"}), 404

    # Auth: owner OR admin
    requester = User.query.get(user_id)

    if not requester:
        return jsonify({"success": False, "message": "User not found"}), 404

    is_owner = claim.user_id == user_id
    is_admin = requester.role == "admin"

    if not is_owner and not is_admin:
        return jsonify({
            "success": False,
            "message": "You are not authorized to download this report",
        }), 403

    claimant = User.query.get(claim.user_id)
    images   = ClaimImage.query.filter_by(claim_id=claim_id).all()
    cost     = estimate_claim(images)

    pdf_buf = generate_pdf(claim, claimant, images, cost)

    filename = f"ClaimSightAI_{claim_id}_Report.pdf"

    return send_file(
        pdf_buf,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )
