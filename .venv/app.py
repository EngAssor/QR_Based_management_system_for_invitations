from flask import Flask, render_template, jsonify, request
import qrcode
import pandas as pd
import json
from datetime import datetime
import os
from io import BytesIO
import base64
import logging

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Store scanned QR codes in memory
scanned_codes = set()


def generate_qr_codes(excel_path):
    """Generate QR codes from Excel data and save them"""
    try:
        # Read Excel file
        df = pd.read_excel(excel_path)
        logger.info(f"Successfully read Excel file with {len(df)} rows")

        # Create QR codes directory if it doesn't exist
        if not os.path.exists('static/qrcodes'):
            os.makedirs('static/qrcodes')

        # Generate QR code for each visitor
        for index, row in df.iterrows():
            data = {
                'name': str(row['name']).strip(),
                'phone_number': str(row['phone_number']).strip(),
                'state': str(row['state']).strip()
            }

            logger.debug(f"Generating QR code for: {data}")

            # Create QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(json.dumps(data))
            qr.make(fit=True)

            # Create image
            qr_image = qr.make_image(fill_color="black", back_color="white")

            # Save QR code
            filename = f"static/qrcodes/{row['name'].replace(' ', '_')}_{row['phone_number']}.png"
            qr_image.save(filename)
            logger.debug(f"Saved QR code to {filename}")

        logger.info("Successfully generated all QR codes")
        return True

    except Exception as e:
        logger.error(f"Error generating QR codes: {str(e)}")
        return False


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/validate-qr', methods=['POST'])
def validate_qr():
    data = request.json
    qr_data = data.get('qr_data')

    logger.debug(f"Received QR data: {qr_data}")

    try:
        # Parse QR data
        visitor_data = json.loads(qr_data)
        logger.debug(f"Parsed visitor data: {visitor_data}")

        # Check if QR code has been scanned before
        if qr_data in scanned_codes:
            logger.warning("QR code has already been scanned")
            return jsonify({'valid': False, 'message': 'QR code has already been scanned'})

        # Read Excel file to validate data
        df = pd.read_excel('visitors.xlsx')
        logger.debug(f"Excel data head: {df.head()}")

        # Clean and convert data for comparison
        df['name'] = df['name'].astype(str).str.strip()
        df['phone_number'] = df['phone_number'].astype(str).str.strip()
        df['state'] = df['state'].astype(str).str.strip()

        # Debug print the exact values we're looking for
        logger.debug(f"Looking for: name='{visitor_data['name']}', "
                     f"phone='{visitor_data['phone_number']}', "
                     f"state='{visitor_data['state']}'")

        # Check if visitor exists in Excel with detailed logging
        visitor_match = df[
            (df['name'] == visitor_data['name']) &
            (df['phone_number'].astype(str) == visitor_data['phone_number']) &
            (df['state'] == visitor_data['state'])
            ]

        logger.debug(f"Found matches: {len(visitor_match)}")
        if not visitor_match.empty:
            logger.debug(f"Matched row: {visitor_match.iloc[0].to_dict()}")

        if len(visitor_match) > 0:
            # Add to scanned codes
            scanned_codes.add(qr_data)
            logger.info(f"Valid visitor found: {visitor_data['name']}")
            return jsonify({
                'valid': True,
                'message': 'Valid visitor',
                'visitor_data': visitor_data
            })
        else:
            logger.warning(f"No matching visitor found in Excel for {visitor_data}")
            # Return more detailed error message
            return jsonify({
                'valid': False,
                'message': 'Invalid visitor data - No matching record found',
                'debug_info': {
                    'searched_for': visitor_data,
                    'excel_columns': list(df.columns),
                    'total_records': len(df)
                }
            })

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return jsonify({'valid': False, 'message': f'Error decoding QR data: {str(e)}'})
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({'valid': False, 'message': f'Error validating data: {str(e)}'})


@app.route('/debug-info')
def debug_info():
    """Endpoint to show current Excel data for debugging"""
    try:
        df = pd.read_excel('visitors.xlsx')
        return jsonify({
            'total_records': len(df),
            'columns': list(df.columns),
            'first_few_records': df.head().to_dict('records')
        })
    except Exception as e:
        return jsonify({'error': str(e)})


if __name__ == '__main__':
    # Generate QR codes when starting the application
    success = generate_qr_codes('visitors.xlsx')
    if success:
        # Run the Flask app
        app.run(port=5000, debug=True)
    else:
        logger.error("Failed to generate QR codes. Please check the Excel file and try again.")