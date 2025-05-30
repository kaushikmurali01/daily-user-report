import psycopg2
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import csv
import os
from datetime import datetime
import os

# Environment variables (from GitHub Actions)
DB_NAME = os.environ['DB_NAME']
DB_USER = os.environ['DB_USER']
DB_PASSWORD = os.environ['DB_PASSWORD']
EMAIL_USER = os.environ['EMAIL_USER']
EMAIL_PASSWORD = os.environ['EMAIL_PASSWORD']
EMAIL_TO = os.environ['EMAIL_TO']

# DB connection
conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host='127.0.0.1',
    port='5433'  # Tunnels Azure PostgreSQL port 5432 to localhost:5433
)
cur = conn.cursor()

# Query for users in last 24 hours
cur.execute("""
    SELECT
        u.id,
        u.first_name,
        u.last_name,
        u.email,
        u.phonenumber,
        c.company_name,
        u."createdAt"
    FROM
        epp.users u
    JOIN
        epp.user_company_role ucr ON u.id = ucr.user_id
    JOIN
        epp.company c ON ucr.company_id = c.id
    WHERE
        u."createdAt" >= NOW() - INTERVAL '24 hours'
    ORDER BY
        u."createdAt" DESC
""")
rows = cur.fetchall()
cur.close()
conn.close()

# Write to CSV
filename = "daily_user_report.csv"
with open(filename, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['First Name', 'Last Name', 'Email', 'Phone Number', 'Company', 'Registration Timestamp'])
    for row in rows:
            formatted = list(row)
            formatted[6] = row[6].strftime('%Y-%m-%d %H:%M:%S')  # Format datetime
            writer.writerow(formatted)

# Create email
msg = MIMEMultipart()
msg['From'] = EMAIL_USER
msg['To'] = EMAIL_TO
msg['Subject'] = "Daily Report: New Users Registered to the SEMI Portal"

# Email body
body = """\
Hi,

Please find attached the daily report of users who registered to the SEMI Portal in the past 24 hours.

The attached CSV file includes the following details for each user:
- First Name
- Last Name
- Email Address
- Phone Number
- Associated Company
- Registration Timestamp

This report is auto-generated and sent daily at 8:00 AM (Toronto Time).
If you have any questions or need additional information, feel free to reach out.

Best regards,  
Kaushik
"""
msg.attach(MIMEText(body, "plain"))

# Attach CSV
with open(filename, "rb") as attachment:
    part = MIMEBase("application", "octet-stream")
    part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(filename)}")
    msg.attach(part)

# Send email via Gmail SMTP
with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.starttls()
    server.login(EMAIL_USER, EMAIL_PASSWORD)
    server.send_message(msg)

print("✅ Email with user report sent successfully.")
