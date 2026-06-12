"""
soslog.org -- Combined Webhook Server
Handles:
  1. Twilio inbound SMS -> saves to Firestore
     - If message starts with ANALYZE: calls Claude API for structured analysis
     - Sends analysis back to user for confirmation
     - User replies CONFIRM to save or EDIT to discard
  2. Stripe webhook -> upgrades user plan on payment
  3. Claude analysis endpoint -> called from dashboard web upload

Install: pip install flask twilio firebase-admin requests gunicorn stripe anthropic

Environment variables:
    TWILIO_AUTH_TOKEN
    TWILIO_ACCOUNT_SID
    GOOGLE_GEOCODING_API_KEY
    FIREBASE_CREDENTIALS_JSON
    STRIPE_SECRET_KEY
    STRIPE_WEBHOOK_SECRET
    ANTHROPIC_API_KEY
"""

from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from twilio.request_validator import RequestValidator
from twilio.rest import Client as TwilioClient
from datetime import datetime, timezone
import os, re, json, uuid
import requests as http
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter
import stripe
import anthropic

app = Flask(__name__)

# Handle CORS manually — more reliable than flask-cors for Railway
@app.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin', '')
    allowed = ['https://soslogs.org', 'https://www.soslogs.org', 'https://soslogs-git-dev-sinkorserves-projects.vercel.app']
    if origin in allowed or '.vercel.app' in origin or origin.endswith('soslogs.org'):
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Max-Age'] = '86400'
        if request.method == 'OPTIONS':
            response.status_code = 200
    return response

@app.route('/analyze', methods=['OPTIONS'])
def analyze_options():
    return '', 204

@app.route('/analyze/confirm', methods=['OPTIONS'])
def analyze_confirm_options():
    return '', 204




# -- Config --
TWILIO_AUTH_TOKEN     = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_ACCOUNT_SID    = os.environ.get("TWILIO_ACCOUNT_SID", "")
GEOCODING_KEY         = os.environ.get("GOOGLE_GEOCODING_API_KEY", "")
VALIDATE_TWILIO       = os.environ.get("VALIDATE_TWILIO", "true").lower() == "true"
STRIPE_SECRET_KEY     = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
ANTHROPIC_API_KEY     = os.environ.get("ANTHROPIC_API_KEY", "")
TWILIO_NUMBER         = "+18887995647"
VERIFY_SERVICE_SID    = os.environ.get("TWILIO_VERIFY_SERVICE_SID", "")

stripe.api_key    = STRIPE_SECRET_KEY
claude_client     = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
twilio_client     = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# -- Firebase init --
if not firebase_admin._apps:
    creds_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")
    if creds_json:
        cred = credentials.Certificate(json.loads(creds_json))
    else:
        cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ══════════════════════════════════════════════════════════════
# CLAUDE ANALYSIS ENGINE
# ══════════════════════════════════════════════════════════════

ANALYSIS_SYSTEM_PROMPT = """You are a neutral documentation analyst for SOSLogs, a personal safety documentation platform.

When given a document, email, or text description from a user, analyze it and return ONLY a JSON object with this exact structure:

{
  "date": "YYYY-MM-DD",
  "thread": "Subject line or document title",
  "your_action": "What the user did — factual, neutral, specific",
  "her_request_or_response": "What the other party did or requested — factual only",
  "response_status": "Pending | Confirmed | Partial | No Response",
  "judges_observation": "How a neutral judge would read this — cooperative or adversarial tone, what it establishes legally",
  "court_relevance": "High | Medium | Low — with one sentence explanation",
  "devils_advocate": "What opposing counsel would argue — specific vulnerabilities in this document",
  "soslogs_relevance": "How this document relates to the SOSLogs platform use case",
  "category": "co_parenting | legal | workplace | personal_safety | financial | medical",
  "key_facts": ["fact 1", "fact 2", "fact 3"]
}

Rules:
- Be neutral and factual. Never take sides.
- Devils advocate must identify specific vulnerabilities, not generic ones.
- Judges observation must identify what this document legally establishes.
- Key facts must be specific, verifiable statements from the document.
- Return ONLY the JSON object. No preamble, no explanation, no markdown.
"""

def analyze_with_claude(text):
    """Call Claude API to analyze document text and return structured JSON."""
    try:
        message = claude_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            system=ANALYSIS_SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": f"Analyze this document:\n\n{text}"}
            ]
        )
        raw = message.content[0].text.strip()
        # Strip markdown if present
        if raw.startswith("```"):
            raw = re.sub(r"```json|```", "", raw).strip()
        return json.loads(raw)
    except Exception as e:
        app.logger.error(f"Claude analysis failed: {e}")
        return None

def format_analysis_for_sms(analysis):
    """Format Claude analysis as a readable SMS confirmation."""
    if not analysis:
        return "Analysis failed. Please try again."

    msg = f"""SOSLogs Analysis — Review & Confirm

Date: {analysis.get('date', 'Unknown')}
Thread: {analysis.get('thread', 'Unknown')}

YOUR ACTION:
{analysis.get('your_action', '')}

RESPONSE STATUS: {analysis.get('response_status', '')}

JUDGE'S OBSERVATION:
{analysis.get('judges_observation', '')}

COURT RELEVANCE: {analysis.get('court_relevance', '')}

DEVIL'S ADVOCATE:
{analysis.get('devils_advocate', '')}

Reply CONFIRM to save this analysis to your SOSLogs record.
Reply EDIT to discard and send a revised version."""

    # Truncate if too long for SMS
    if len(msg) > 1500:
        msg = msg[:1450] + "...\n\nReply CONFIRM to save or EDIT to discard."
    return msg

# -- Pending analyses in memory (phone -> analysis dict) --
# In production this should be stored in Firestore with TTL
pending_analyses = {}

# ══════════════════════════════════════════════════════════════
# STRIPE WEBHOOK
# ══════════════════════════════════════════════════════════════

def find_phone_by_email(email):
    try:
        email_docs = db.collection_group('emails').where(
            filter=FieldFilter('email', '==', email)
        ).get()
        for doc in email_docs:
            phone = doc.reference.parent.parent.id
            if phone and phone.startswith('+'):
                return phone
    except Exception as e:
        app.logger.warning(f"find_phone_by_email error: {e}")
    return None

def upgrade_user_plan(email, plan, subscription_id=None):
    phone = find_phone_by_email(email)
    if not phone:
        app.logger.warning(f"upgrade_user_plan: no phone found for {email}")
        return False
    try:
        profile_ref = db.collection('users').document(phone).collection('profile').document('data')
        update_data = {
            'plan':          plan,
            'planUpdatedAt': firestore.SERVER_TIMESTAMP,
            'stripeEmail':   email,
        }
        if subscription_id:
            update_data['stripeSubscriptionId'] = subscription_id
        profile_ref.set(update_data, merge=True)
        app.logger.info(f"Plan updated: {phone} ({email}) -> {plan}")
        return True
    except Exception as e:
        app.logger.error(f"upgrade_user_plan error: {e}")
        return False

@app.route("/stripe/webhook", methods=["POST"])
def stripe_webhook():
    payload    = request.get_data()
    sig_header = request.headers.get("Stripe-Signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError as e:
        return jsonify({"error": "Invalid signature"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    event_type = event["type"]
    app.logger.info(f"Stripe event: {event_type}")

    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        email   = session.get("customer_details", {}).get("email") or session.get("customer_email")
        sub_id  = session.get("subscription")
        if email:
            upgrade_user_plan(email, "base", sub_id)

    elif event_type == "invoice.payment_succeeded":
        invoice = event["data"]["object"]
        email   = invoice.get("customer_email")
        sub_id  = invoice.get("subscription")
        if email and invoice.get("billing_reason") != "subscription_create":
            upgrade_user_plan(email, "base", sub_id)

    elif event_type in ("customer.subscription.deleted", "invoice.payment_failed"):
        obj   = event["data"]["object"]
        email = obj.get("customer_email")
        if not email:
            try:
                customer = stripe.Customer.retrieve(obj.get("customer"))
                email = customer.get("email")
            except Exception:
                pass
        if email:
            upgrade_user_plan(email, "free")

    return jsonify({"status": "ok"}), 200

# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════

def enc(email):
    return email.replace('.', '_dot_').replace('@', '_at_')

def find_email_key(phone):
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

def save_analysis_record(phone, analysis, original_text, email=''):
    """Save confirmed analysis to Firestore flat records path only.
    Always writes to users/{phone}/records — never to nested email path
    to avoid saving under the wrong email subcollection.
    """
    msg_id = f"analysis_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    email_for_record = email  # Use email passed from frontend

    body = f"""ANALYZED DOCUMENT

Original Text:
{original_text}

--- SOSLogs Analysis ---
Date: {analysis.get('date', '')}
Thread: {analysis.get('thread', '')}

Your Action: {analysis.get('your_action', '')}
Her Request/Response: {analysis.get('her_request_or_response', '')}
Response Status: {analysis.get('response_status', '')}

Judge's Observation: {analysis.get('judges_observation', '')}
Court Relevance: {analysis.get('court_relevance', '')}
Devil's Advocate: {analysis.get('devils_advocate', '')}

Key Facts: {', '.join(analysis.get('key_facts', []))}"""

    app.logger.info(f"Analysis record email: {email_for_record}")

    record = {
        'body':           body,
        'messageSid':     msg_id,
        'from':           phone,
        'email':          email_for_record,
        'timestamp':      firestore.SERVER_TIMESTAMP,
        'timestampLocal': datetime.now(timezone.utc).isoformat(),
        'source':         'claude_analysis',
        'category':       analysis.get('category', 'legal'),
        'analysisData':   analysis,
        'originalText':   original_text,
        'location': {
            'city': '', 'state': '', 'country': 'US',
            'lat': None, 'lng': None,
            'formatted': '', 'precision': 'unknown',
            'extractedAddress': None,
        },
        'hasMedia':  False,
        'mediaUrls': [],
    }

    # Write ONLY to flat path — avoids email subcollection ambiguity
    db.collection('users').document(phone).collection('records').document(msg_id).set(record)
    app.logger.info(f"Analysis saved: users/{phone}/records/{msg_id}")
    return msg_id

ADDRESS_PATTERNS = [
    r'(?:at|located at|incident at|location[:\s]+|address[:\s]+)\s*'
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
        r = http.get('https://maps.googleapis.com/maps/api/geocode/json',
                     params={'address': query, 'key': GEOCODING_KEY}, timeout=5)
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

# ══════════════════════════════════════════════════════════════
# TWILIO SMS WEBHOOK
# ══════════════════════════════════════════════════════════════

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

    app.logger.info(f"Inbound SMS — From: '{phone}' Body: '{body[:50]}' SID: {sid}")

    resp = MessagingResponse()

    # Guard: reject if phone is empty
    if not phone:
        app.logger.error(f"Inbound SMS has empty From field — raw form: {dict(request.form)}")
        resp.message("Unable to process — sender phone number not detected.")
        return str(resp), 200, {"Content-Type": "text/xml"}

    # ── CONFIRM command: save pending analysis ──────────────────
    if body.upper().strip() == "CONFIRM":
        if phone in pending_analyses:
            analysis_data = pending_analyses.pop(phone)
            save_analysis_record(phone, analysis_data['analysis'], analysis_data['original_text'])
            resp.message("Analysis saved to your SOSLogs record. View it at soslogs.org")
        else:
            resp.message("No pending analysis to confirm. Send ANALYZE followed by your document text.")
        return str(resp), 200, {"Content-Type": "text/xml"}

    # ── EDIT command: discard pending analysis ──────────────────
    if body.upper().strip() == "EDIT":
        if phone in pending_analyses:
            pending_analyses.pop(phone)
        resp.message("Analysis discarded. Send your revised document text starting with ANALYZE:")
        return str(resp), 200, {"Content-Type": "text/xml"}

    # ── ANALYZE command: trigger Claude analysis ────────────────
    if body.upper().startswith("ANALYZE:") or body.upper().startswith("ANALYZE "):
        text_to_analyze = body[8:].strip() if body.upper().startswith("ANALYZE:") else body[8:].strip()
        if not text_to_analyze:
            resp.message("Please include the document text after ANALYZE:\n\nExample: ANALYZE: [paste your document text here]")
            return str(resp), 200, {"Content-Type": "text/xml"}

        resp.message("Analyzing your document... This may take 15-30 seconds. You will receive the analysis shortly.")

        # Analyze asynchronously — send result via separate Twilio message
        try:
            analysis = analyze_with_claude(text_to_analyze)
            if analysis:
                pending_analyses[phone] = {
                    'analysis':     analysis,
                    'original_text': text_to_analyze,
                    'timestamp':    datetime.now(timezone.utc).isoformat()
                }
                confirmation_msg = format_analysis_for_sms(analysis)
                twilio_client.messages.create(
                    body=confirmation_msg,
                    from_=TWILIO_NUMBER,
                    to=phone
                )
            else:
                twilio_client.messages.create(
                    body="Analysis could not be completed. Please try again or use the web dashboard.",
                    from_=TWILIO_NUMBER,
                    to=phone
                )
        except Exception as e:
            app.logger.error(f"Analysis error: {e}")

        return str(resp), 200, {"Content-Type": "text/xml"}

    # ── Standard SMS log: save directly ────────────────────────
    extracted_address = extract_address(body)
    if extracted_address:
        # User included an address — geocode it precisely
        geo = geocode(extracted_address)
        loc_city    = geo["formatted"].split(",")[0] if geo else city
        loc_state   = state
        loc_formatted = geo["formatted"] if geo else extracted_address
        loc_precision = "address"
    else:
        # No address in message — don't use Twilio's often-wrong city metadata
        geo = None
        loc_city    = ""
        loc_state   = ""
        loc_formatted = ""
        loc_precision = "unknown"

    record = {
        "body":           body,
        "messageSid":     sid,
        "from":           phone,
        "timestamp":      firestore.SERVER_TIMESTAMP,
        "timestampLocal": datetime.now(timezone.utc).isoformat(),
        "source":         "sms",
        "location": {
            "city":             loc_city,
            "state":            loc_state,
            "country":          country,
            "zip":              zipcode if extracted_address else "",
            "lat":              geo["lat"] if geo else None,
            "lng":              geo["lng"] if geo else None,
            "formatted":        loc_formatted,
            "precision":        loc_precision,
            "extractedAddress": extracted_address,
        },
        "hasMedia":  n_media > 0,
        "mediaUrls": [request.form.get(f"MediaUrl{i}") for i in range(n_media)],
    }

    try:
        email_key = find_email_key(phone)
        db.collection('users').document(phone).collection('emails').document(email_key).collection('records').document(sid).set(record)
        db.collection('users').document(phone).collection('records').document(sid).set(record)
        app.logger.info(f"Saved: users/{phone}/records/{sid}")
    except Exception as e:
        app.logger.error(f"Firestore write failed: {e}")

    location_hint = " Include your address for accurate location tracking." if not extracted_address else ""
    resp.message(f"SOSLog received. Your record is saved.{location_hint} Reply STOP to opt out.")
    return str(resp), 200, {"Content-Type": "text/xml"}

# ══════════════════════════════════════════════════════════════
# WEB DASHBOARD ANALYSIS ENDPOINT
# ══════════════════════════════════════════════════════════════

@app.route("/analyze", methods=["POST"])
def analyze_document():
    """Called from dashboard when user uploads a document for analysis."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    text  = data.get("text", "").strip()
    phone = data.get("phone", "").strip()

    if not text:
        return jsonify({"error": "No text to analyze"}), 400
    if not phone:
        return jsonify({"error": "No phone provided"}), 400

    # Handle FILE_BASE64 uploads — extract text via Claude vision
    extracted_text = text
    if text.startswith("FILE_BASE64:"):
        try:
            parts = text.split(":", 2)
            media_type = parts[1]  # e.g. application/pdf or image/jpeg
            base64_data = parts[2]

            app.logger.info(f"Processing file upload: {media_type}")

            # Send to Claude as a document/image for text extraction
            if media_type == "application/pdf":
                extract_msg = claude_client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4000,
                    messages=[{
                        "role": "user",
                        "content": [
                            {
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": "application/pdf",
                                    "data": base64_data
                                }
                            },
                            {
                                "type": "text",
                                "text": "Please extract and return all the text content from this document exactly as it appears."
                            }
                        ]
                    }]
                )
            else:
                # Image file
                extract_msg = claude_client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4000,
                    messages=[{
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": base64_data
                                }
                            },
                            {
                                "type": "text",
                                "text": "Please extract and return all the text content from this image exactly as it appears."
                            }
                        ]
                    }]
                )
            extracted_text = extract_msg.content[0].text
            app.logger.info(f"Extracted {len(extracted_text)} chars from file")
        except Exception as e:
            app.logger.error(f"File extraction error: {e}")
            return jsonify({"error": f"Could not extract text from file: {str(e)}"}), 500

    analysis = analyze_with_claude(extracted_text)
    if not analysis:
        return jsonify({"error": "Analysis failed"}), 500

    return jsonify({
        "status":   "ok",
        "analysis": analysis,
        "text":     extracted_text,  # Return extracted text not base64
        "phone":    phone
    }), 200

@app.route("/analyze/confirm", methods=["POST"])
def confirm_analysis():
    """Called from dashboard when user confirms the analysis and wants to save."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    phone         = data.get("phone", "").strip()
    analysis      = data.get("analysis", {})
    original_text = data.get("text", "").strip()
    user_email    = data.get("email", "").strip()

    if not phone or not analysis:
        return jsonify({"error": "Missing phone or analysis"}), 400

    try:
        msg_id = save_analysis_record(phone, analysis, original_text, user_email)
        return jsonify({"status": "ok", "recordId": msg_id}), 200
    except Exception as e:
        app.logger.error(f"confirm_analysis error: {e}")
        return jsonify({"error": str(e)}), 500

# ══════════════════════════════════════════════════════════════
# TWILIO VERIFY OTP ENDPOINTS
# ══════════════════════════════════════════════════════════════

@app.route("/verify/send", methods=["POST", "OPTIONS"])
def verify_send():
    """Send OTP to phone number via Twilio Verify."""
    if request.method == "OPTIONS":
        return '', 204
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    phone = data.get("phone", "").strip()
    if not phone:
        return jsonify({"error": "Phone number required"}), 400

    # Only allow US numbers
    if not phone.startswith("+1") or len(phone.replace("+1","").replace(" ","").replace("-","")) != 10:
        return jsonify({"error": "Only US phone numbers (+1) are supported"}), 400

    if not VERIFY_SERVICE_SID:
        return jsonify({"error": "Verify service not configured"}), 500

    try:
        verification = twilio_client.verify.v2.services(VERIFY_SERVICE_SID)             .verifications.create(to=phone, channel="sms")
        app.logger.info(f"OTP sent to {phone} - status: {verification.status}")
        return jsonify({"status": "ok", "message": "Verification code sent"}), 200
    except Exception as e:
        app.logger.error(f"Twilio Verify send error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/verify/check", methods=["POST", "OPTIONS"])
def verify_check():
    """Check OTP code entered by user."""
    if request.method == "OPTIONS":
        return '', 204
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    phone = data.get("phone", "").strip()
    code  = data.get("code", "").strip()

    if not phone or not code:
        return jsonify({"error": "Phone and code required"}), 400

    if not VERIFY_SERVICE_SID:
        return jsonify({"error": "Verify service not configured"}), 500

    try:
        check = twilio_client.verify.v2.services(VERIFY_SERVICE_SID)             .verification_checks.create(to=phone, code=code)
        app.logger.info(f"OTP check for {phone} - status: {check.status}")
        if check.status == "approved":
            return jsonify({"status": "approved"}), 200
        else:
            return jsonify({"status": "rejected", "error": "Invalid or expired code"}), 400
    except Exception as e:
        app.logger.error(f"Twilio Verify check error: {e}")
        return jsonify({"error": str(e)}), 500


# ══════════════════════════════════════════════════════════════
# CLAUDE INSIGHTS ENDPOINT
# ══════════════════════════════════════════════════════════════

@app.route("/insights", methods=["POST", "OPTIONS"])
def insights():
    """Chat with Claude about user's own log data."""
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        return response
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    phone       = data.get("phone", "").strip()
    records_ctx = data.get("records", "")
    messages    = data.get("messages", [])

    if not phone or not messages:
        return jsonify({"error": "Missing phone or messages"}), 400

    system_prompt = f"""You are a helpful documentation analyst assistant for SOSLogs, a personal safety documentation platform.
You have access to the user's incident logs and help them understand patterns, generate insights, and assess their documentation strength.

The user's log data summary:
{records_ctx}

Guidelines:
- Be concise, factual, and supportive
- Reference specific dates, people, or locations from the logs when relevant
- Assess documentation strength using: Specificity, Consistency, Corroboration, Timeline, Patterns, Objectivity
- Never make legal conclusions — suggest consulting an attorney for legal advice
- Format responses clearly with line breaks for readability"""

    try:
        message = claude_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=system_prompt,
            messages=messages
        )
        reply = message.content[0].text
        app.logger.info(f"Insights response for {phone}: {len(reply)} chars")
        return jsonify({"reply": reply}), 200
    except Exception as e:
        app.logger.error(f"Insights error: {e}")
        return jsonify({"error": str(e)}), 500



# ══════════════════════════════════════════════════════════════
# ACCOUNT — UPDATE PHONE NUMBER
# ══════════════════════════════════════════════════════════════

@app.route("/account/update-phone", methods=["POST", "OPTIONS"])
def update_phone():
    """Migrate all user data from old phone to new phone number."""
    if request.method == "OPTIONS":
        return '', 204
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data"}), 400

    old_phone = data.get("old_phone", "").strip()
    new_phone = data.get("new_phone", "").strip()
    email     = data.get("email", "").strip()

    if not old_phone or not new_phone:
        return jsonify({"error": "Missing phone numbers"}), 400
    if old_phone == new_phone:
        return jsonify({"error": "New number is same as current"}), 400

    app.logger.info(f"Phone migration: {old_phone} → {new_phone}")

    try:
        # 1. Copy profile
        old_profile_ref = db.collection('users').document(old_phone).collection('profile').document('data')
        old_profile = old_profile_ref.get()
        if old_profile.exists:
            profile_data = old_profile.to_dict()
            profile_data['phone'] = new_phone
            db.collection('users').document(new_phone).collection('profile').document('data').set(profile_data)

        # 2. Copy emails subcollection
        old_emails = db.collection('users').document(old_phone).collection('emails').stream()
        for email_doc in old_emails:
            db.collection('users').document(new_phone).collection('emails').document(email_doc.id).set(email_doc.to_dict())

        # 3. Copy all records
        old_records = db.collection('users').document(old_phone).collection('records').stream()
        migrated = 0
        for record in old_records:
            record_data = record.to_dict()
            record_data['from'] = new_phone
            db.collection('users').document(new_phone).collection('records').document(record.id).set(record_data)
            migrated += 1

        # 4. Delete old data
        # Delete old records
        old_records2 = db.collection('users').document(old_phone).collection('records').stream()
        for record in old_records2:
            record.reference.delete()

        # Delete old emails
        old_emails2 = db.collection('users').document(old_phone).collection('emails').stream()
        for email_doc in old_emails2:
            email_doc.reference.delete()

        # Delete old profile
        old_profile_ref.delete()

        # Delete old user document
        db.collection('users').document(old_phone).delete()

        app.logger.info(f"Migration complete: {migrated} records moved")
        return jsonify({"status": "ok", "migrated": migrated}), 200

    except Exception as e:
        app.logger.error(f"Migration error: {e}")
        return jsonify({"error": str(e)}), 500

# ══════════════════════════════════════════════════════════════
# HEALTH CHECK
# ══════════════════════════════════════════════════════════════

@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "soslog-webhook"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
