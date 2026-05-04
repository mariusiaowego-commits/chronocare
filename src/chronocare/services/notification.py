"""Notification service — email and SMS alerts."""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from pathlib import Path

from chronocare.config import settings


class NotificationService:
    """Handle email and SMS notifications."""

    def __init__(self):
        self.smtp_host = getattr(settings, "SMTP_HOST", None)
        self.smtp_port = getattr(settings, "SMTP_PORT", 587)
        self.smtp_user = getattr(settings, "SMTP_USER", None)
        self.smtp_pass = getattr(settings, "SMTP_PASS", None)
        self.notify_email = getattr(settings, "NOTIFY_EMAIL", None)

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str | None = None,
    ) -> dict:
        """Send email notification."""
        if not all([self.smtp_host, self.smtp_user, self.smtp_pass]):
            return {
                "success": False,
                "error": "SMTP not configured. Set SMTP_HOST, SMTP_USER, SMTP_PASS in .env",
            }

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.smtp_user
            msg["To"] = to_email

            if text_content:
                msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_pass)
                server.send_message(msg)

            return {"success": True, "message": f"Email sent to {to_email}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def send_health_alert(
        self,
        person_name: str,
        alerts: list[dict],
        to_email: str | None = None,
    ) -> dict:
        """Send health alert notification."""
        recipient = to_email or self.notify_email
        if not recipient:
            return {"success": False, "error": "No recipient email configured"}

        # Build alert content
        critical_alerts = [a for a in alerts if a["severity"] == "critical"]
        high_alerts = [a for a in alerts if a["severity"] == "high"]

        subject = f"⚠️ ChronoCare 健康预警 - {person_name}"
        if critical_alerts:
            subject = f"🚨 ChronoCare 紧急预警 - {person_name}"

        # HTML content
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">🏥 ChronoCare 健康预警</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0 0;">{person_name}</p>
            </div>
            <div style="background: #f8f9fa; padding: 20px; border: 1px solid #e9ecef;">
                <p style="color: #666;">检测时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        """

        if critical_alerts:
            html += '<h2 style="color: #dc3545;">🚨 紧急预警</h2>'
            for alert in critical_alerts:
                html += f"""
                <div style="background: #f8d7da; border: 1px solid #f5c6cb; padding: 10px; border-radius: 5px; margin: 10px 0;">
                    <strong>{alert['icon']} {alert['title']}</strong><br>
                    <span style="color: #721c24;">{alert['message']}</span>
                </div>
                """

        if high_alerts:
            html += '<h2 style="color: #ffc107;">⚠️ 重要预警</h2>'
            for alert in high_alerts:
                html += f"""
                <div style="background: #fff3cd; border: 1px solid #ffeeba; padding: 10px; border-radius: 5px; margin: 10px 0;">
                    <strong>{alert['icon']} {alert['title']}</strong><br>
                    <span style="color: #856404;">{alert['message']}</span>
                </div>
                """

        html += """
                <p style="color: #666; margin-top: 20px;">
                    <a href="http://localhost:8000/dashboard" style="color: #007bff;">查看仪表盘</a>
                </p>
            </div>
            <div style="background: #343a40; color: #fff; padding: 10px; text-align: center; border-radius: 0 0 10px 10px; font-size: 12px;">
                ChronoCare 老年父母健康管理平台
            </div>
        </body>
        </html>
        """

        # Text content
        text = f"ChronoCare 健康预警 - {person_name}\n\n"
        text += f"检测时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        for alert in alerts:
            text += f"{alert['icon']} {alert['title']}: {alert['message']}\n"

        return await self.send_email(recipient, subject, html, text)

    async def send_weekly_report(
        self,
        person_name: str,
        report: dict,
        to_email: str | None = None,
    ) -> dict:
        """Send weekly report notification."""
        recipient = to_email or self.notify_email
        if not recipient:
            return {"success": False, "error": "No recipient email configured"}

        subject = f"📊 ChronoCare 周报 - {person_name} ({report['period']['start']})"

        bs = report["blood_sugar"]
        bp = report["blood_pressure"]

        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">📊 周报</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0 0;">{person_name} | {report['period']['start']} 至 {report['period']['end']}</p>
            </div>
            <div style="background: #f8f9fa; padding: 20px; border: 1px solid #e9ecef;">
                <h2>🩸 血糖</h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr><td>平均</td><td><strong>{bs['avg'] or '-'} mmol/L</strong></td></tr>
                    <tr><td>范围</td><td>{bs['min'] or '-'} ~ {bs['max'] or '-'}</td></tr>
                    <tr><td>预警</td><td style="color: {'#dc3545' if bs['alert_count'] > 0 else '#28a745'};">{bs['alert_count']} 次</td></tr>
                </table>

                <h2>❤️ 血压</h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr><td>平均</td><td><strong>{bp['avg_systolic'] or '-'}/{bp['avg_diastolic'] or '-'} mmHg</strong></td></tr>
                    <tr><td>心率</td><td>{bp['avg_heart_rate'] or '-'} bpm</td></tr>
                    <tr><td>预警</td><td style="color: {'#dc3545' if bp['alert_count'] > 0 else '#28a745'};">{bp['alert_count']} 次</td></tr>
                </table>

                <p style="margin-top: 20px;">
                    <a href="http://localhost:8000/health-report" style="color: #007bff;">查看完整报告</a>
                </p>
            </div>
        </body>
        </html>
        """

        return await self.send_email(recipient, subject, html)


# Singleton
notification_service = NotificationService()
