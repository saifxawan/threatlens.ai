"""Reports routes — CSV and PDF export"""
import csv
import io
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timezone
from app.database import get_db
from app.models.alert import Alert
from app.models.log_entry import LogEntry
from app.models.prediction import Prediction
from app.models.model_metrics import ModelMetrics

router = APIRouter(prefix="/api/reports", tags=["reports"])
from app.routes.auth import get_current_user


@router.get("/summary")
async def report_summary(db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    total_logs = (await db.execute(select(func.count(LogEntry.id)))).scalar() or 0
    total_threats = (await db.execute(
        select(func.count(Prediction.id)).where(Prediction.prediction == "anomaly")
    )).scalar() or 0
    total_alerts = (await db.execute(select(func.count(Alert.id)))).scalar() or 0

    sev_result = await db.execute(
        select(Alert.severity, func.count(Alert.id)).group_by(Alert.severity)
    )
    by_sev = {row[0]: row[1] for row in sev_result}

    top_ips_result = await db.execute(
        select(Alert.source_ip, func.count(Alert.id).label("c"))
        .where(Alert.source_ip.isnot(None))
        .group_by(Alert.source_ip).order_by(desc("c")).limit(5)
    )
    top_ips = [{"ip": r[0], "count": r[1]} for r in top_ips_result]

    top_types_result = await db.execute(
        select(Alert.threat_type, func.count(Alert.id).label("c"))
        .where(Alert.threat_type.isnot(None))
        .group_by(Alert.threat_type).order_by(desc("c")).limit(5)
    )
    top_types = [{"type": r[0], "count": r[1]} for r in top_types_result]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_logs_analyzed": total_logs,
        "total_anomalies_detected": total_threats,
        "total_alerts": total_alerts,
        "severity_distribution": by_sev,
        "top_suspicious_ips": top_ips,
        "top_attack_types": top_types,
        "recommendations": [
            "Enable MFA for all privileged accounts",
            "Block top suspicious IP addresses at firewall",
            "Implement account lockout after 5 failed login attempts",
            "Regularly audit sudo and privileged command logs",
            "Deploy WAF to filter malicious web requests",
        ],
    }


@router.get("/export/csv")
async def export_csv(db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    result = await db.execute(
        select(Alert).order_by(desc(Alert.created_at)).limit(1000)
    )
    alerts = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Title", "Severity", "Status", "Threat Type",
        "Source IP", "Description", "Recommendation", "Created At"
    ])
    for a in alerts:
        writer.writerow([
            a.id, a.title, a.severity, a.status, a.threat_type,
            a.source_ip, a.description, a.recommendation,
            a.created_at.isoformat() if a.created_at else ""
        ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=threatlens_report.csv"},
    )


@router.get("/export/pdf")
async def export_pdf(db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    """Generate a PDF security report using fpdf2."""
    try:
        from fpdf import FPDF

        total_logs = (await db.execute(select(func.count(LogEntry.id)))).scalar() or 0
        total_threats = (await db.execute(
            select(func.count(Prediction.id)).where(Prediction.prediction == "anomaly")
        )).scalar() or 0
        total_alerts = (await db.execute(select(func.count(Alert.id)))).scalar() or 0

        recent_alerts_result = await db.execute(
            select(Alert).order_by(desc(Alert.created_at)).limit(10)
        )
        recent_alerts = recent_alerts_result.scalars().all()

        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Header
        pdf.set_fill_color(10, 25, 47)
        pdf.rect(0, 0, 210, 40, "F")
        pdf.set_text_color(0, 212, 255)
        pdf.set_font("Helvetica", "B", 20)
        pdf.set_y(12)
        pdf.cell(0, 10, "ThreatLens AI — Security Report", align="C", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(180, 180, 180)
        pdf.cell(0, 8, f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", align="C", ln=True)

        pdf.set_y(50)
        pdf.set_text_color(0, 0, 0)

        # Summary section
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_fill_color(0, 212, 255)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 10, "  Executive Summary", fill=True, ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 12)
        pdf.ln(5)

        for label, value in [
            ("Total Logs Analyzed:", f"{total_logs:,}"),
            ("Anomalies Detected:", f"{total_threats:,}"),
            ("Total Alerts:", f"{total_alerts:,}"),
            ("Anomaly Rate:", f"{round(total_threats/max(total_logs,1)*100, 2)}%"),
        ]:
            pdf.cell(80, 8, label, border=0)
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, value, ln=True)
            pdf.set_font("Helvetica", "", 12)

        pdf.ln(5)

        # Recent Alerts Table
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_fill_color(0, 212, 255)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 10, "  Recent Security Alerts", fill=True, ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(3)

        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(230, 230, 230)
        for col, width in [("ID", 15), ("Title", 80), ("Severity", 25), ("IP", 35), ("Status", 30)]:
            pdf.cell(width, 8, col, border=1, fill=True)
        pdf.ln()

        pdf.set_font("Helvetica", "", 8)
        for a in recent_alerts:
            sev_colors = {"critical": (220, 38, 38), "high": (234, 88, 12), "medium": (202, 138, 4), "low": (22, 163, 74)}
            pdf.cell(15, 7, str(a.id), border=1)
            title_short = (a.title or "")[:45] + ("..." if len(a.title or "") > 45 else "")
            pdf.cell(80, 7, title_short, border=1)
            sev = (a.severity or "").upper()
            r, g, b = sev_colors.get(a.severity or "", (100, 100, 100))
            pdf.set_text_color(r, g, b)
            pdf.set_font("Helvetica", "B", 8)
            pdf.cell(25, 7, sev, border=1)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Helvetica", "", 8)
            pdf.cell(35, 7, a.source_ip or "N/A", border=1)
            pdf.cell(30, 7, (a.status or "").upper(), border=1)
            pdf.ln()

        pdf.ln(10)
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_fill_color(0, 212, 255)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 10, "  Security Recommendations", fill=True, ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 11)
        pdf.ln(3)
        recommendations = [
            "Enable Multi-Factor Authentication (MFA) for all privileged accounts",
            "Block the top suspicious IP addresses at the network firewall",
            "Implement account lockout policy after 5 consecutive failed logins",
            "Deploy a Web Application Firewall (WAF) to filter malicious requests",
            "Regularly rotate credentials and audit access logs",
            "Conduct security awareness training for all staff",
        ]
        for i, rec in enumerate(recommendations, 1):
            pdf.cell(10, 8, f"{i}.")
            pdf.cell(0, 8, rec, ln=True)

        # Footer
        pdf.ln(10)
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(0, 8, "Generated by ThreatLens AI — BSIT-VI Cybersecurity Lab Project", align="C", ln=True)

        pdf_bytes = pdf.output()
        return StreamingResponse(
            io.BytesIO(bytes(pdf_bytes)),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=threatlens_report.pdf"},
        )

    except Exception as e:
        return {"error": str(e), "message": "PDF generation failed. Install fpdf2: pip install fpdf2"}
