import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

class Notifier:
    def __init__(self):
        self.email_user = os.getenv("EMAIL_USER")
        self.email_pass = os.getenv("EMAIL_PASSWORD")
        self.tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.tg_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.tg_enabled = os.getenv("TELEGRAM_ENABLED", "False").lower() == "true"

    def send_telegram(self, message: str):
        if not self.tg_enabled or not self.tg_token:
            return
        
        url = f"https://api.telegram.org/bot{self.tg_token}/sendMessage"
        data = {"chat_id": self.tg_chat_id, "text": message}
        try:
            requests.post(url, data=data, timeout=5)
        except Exception as e:
            print(f"⚠️ Telegram send failed: {e}")

    def send_email(self, recipient: str, subject: str, body: str):
        if not self.email_user or not self.email_pass:
            print("⚠️ Email credentials missing.")
            return

        try:
            msg = MIMEMultipart()
            msg["Subject"] = subject
            msg["From"] = self.email_user
            msg["To"] = recipient
            msg.attach(MIMEText(body, "plain"))

            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(self.email_user, self.email_pass)
            server.sendmail(self.email_user, recipient, msg.as_string())
            server.quit()
        except Exception as e:
            print(f"⚠️ Email send failed: {e}")

    def alert(self, success: bool, recipient: str, details: str = ""):
        """Sends notifications based on success/failure."""
        icon = "✅" if success else "❌"
        status = "Success" if success else "Failed"
        message = f"{icon} Gym Reservation {status}\n\n{details}"
        
        # Always send Telegram if enabled
        self.send_telegram(message)

        # Only send email on failure (to avoid spam) or if requested
        if not success:
            self.send_email(recipient, f"{icon} Reservation {status}", details)