"""
soslog.org -- Twilio Inbound SMS Webhook
Receives inbound SMS, geocodes city/state to lat/lng,
writes to Firestore under phone-first hierarchy.

Install: pip install flask twilio firebase-admin requests gunicorn

Environment variables:
    TWILIO_AUTH_TOKEN           -- Twilio console
    GOOGLE_GEOCODING_API_KEY    -- Google Cloud
    FIREBASE_CREDENTIALS_JSON   -- Full Firebase service account JSON as string
"""

from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from twilio.request_validator import RequestValidator
from datetime import datetime, timezone
import os, re, json
import requests as http
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# -- Config --
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
GEOCODING_KEY     = os.environ.get("GOOGLE_GEOCODING_API_KEY", "")
VALIDATE_TWILIO   = os.environ.get("VALIDATE_TWILIO", "true").lower() == "true"
AUTO_REPLY        = "SOSLog received your message. Your record is saved. Reply STOP to opt out."

# -- Firebase init --
# Reads credentials exclusively from FIREBASE_CREDENTIALS_JSON env var.
# Raises a clear error at startup if the variable is missing or empty so the
# app never attempts to load a local file that won't exist in production.
import logging as _logging
if not firebase_admin._apps:
    creds_json = os.environ.get("FIREBASE_CREDENTIALS_JSON", "").strip()
    if not creds_json:
        raise EnvironmentError(
            "FIREBASE_CREDENTIALS_JSON environment variable is not set or is empty. "
            "Set it to the full Firebase service account JSON string."
        )
    _logging.getLogger(__name__).info(
        "Firebase: loading credentials from FIREBASE_CREDENTIALS_JSON env var"
    )
    cred = credentials.Certificate(json.loads(creds_json))
    firebase_admin.initialize_app(cred)

db = firestore.client()

# -- Helpers --
def enc(email):
    return email.replace('.', '_dot_').replace('@', '_at_')

def records_ref(phone, email_key):
    return (db.collection('users').document(phone)
              .collection('emails').document(email_key)
              .collection('records'))

def find_email_key(phone):
    """Return encoded email key linked to this phone, or 'unlinked'."""
    try:
        docs = list(db.collection('users').document(phone)
                      .collection('emails').stream())
        for d in docs:
            if d.id != 'unlinked':
                return d.id
    except Exception as e:
        app.logger.warning(f"find_email_key: {e}")
    return 'unlinked'

def valid_twilio(req):
    if not VALIDATE_TWILIO:
        return True
    v = RequestValidator(TWILIO_AUTH_TOKEN)
    return v.validate(req.url, req.form.to_dict(),
                      req.headers.get("X-Twilio-Signature", ""))

# -- Address patterns --
ADDRESS_PATTERNS = [
    r'(?:at|located at|incident at|location[:\s]+|address[:\s]+)\s*'
    r'(\d+\s+[A-Za-z0-9\s\.,#-]+'
    r'(?:St|Street|Ave|Avenue|Blvd|Boulevard|Rd|Road|Dr|Drive|Ln|Lane|Way|Ct|Court|Pl|Place|Hwy|Highway|Pkwy|Parkway)'
    r'[A-Za-z0-9\s\.,#-]*(?:[A-Z]{2}\s+\d{5})?)',

    r'(\d+\s+[A-Za-z0-9\s\.,#-]+'
    r'(?:St|Street|Ave|Avenue|Blvd|Boulevard|Rd|Road|Dr|Drive|Ln|Lane|Way|Ct|Court|Pl|Place|Hwy|Highway|Pkwy|Parkway)'
    r'[A-Za-z0-9\s\.,#-]*(?:[A-Z]{2}\s+\d{5})?)',
]

def extract_address(text):
    for pattern in ADDRESS_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            addr = match.group(1).strip().rstrip('.,')
            if len(addr) > 8:
                return addr
    return None

def geocode(address, state='', country=''):
    if not address:
        return None
    query = ', '.join(p for p in [address, state, country] if p) if (state or country) else address
    try:
        r = http.get(
            'https://maps.googleapis.com/maps/api/geocode/json',
            params={'address': query, 'key': GEOCODING_KEY},
            timeout=5
        )
        data = r.json()
        if data.get('status') == 'OK' and data.get('results'):
            loc = data['results'][0]['geometry']['location']
            return {
                'lat':       loc['lat'],
                'lng':       loc['lng'],
                'formatted': data['results'][0].get('formatted_address', query),
                'precision': 'address' if (not state and not country) else 'city'
            }
    except Exception as e:
        app.logger.warning(f"Geocoding failed '{query}': {e}")
    return None

# -- Inbound SMS --
@app.route("/sms/inbound", methods=["POST"])
def inbound_sms():
    if not valid_twilio(request):
        return jsonify({"error": "Forbidden"}), 403

    phone   = request.form.get("From", "").strip()
    body    = request.form.get("Body", "").strip()
    sid     = request.form.get("MessageSid")
    city    = request.form.get("FromCity", "")
    state   = request.form.get("FromState", "")
    country = request.form.get("FromCountry", "")
    zipcode = request.form.get("FromZip", "")
    n_media = int(request.form.get("NumMedia", 0))

    # Try street address from message first, fall back to city level
    extracted_address = extract_address(body)
    if extracted_address:
        geo = geocode(extracted_address)
    else:
        geo = geocode(city, state, country)

    record = {
        "body":           body,
        "messageSid":     sid,
        "from":           phone,
        "timestamp":      firestore.SERVER_TIMESTAMP,
        "timestampLocal": datetime.now(timezone.utc).isoformat(),
        "source":         "sms",
        "location": {
            "city":             city,
            "state":            state,
            "country":          country,
            "zip":              zipcode,
            "lat":              geo["lat"]       if geo else None,
            "lng":              geo["lng"]       if geo else None,
            "formatted":        geo["formatted"] if geo else f"{city}, {state}".strip(", "),
            "precision":        geo.get("precision", "city") if geo else "unknown",
            "extractedAddress": extracted_address,
        },
        "hasMedia":  n_media > 0,
        "mediaUrls": [request.form.get(f"MediaUrl{i}") for i in range(n_media)],
    }

    try:
        email_key = find_email_key(phone)
        records_ref(phone, email_key).document(sid).set(record)
        app.logger.info(f"Saved: users/{phone}/emails/{email_key}/records/{sid}")
    except Exception as e:
        app.logger.error(f"Firestore write failed: {e}")

    resp = MessagingResponse()
    resp.message(AUTO_REPLY)
    return str(resp), 200, {"Content-Type": "text/xml"}

# -- Health check --
@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "soslog-sms-webhook"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
