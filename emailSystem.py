from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
import smtplib
import os
from dotenv import load_dotenv

load_dotenv()


def send_email(recipient_email: str, details: str = ""):
    sender_email = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASSWORD")

    if not sender_email or not password:
        print("Please set the EMAIL_USER and EMAIL_PASSWORD environment variables.")
        return

    smtp = smtplib.SMTP("smtp.gmail.com", 587)
    smtp.ehlo()
    smtp.starttls()
    smtp.login(sender_email, password)

    msg = MIMEMultipart()
    msg["Subject"] = "❌ Reservation failed"
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg.attach(MIMEText("❌ Error during reservation: \n " + details))

    smtp.sendmail(sender_email, recipient_email, msg.as_string())
    smtp.quit()


if __name__ == "__main__":
    recipient = input("Enter recipient's email address: ")
    send_email(recipient)
