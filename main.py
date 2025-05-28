import psycopg2
import smtplib
import os
import csv
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Read environment variables
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
EMAIL_USER = os.environ["EMAIL_USER"]
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"]
EMAIL_TO = os.environ["EMAIL_TO"]

# Connect to database via local port forwarded to Azure
conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host="localhost",
    port=5433
)

cur = conn.cursor()

# Query users created in last 24 hours
cur.execute("""
    SELECT
        u.first_name,
        u.last_name,
        u.email,
        u.phone_number,
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
with open(filename, "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["First Name", "Last Name", "Email", "Phone Number", "Created At", "Company"])
    writer.writerows(rows)

# Email setup
msg = MIMEMultipart()
msg["From"] = EMAIL_USER
msg["To"] = EMAIL_TO
msg["Subject"] = "📋 Daily User Report"

with open(filename, "rb") as f:
    part = MIMEBase("application", "octet-stream")
    part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f"attachment; filename={filename}")
    msg.attach(part)

with smtplib.SMTP("smtp.office365.com", 587) as server:
    server.starttls()
    server.login(EMAIL_USER, EMAIL_PASSWORD)
    server.send_message(msg)

print("✅ Report sent successfully.")
