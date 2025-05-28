import psycopg2
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import csv
import os
from datetime import datetime, timedelta
import os

# ENV Variables
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_TO = os.getenv("EMAIL_TO")

# DB Connection via SSH tunnel (localhost)
conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host="localhost",  # SSH tunnel forwards remote DB to localhost
    port="5433"         # Forwarded port in GitHub Actions
)
cur = conn.cursor()

# Query for last 24 hours
cur.execute("""
    SELECT
        u.first_name,
        u.last_name,
        u.email,
        u.phonenumber,
        u."createdAt",
        c.company_name
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
filename = "daily_user_report.csv"

# Write CSV
with open(filename, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['First Name', 'Last Name', 'Email', 'Phone', 'Created At', 'Company'])
    writer.writerows(rows)

# Compose email
msg = MIMEMultipart()
msg['From'] = EMAIL_USER
msg['To'] = EMAIL_TO
msg['Subject'] = "📋 Daily User Report (CSV Attached)"

# Attach CSV
with open(filename, "rb") as attachment:
    part = MIMEBase("application", "octet-stream")
    part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f"attachment; filename={filename}")
    msg.attach(part)

# Send email via Gmail SMTP
with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.starttls()
    server.login(EMAIL_USER, EMAIL_PASSWORD)  # Gmail App Password
    server.send_message(msg)

print("✅ Report sent successfully.")
