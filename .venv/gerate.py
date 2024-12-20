import os
import pandas as pd
import pyqrcode

# Configuration
EXCEL_FILE = 'visitors.xlsx'  # Path to your Excel file
QR_CODES_DIR = 'static/qr_codes'  # Directory to save QR codes

# Create the directory if it doesn't exist
os.makedirs(QR_CODES_DIR, exist_ok=True)

# Read the Excel file
df = pd.read_excel(EXCEL_FILE)

# Generate QR codes for each visitor
for index, row in df.iterrows():
    visitor_data = f"{row['name']},{row['phone_number']},{row['state']}"
    qr = pyqrcode.create(visitor_data)
    qr_file = os.path.join(QR_CODES_DIR, f"{row['name']}_qr.png")
    qr.png(qr_file, scale=8)

# Save updated DataFrame with scanned status
df['scanned'] = False
df.to_excel('updated_visitors.xlsx', index=False)
