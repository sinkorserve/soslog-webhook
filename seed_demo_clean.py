"""
SOSLogs — Demo Seed Script (Clean Version)
Fictional entries across multiple US cities.
No real addresses, no real people, no real incidents.

Run: python3 seed_demo_clean.py
Requires: pip install firebase-admin
"""

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timezone

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

PHONE     = "+15550001234"
EMAIL     = "emailnaven@gmail.com"
EMAIL_KEY = "emailnaven_at_gmail_com"

def ts(year, month, day, hour=9, minute=0):
    return datetime(year, month, day, hour, minute, 0, tzinfo=timezone.utc)

# Fictional incidents across multiple US cities
# Names, addresses, and situations are entirely made up
INCIDENTS = [

    # ── Workplace HR — Austin TX ──────────────────────────────
    (ts(2026,2,10,9,15),
     "Workplace incident at 823 Congress Ave, Austin TX. Manager John Smith made a dismissive comment about my project proposal in front of four team members during the morning standup. Witnesses present: Sarah Johnson, Mike Davis, Lisa Chen, and Tom Rivera. Comment was unprompted and unrelated to the agenda.",
     "Austin", "TX",
     "workplace_hr",
     30.2672, -97.7431,
     "823 Congress Ave, Austin, TX 78701",
     "address"),

    (ts(2026,2,18,14,30),
     "HR incident at 823 Congress Ave, Austin TX. Received a written warning from John Smith for alleged missed deadlines despite having submitted all deliverables on time with email confirmation. No prior verbal warning was given. All submission timestamps retained as evidence.",
     "Austin", "TX",
     "workplace_hr",
     30.2672, -97.7431,
     "823 Congress Ave, Austin, TX 78701",
     "address"),

    (ts(2026,3,5,11,0),
     "Workplace incident at 823 Congress Ave, Austin TX. John Smith removed me from a client presentation I had prepared for three weeks and assigned it to a junior colleague without explanation. Client later asked why I was not presenting. No internal communication provided to me.",
     "Austin", "TX",
     "workplace_hr",
     30.2672, -97.7431,
     "823 Congress Ave, Austin, TX 78701",
     "address"),

    (ts(2026,3,12,16,45),
     "HR documentation at 823 Congress Ave, Austin TX. Annual performance review rated me below expectations on leadership despite successfully delivering three major projects this quarter. Review criteria were changed from prior year without advance notice. Formal objection submitted in writing.",
     "Austin", "TX",
     "workplace_hr",
     30.2672, -97.7431,
     "823 Congress Ave, Austin, TX 78701",
     "address"),

    (ts(2026,3,20,8,30),
     "Workplace incident at 823 Congress Ave, Austin TX. Colleague Sarah Johnson informed me that John Smith told the team I was being reassigned without informing me directly. This occurred during a team lunch on March 19. I was not invited to the lunch and learned about this secondhand.",
     "Austin", "TX",
     "workplace_hr",
     30.2672, -97.7431,
     "823 Congress Ave, Austin, TX 78701",
     "address"),

    # ── Law enforcement — Houston TX ──────────────────────────
    (ts(2026,1,15,22,30),
     "Incident near 4500 Main St, Houston TX. Unknown individual followed me from the parking garage to my vehicle after leaving the office at 10:30 PM. Individual was male, approximately six feet tall, wearing dark clothing. Drove away when I called out loudly. Partial plate captured: HXL-227.",
     "Houston", "TX",
     "law_enforcement",
     29.7194, -95.3990,
     "4500 Main St, Houston, TX 77002",
     "address"),

    (ts(2026,2,3,19,15),
     "Incident at intersection of Westheimer Rd and Montrose Blvd, Houston TX. Received a threatening voicemail from an unknown number stating I should withdraw my HR complaint or face consequences. Recording preserved and backed up to cloud storage. Reported to Houston Police Department. Report number HPD-2026-0203-8821.",
     "Houston", "TX",
     "law_enforcement",
     29.7388, -95.3909,
     "Westheimer Rd & Montrose Blvd, Houston, TX 77006",
     "address"),

    (ts(2026,2,28,20,0),
     "Incident near 2800 Kirby Dr, Houston TX. Vehicle with partial plate HXL-227 seen parked outside my apartment complex for the second time this week. Filed incident report with Houston Police Department. Report number HPD-2026-0228-3347. Officer Rodriguez responded and documented the vehicle.",
     "Houston", "TX",
     "law_enforcement",
     29.7340, -95.4154,
     "2800 Kirby Dr, Houston, TX 77098",
     "address"),

    (ts(2026,3,8,21,30),
     "Incident near 5600 Bellaire Blvd, Houston TX. Same dark sedan observed in my neighborhood for the third time. Dashcam footage captured full license plate. Footage preserved and provided to Houston Police as follow-up to prior reports. Detective Miller assigned to case.",
     "Houston", "TX",
     "law_enforcement",
     29.7080, -95.4697,
     "5600 Bellaire Blvd, Houston, TX 77401",
     "address"),

    # ── Documentation and resolution — Dallas TX ──────────────
    (ts(2026,1,8,10,0),
     "Documentation filed at 1500 Marilla St, Dallas TX city offices. Submitted formal workplace complaint with the city equal opportunity department. Complaint reference number EOD-2026-0108-114. Was informed a response would be provided within 10 business days.",
     "Dallas", "TX",
     "workplace_hr",
     32.7767, -96.7970,
     "1500 Marilla St, Dallas, TX 75201",
     "address"),

    (ts(2026,1,22,9,0),
     "Consulted with attorney Patricia Williams at 2001 Bryan St, Dallas TX regarding workplace documentation. Attorney confirmed the six-month pattern of documented behavior meets the threshold for a formal hostile work environment claim. Advised to continue detailed timestamped logging.",
     "Dallas", "TX",
     "law_enforcement",
     32.7897, -96.7914,
     "2001 Bryan St, Dallas, TX 75201",
     "address"),

    (ts(2026,4,1,8,0),
     "Medical documentation. Visited Dr. Patel at 3600 Gaston Ave, Dallas TX. Reported stress-related symptoms including difficulty sleeping and persistent headaches over the past four weeks. Doctor confirmed symptoms consistent with workplace stress. Medical records retained.",
     "Dallas", "TX",
     "workplace_hr",
     32.7876, -96.7712,
     "3600 Gaston Ave, Dallas, TX 75246",
     "address"),

    (ts(2026,4,10,15,0),
     "Formal appeal submitted at 823 Congress Ave, Austin TX HR office. Appeal included 52 pages of documented evidence covering email records, timestamped meeting notes, peer evaluations, and incident logs. Received written acknowledgment of receipt from HR Director.",
     "Austin", "TX",
     "workplace_hr",
     30.2672, -97.7431,
     "823 Congress Ave, Austin, TX 78701",
     "address"),

    (ts(2026,4,22,11,30),
     "Positive development at 823 Congress Ave, Austin TX. HR Director Jennifer Lopez met for two hours to review the full documentation package. She expressed serious concern about the pattern of incidents and confirmed an independent investigation would be initiated. Reference number HR-INV-2026-0422.",
     "Austin", "TX",
     "workplace_hr",
     30.2672, -97.7431,
     "823 Congress Ave, Austin, TX 78701",
     "address"),

]

# ── Write to Firestore ─────────────────────────────────────────
def enc(email):
    return email.replace('.','_dot_').replace('@','_at_')

# First delete existing records
print("Clearing existing records for demo account...")
flat_ref   = db.collection('users').document(PHONE).collection('records')
nested_ref = (db.collection('users').document(PHONE)
                .collection('emails').document(EMAIL_KEY)
                .collection('records'))

# Delete flat records
for doc in flat_ref.stream():
    doc.reference.delete()
print("Flat records cleared")

# Delete nested records
for doc in nested_ref.stream():
    doc.reference.delete()
print("Nested records cleared")

# Profile
db.collection('users').document(PHONE).collection('profile').document('data').set({
    'uid':         'demo',
    'phone':       PHONE,
    'country':     'United States',
    'plan':        'base',
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

print(f"\nWriting {len(INCIDENTS)} clean demo records...")
print(f"Cities: Austin TX, Houston TX, Dallas TX")
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
    cat = 'HR' if category == 'workplace_hr' else 'LE'
    print(f"  [{cat}] {timestamp.strftime('%b %d %Y')} {city} — {body[:55]}...")

print()
print(f"Done! {len(INCIDENTS)} clean records written across Austin, Houston and Dallas.")
print("No real addresses, no real people, no real incidents.")
