import os
import psycopg2
import csv
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Connect to PostgreSQL
conn = psycopg2.connect(
    dbname="epp",
    user="customer",
    password=os.getenv("DB_PASSWORD"),
    host="semi-prod-db.postgres.database.azure.com",
    port="5432"
)
cur = conn.cursor()

# Query for last 24 hours
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
cur.close()
conn.close()

# Save as CSV
filename = f"user_report_{datetime.now().strftime('%Y-%m-%d')}.csv"
with open(filename, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['First Name', 'Last Name', 'Email', 'Phone Number', 'Created At', 'Company'])
    writer.writerows(rows)

# Prepare email
msg = MIMEMultipart()
msg['From'] = os.getenv("EMAIL_SENDER")
msg['To'] = os.getenv("EMAIL_RECIPIENT")
msg['Subject'] = "📋 Daily User Report (CSV Attached)"

with open(filename, "rb") as attachment:
    part = MIMEBase("application", "octet-stream")
    part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f"attachment; filename={filename}")
    msg.attach(part)

# Send email using Outlook SMTP
with smtplib.SMTP("smtp.office365.com", 587) as server:
    server.starttls()
    server.login(os.getenv("EMAIL_SENDER"), os.getenv("EMAIL_PASSWORD"))
    server.send_message(msg)

print("✅ Email sent.")
