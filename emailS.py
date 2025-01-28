import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(sender_email, sender_password, recipient_email, subject, message):
    try:
        # Set up the email details
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))
        
        # Connect to Gmail's SMTP server
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()  # Secure the connection
            server.login(sender_email, sender_password)  # Login to your email
            server.sendmail(sender_email, recipient_email, msg.as_string())  # Send email
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Usage
send_email(
    sender_email="kalattas66@gmail.com",
    sender_password="1234456767asD",
    recipient_email="kalattas6@gmail.com",
    subject="Test Email",
    message="This is a test email sent from Python."
)
