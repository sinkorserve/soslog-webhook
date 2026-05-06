"""
SOSLogs — Demo Seed Script for Stripe Review
Creates a realistic demo account with HR, LE, and workplace entries
including geocoded locations so map, people, places and spider chart
all show meaningful data.

Run: python3 seed_demo.py
Requires: pip install firebase-admin
"""

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timezone

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# ── Demo account — update after creating on soslogs.org ──────
PHONE     = "+15550001234"   # UPDATE after signup
EMAIL     = "emailnaven@gmail.com"
EMAIL_KEY = "emailnaven_at_gmail_com"

def ts(year, month, day, hour=9, minute=0):
    return datetime(year, month, day, hour, minute, 0, tzinfo=timezone.utc)

# ── Demo incidents ────────────────────────────────────────────
# Mix of workplace HR, law enforcement, and personal safety entries
# with real Dallas-Fort Worth addresses for map pins

INCIDENTS = [

    # ── Workplace HR entries ──────────────────────────────────
    (ts(2026,2,10,9,15),
     "Workplace incident at 500 E Border St, Arlington TX. Manager John Smith made a derogatory comment about my accent in front of three team members during the morning standup. Witnesses present: Sarah Johnson, Mike Davis, and Lisa Chen. Comment was unprompted and unrelated to work discussion.",
     "Arlington", "TX",
     "workplace_hr",
     32.7218, -97.1067,
     "500 E Border St, Arlington, TX 76010",
     "address"),

    (ts(2026,2,18,14,30),
     "HR incident at 500 E Border St, Arlington TX. Received written warning from John Smith for alleged poor communication despite having sent detailed weekly reports every Friday for the past six months. No prior verbal warning was given. Documentation of all weekly reports retained.",
     "Arlington", "TX",
     "workplace_hr",
     32.7218, -97.1067,
     "500 E Border St, Arlington, TX 76010",
     "address"),

    (ts(2026,3,5,11,0),
     "Workplace incident at 500 E Border St, Arlington TX. John Smith excluded me from a project kickoff meeting with the client even though I am the assigned project lead. Discovered the meeting occurred when the client mentioned it during a separate call. No explanation provided.",
     "Arlington", "TX",
     "workplace_hr",
     32.7218, -97.1067,
     "500 E Border St, Arlington, TX 76010",
     "address"),

    (ts(2026,3,12,16,45),
     "HR documentation at 500 E Border St, Arlington TX. Performance review conducted by John Smith rated me below expectations on teamwork despite my team giving me a 4.8 out of 5 peer review score. Review criteria were not shared in advance. Requested copy of evaluation criteria in writing.",
     "Arlington", "TX",
     "workplace_hr",
     32.7218, -97.1067,
     "500 E Border St, Arlington, TX 76010",
     "address"),

    (ts(2026,3,20,8,30),
     "Workplace incident at 500 E Border St, Arlington TX. Overheard John Smith telling Sarah Johnson that I was being managed out. This conversation took place in the hallway near conference room B at approximately 8:30 AM. Sarah Johnson appeared uncomfortable and walked away quickly.",
     "Arlington", "TX",
     "workplace_hr",
     32.7218, -97.1067,
     "500 E Border St, Arlington, TX 76010",
     "address"),

    # ── Law enforcement entries ───────────────────────────────
    (ts(2026,1,15,22,30),
     "Incident near 1100 W Abrams St, Arlington TX. Unknown individual followed me from the parking lot to my car after leaving the building at 10:30 PM. Individual was male, approximately 6 feet tall, wearing dark clothing. Drove away quickly when I called out. Vehicle was a dark blue sedan, partial plate TXZ-44.",
     "Arlington", "TX",
     "law_enforcement",
     32.7084, -97.1280,
     "1100 W Abrams St, Arlington, TX 76013",
     "address"),

    (ts(2026,2,3,19,15),
     "Incident at intersection of Lemmon Ave and N Haskell Ave, Dallas TX. Received threatening text message from unknown number stating I should drop my workplace complaint or face consequences. Screenshot saved. Number traced to prepaid phone. Reported to local police. Report number DPD-2026-0203-4471.",
     "Dallas", "TX",
     "law_enforcement",
     32.8148, -96.7970,
     "Lemmon Ave & N Haskell Ave, Dallas, TX 75204",
     "address"),

    (ts(2026,2,28,20,0),
     "Incident near 300 E Abram St, Arlington TX. Vehicle with partial plate TXZ-44 seen parked outside my building for the third time this month. Different driver visible this time. Photographed the vehicle. Filed incident report with Arlington Police Department. Report number APD-2026-0228-1122.",
     "Arlington", "TX",
     "law_enforcement",
     32.7354, -97.1081,
     "300 E Abram St, Arlington, TX 76010",
     "address"),

    (ts(2026,3,8,21,30),
     "Incident near 2200 E Randol Mill Rd, Arlington TX. Noticed same dark blue sedan in my neighborhood. Took a different route home and vehicle followed for approximately two blocks before turning off. License plate captured on dashcam. Footage preserved and backed up.",
     "Arlington", "TX",
     "law_enforcement",
     32.7583, -97.0806,
     "2200 E Randol Mill Rd, Arlington, TX 76011",
     "address"),

    # ── Personal safety and documentation ────────────────────
    (ts(2026,1,8,10,0),
     "Documentation at 100 W Abram St, Arlington TX City Hall. Filed formal complaint with city HR department regarding workplace conduct. Complaint number CH-2026-0108. Was told a response would be provided within 14 business days. No response received as of February 1 2026.",
     "Arlington", "TX",
     "workplace_hr",
     32.7357, -97.1081,
     "100 W Abram St, Arlington, TX 76010",
     "address"),

    (ts(2026,1,22,9,0),
     "Spoke with attorney Sarah Williams at 1700 Pacific Ave, Dallas TX regarding workplace situation. Attorney confirmed pattern of behavior documented over six months meets threshold for hostile work environment claim. Advised to continue detailed logging with timestamps and witnesses.",
     "Dallas", "TX",
     "law_enforcement",
     32.7831, -96.7998,
     "1700 Pacific Ave, Dallas, TX 75201",
     "address"),

    (ts(2026,4,1,8,0),
     "Physical impact documentation. Racing heart, inability to sleep, and persistent headaches over the past three weeks directly attributed to ongoing workplace stress and harassment. Visited Dr. Patel at 800 W Randol Mill Rd, Arlington TX. Medical records retained. Doctor confirmed stress-related symptoms.",
     "Arlington", "TX",
     "workplace_hr",
     32.7583, -97.1280,
     "800 W Randol Mill Rd, Arlington, TX 76012",
     "address"),

    (ts(2026,4,10,15,0),
     "Follow up at 500 E Border St, Arlington TX. Submitted formal appeal of performance review to HR Director. Appeal included 47 pages of documented evidence including email threads, meeting notes, peer reviews, and timestamped incident logs. Received acknowledgment of receipt.",
     "Arlington", "TX",
     "workplace_hr",
     32.7218, -97.1067,
     "500 E Border St, Arlington, TX 76010",
     "address"),

    (ts(2026,4,22,11,30),
     "Positive development at 500 E Border St, Arlington TX. HR Director Jennifer Lopez met with me for two hours to review documentation. She expressed concern about the pattern of incidents and confirmed an independent investigation would be initiated. Investigation reference number HR-INV-2026-0422.",
     "Arlington", "TX",
     "workplace_hr",
     32.7218, -97.1067,
     "500 E Border St, Arlington, TX 76010",
     "address"),

]

# ── Write to Firestore ─────────────────────────────────────────
def enc(email):
    return email.replace('.','_dot_').replace('@','_at_')

# Profile
db.collection('users').document(PHONE).collection('profile').document('data').set({
    'uid':         'demo',
    'phone':       PHONE,
    'country':     'United States',
    'plan':        'base',      # Pre-set to base for Stripe demo
    'status':      'active',
    'joinedAt':    firestore.SERVER_TIMESTAMP,
    'joinedLocal': datetime.now(timezone.utc).isoformat(),
}, merge=True)

# Email doc
db.collection('users').document(PHONE).collection('emails').document(EMAIL_KEY).set({
    'email':    EMAIL,
    'addedAt':  firestore.SERVER_TIMESTAMP,
    'primary':  True,
}, merge=True)

flat_ref    = db.collection('users').document(PHONE).collection('records')
nested_ref  = (db.collection('users').document(PHONE)
                 .collection('emails').document(EMAIL_KEY)
                 .collection('records'))

print(f"Writing {len(INCIDENTS)} demo records...")
print(f"Phone: {PHONE}")
print(f"Email: {EMAIL}")
print(f"Plan:  base (pre-set for Stripe demo)")
print()

for i, entry in enumerate(INCIDENTS):
    timestamp, body, city, state, category, lat, lng, formatted, precision = entry
    msg_id = f"demo_{timestamp.strftime('%Y%m%d_%H%M')}_{i:02d}"

    record = {
        'body':           body,
        'messageSid':     msg_id,
        'from':           PHONE,
        'email':          EMAIL,
        'timestamp':      timestamp,
        'timestampLocal': timestamp.isoformat(),
        'source':         'web',
        'category':       category,
        'seeded':         True,
        'location': {
            'city':             city,
            'state':            state,
            'country':          'US',
            'zip':              '',
            'lat':              lat,
            'lng':              lng,
            'formatted':        formatted,
            'precision':        precision,
            'extractedAddress': formatted,
        },
        'hasMedia':  False,
        'mediaUrls': [],
    }

    flat_ref.document(msg_id).set(record)
    nested_ref.document(msg_id).set(record)
    cat_label = 'HR' if category == 'workplace_hr' else 'LE'
    print(f"  [{cat_label}] {timestamp.strftime('%b %d %Y')} — {body[:60]}...")

print()
print(f"Done! {len(INCIDENTS)} records written.")
print()
print("Next steps:")
print("1. Create account on soslogs.org with:")
print(f"   Email: {EMAIL}")
print(f"   Phone: {PHONE}")
print("2. Copy the uid from Firebase Auth → update PHONE above if different")
print("3. Firebase Console → users → profile → data → plan should show 'base'")
print("4. Log in and verify dashboard shows all data")
