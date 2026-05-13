"""
SOSLogs — Seed Script
Adds Arlington workplace incident logs to Firestore as if they were
texted to 1-888-799-LOGS from +19167900975 (navenk@gmail.com)

Run: python3 seed_logs.py
Requires: pip install firebase-admin
"""

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timezone
import uuid

# ── Firebase init ─────────────────────────────────────────────
cred = credentials.Certificate("serviceAccountKey-dev.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# ── User identity ─────────────────────────────────────────────
PHONE     = "+19167900975"
EMAIL     = "navenk@gmail.com"
EMAIL_KEY = "navenk_at_gmail_com"   # encoded email key in Firestore

def ts(year, month, day, hour=9, minute=0):
    return datetime(year, month, day, hour, minute, 0, tzinfo=timezone.utc)

# ── Incident records ──────────────────────────────────────────
# Each entry: (datetime, message_body, location_city, location_state)
INCIDENTS = [

    # ── October 2025 ──────────────────────────────────────────
    (ts(2025,10,16,14,0),
     "Incident at Arlington Water Utility office: Morgan included Robert and was requested to coordinate as a team on CFE line inspection without informing me first. First documented instance of coordination concern and supervisory bypass.",
     "Arlington", "TX"),

    # ── November 2025 ──────────────────────────────────────────
    (ts(2025,11,24,10,30),
     "Incident at Arlington Water Utility office: Morgan presented Davis Pressure Plane Expansion work in meeting without including updates in weekly email updates prior to the meeting date. I did not see any update on this project in weekly emails before the presentation. No advance notice given to me as supervisor.",
     "Arlington", "TX"),

    (ts(2025,11,30,16,0),
     "Morgan cancelled our regular 1:1 meetings after November 2025. She indicated she was working directly with Robert and did not see a need for our meetings. I was not informed of this decision. Robert confirmed on April 20 2026 he was unaware the meetings had been cancelled.",
     "Arlington", "TX"),

    # ── January 2026 ──────────────────────────────────────────
    (ts(2026,1,29,13,0),
     "Incident at Arlington Water Utility: Morgan attended PB WTP UPP Supply meeting with Brad, Robert, Mike and Dylan without informing me. As her supervisor I was not included or notified of this meeting.",
     "Arlington", "TX"),

    # ── February 2026 ──────────────────────────────────────────
    (ts(2026,2,19,11,0),
     "Incident at Arlington Water Utility: Morgan coordinated with Lori and Gabriel on valve locations but did not inform me of her findings. I discovered this on April 20 2026 after directly asking Morgan. She said she thought I would be updated during the group meeting.",
     "Arlington", "TX"),

    (ts(2026,2,26,9,0),
     "Incident at Arlington Water Utility: Morgan did not know location of CIP scoring files despite being on the team for months. Required repeated direction from me on file paths and task expectations. Pattern of not retaining direction.",
     "Arlington", "TX"),

    (ts(2026,2,27,14,0),
     "Incident at Arlington Water Utility: Morgan independently decided to hold off on adding CIP project scores without consulting me as her supervisor. This is a unilateral decision on a task assigned to her that should have been coordinated.",
     "Arlington", "TX"),

    # ── March 2026 ──────────────────────────────────────────
    (ts(2026,3,10,8,0),
     "Incident at Arlington Water Utility: Robert held 3S scores meeting with Morgan and Mike while I was out sick. No one notified me a meeting was being held on my project. Morgan did not send meeting notes or key points afterward despite this being a supervisory expectation.",
     "Arlington", "TX"),

    (ts(2026,3,10,9,0),
     "Physical impact: Racing heart, inability to sleep, sweating, and headaches severe enough to require two sick days March 10 and 11 2026. Direct result of cumulative workplace stress from sustained pattern of exclusion and undermining by manager Robert.",
     "Arlington", "TX"),

    (ts(2026,3,11,13,25),
     "Action taken: Issued formal written corrective action to Morgan at 1:25 PM establishing three supervisory working norms: 1) Confirm receipt of direction before independently adjusting approach. 2) Attend weekly check-ins via MS Teams. 3) Keep me informed of all meetings and share notes before further coordination.",
     "Arlington", "TX"),

    (ts(2026,3,11,14,18),
     "Morgan accepted corrective action in writing at 2:18 PM stating: I think these adjustments will keep you and I on the same page for projects moving forward. I appreciate the feedback. This constitutes her written agreement to all three supervisory norms.",
     "Arlington", "TX"),

    (ts(2026,3,13,9,0),
     "Incident at Arlington Water Utility: First learned of IDs discussed in March 10 3S scores meeting through Mike on March 13. Morgan never sent meeting summary despite corrective action establishing that expectation signed March 11.",
     "Arlington", "TX"),

    (ts(2026,3,18,15,0),
     "3S Scores meeting held March 18 2026. Participants: Naveen, Robert, Mike, Morgan, Robbie. Computations confirmed correct. Two root causes identified for map display errors. Robbie provided unsolicited positive feedback on my work. After Robbie's comments Robert Mike and Morgan were notably quiet. Morgan confirmed IDs from March 10 meeting were not fully communicated to me. Requested complete ID list via Teams at end of day.",
     "Arlington", "TX"),

    (ts(2026,3,18,16,30),
     "Follow up: Sent Teams message to Morgan requesting complete summary of all IDs discussed in March 10 meeting. This is first official request documented in writing after verbal confirmation in meeting that summary was incomplete.",
     "Arlington", "TX"),

    # ── April 2026 ──────────────────────────────────────────
    (ts(2026,4,16,10,0),
     "Incident at Arlington Water Utility: Morgan updated wrong Public Works SharePoint file independently without coordinating with me. Addressed in recorded Teams meeting same day April 16 2026.",
     "Arlington", "TX"),

    (ts(2026,4,17,11,0),
     "Observed Morgan in Brad's office following our recorded Teams meeting on April 16. Pattern of escalating to Brad after supervisory interactions with me.",
     "Arlington", "TX"),

    (ts(2026,4,18,9,0),
     "Incident: Mike sent point repair email to field ops including only Morgan and Robert. I was excluded from the communication. Asked Mike if there was a reason for my exclusion. He said not really.",
     "Arlington", "TX"),

    (ts(2026,4,18,14,0),
     "Incident: Received Teams message from Morgan about pending Workday spend request for Texas Water conference April 27 2026. No formal approval request submitted to me as supervisor. No discussion about task coverage during her absence. One week notice only.",
     "Arlington", "TX"),

    (ts(2026,4,19,10,0),
     "Background: In January 2026 Robert told me and Mike we would attend Texas Water conference. In February 2026 Robert informed me Brad decided younger engineers would attend instead. Morgan was registered in my place. I was never formally informed by Morgan despite weeks passing. This Texas Water conference registration was cancelled and transferred to Morgan without formal communication to me.",
     "Arlington", "TX"),

    (ts(2026,4,19,10,30),
     "Pattern documentation: Performance review February 2026 Robert agreed with my self-rating of 4 out of 4 on Accountability and Problem Solving. 3 out of 4 on Communication and Continuous Learning. This rating came two weeks before these incidents escalated. His conduct is inconsistent with this evaluation.",
     "Arlington", "TX"),

    (ts(2026,4,20,14,0),
     "Meeting April 20 2026 with Robert: Confirmed he was unaware Morgan had cancelled our 1:1 meetings since November 2025. Also confirmed he did not formally communicate Texas Water conference decision to me. Robert acknowledged these gaps.",
     "Arlington", "TX"),

    (ts(2026,4,19,18,0),
     "Private timestamped record April 19 2026: Morgan submitted Workday spend request for Texas Water conference without my formal approval as supervisor. Brad cannot approve this request on my behalf without a documented reason. This follows a 6 month pattern of supervisory bypass dating back to October 2025.",
     "Arlington", "TX"),

    # ── Role erosion pattern ──────────────────────────────────
    (ts(2026,4,20,15,0),
     "Role erosion pattern documented: Over 6 months tasks I was PM on were progressively handed to Morgan. My task list has been reduced to primarily Asset Management Plan and WTP Asset Management while Morgan manages water-side work independently. Evidence suggests Brad and Robert are coordinating Morgan's advancement without my input.",
     "Arlington", "TX"),

    (ts(2026,4,20,15,30),
     "3S scoring system recognition: Python-based 3S scoring system I developed reduced processing time from 6 hours to 30 minutes. Recognized publicly by director Alex. Robert has been building narrative that the system has problems while giving me a 4 out of 4 rating on problem solving in February 2026 review.",
     "Arlington", "TX"),

]

# ── Write to Firestore ─────────────────────────────────────────
def enc(email):
    return email.replace('.','_dot_').replace('@','_at_')

records_ref = (
    db.collection('users')
      .document(PHONE)
      .collection('emails')
      .document(EMAIL_KEY)
      .collection('records')
)

# Ensure user profile exists with real structure
# NOTE: uid field will be 'seeded' until user logs in and updates it
db.collection('users').document(PHONE).collection('profile').document('data').set({
    'uid':         'seeded',  # Will be updated on first login
    'phone':       PHONE,
    'country':     'United States',
    'plan':        'free',
    'status':      'active',
    'joinedAt':    firestore.SERVER_TIMESTAMP,
    'joinedLocal': datetime.now(timezone.utc).isoformat(),
}, merge=True)

# Ensure email doc exists
db.collection('users').document(PHONE).collection('emails').document(EMAIL_KEY).set({
    'email':    EMAIL,
    'addedAt':  firestore.SERVER_TIMESTAMP,
    'primary':  True,
}, merge=True)

# Write to BOTH paths so both query strategies find the records:
# 1. users/{phone}/emails/{email}/records/{id}  (nested - original)
# 2. users/{phone}/records/{id}                  (flat - new query strategy)
flat_ref = db.collection('users').document(PHONE).collection('records')

print(f"Writing {len(INCIDENTS)} incident records to Firestore...")
print(f"Nested path: users/{PHONE}/emails/{EMAIL_KEY}/records/")
print(f"Flat path:   users/{PHONE}/records/")
print()

for i, (timestamp, body, city, state) in enumerate(INCIDENTS):
    msg_id = f"seeded_{timestamp.strftime('%Y%m%d_%H%M')}_{i:02d}"
    record = {
        'body':           body,
        'messageSid':     msg_id,
        'from':           PHONE,
        'email':          EMAIL,
        'timestamp':      timestamp,
        'timestampLocal': timestamp.isoformat(),
        'source':         'sms',
        'seeded':         True,
        'location': {
            'city':             city,
            'state':            state,
            'country':          'US',
            'zip':              '',
            'lat':              32.7357,
            'lng':              -97.1081,
            'formatted':        f'{city}, {state}',
            'precision':        'city',
            'extractedAddress': None,
        },
        'hasMedia':  False,
        'mediaUrls': [],
    }
    # Write to nested path (original)
    records_ref.document(msg_id).set(record)
    # Write to flat path (new - for easier querying)
    flat_ref.document(msg_id).set(record)
    print(f"  ✅ {timestamp.strftime('%b %d %Y %H:%M')} — {body[:60]}...")

print()
print(f"Done! {len(INCIDENTS)} records written to Firestore.")
print(f"Log into soslogs.org with navenk@gmail.com to see them on the map.")
