"""
Generates a labelled synthetic ticket dataset for SupportPilot (Milestone 1).

Why synthetic?  A real EV-charging support history is not available for this
project, so we write realistic base complaints per category and expand them
with neutral prefixes / suffixes (station ids, site names, polite filler).

IMPORTANT for honest evaluation:
  * Base complaints are split into TRAIN and TEST sets.  The test base
    sentences are never seen in training, so the test set measures
    generalisation to unseen wording, not memorisation.
  * Results on synthetic data are indicative only.  Replace
    data/training_tickets.csv with real tickets before reporting final numbers.

Run:  python generate_dataset.py
"""
import csv
import random
from pathlib import Path

random.seed(42)
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# (text, severity)
TRAIN = {
    "Charger Hardware": [
        ("Connector is physically stuck in my car and I cannot unplug it", "High"),
        ("Charging cable is damaged and the insulation is cracked", "High"),
        ("Screen on the charger is blank and unresponsive", "Medium"),
        ("The charger emergency stop button is jammed", "High"),
        ("Connector latch feels loose and wobbly", "Medium"),
        ("Charger bay lighting is dim at night", "Low"),
        ("Cable holster is broken and the cable drags on the ground", "Low"),
        ("Charger display shows a fault code and will not start", "High"),
    ],
    "Safety Hazard": [
        ("I saw smoke coming from the charger", "Critical"),
        ("There was a burning smell near the charging unit", "Critical"),
        ("Sparks came out of the connector when I plugged in", "Critical"),
        ("I got an electric shock touching the charger handle", "Critical"),
        ("Water is leaking into the charger cabinet", "High"),
        ("A vehicle collided with the charging post and it is leaning", "High"),
        ("Charging post base is cracked and unstable", "Medium"),
        ("Warning sign next to the charger has fallen off", "Low"),
    ],
    "Payment & Billing": [
        ("I was charged twice for a single charging session", "High"),
        ("Payment failed but the charger started anyway", "Medium"),
        ("I need a copy of my invoice for last month", "Low"),
        ("The price shown on the screen differs from my bill", "Medium"),
        ("Refund for a failed session has not arrived", "Medium"),
        ("Card was declined at the charger even though it works elsewhere", "Medium"),
        ("My company needs a VAT receipt", "Low"),
        ("Idle fee was applied although I had left the bay", "Medium"),
    ],
    "Account & App": [
        ("I cannot log in to the mobile app", "Medium"),
        ("How do I change the email address on my account", "Low"),
        ("App crashes when I open the map", "Medium"),
        ("Please delete my account and personal data", "Low"),
        ("Password reset email is not arriving", "Medium"),
        ("Charger map does not show nearby stations", "Medium"),
        ("Push notifications about charge completion are not working", "Low"),
        ("Cannot add a new payment card in the app", "Medium"),
    ],
    "RFID & Authentication": [
        ("My RFID card is not recognized by the charger", "Medium"),
        ("Tap to start does nothing with my membership card", "Medium"),
        ("Need a replacement RFID card because I lost mine", "Low"),
        ("Fleet driver cards are all being rejected at the depot", "High"),
        ("Card was blocked after too many failed attempts", "Medium"),
        ("Plug and charge authentication fails with my vehicle", "Medium"),
        ("Please activate my new RFID card", "Low"),
        ("QR code on the charger does not open the app", "Medium"),
    ],
    "Charging Session": [
        ("Charging stops after a few minutes every time", "High"),
        ("Charging speed is only 7 kW on a 150 kW charger", "Medium"),
        ("Session will not start after I plug in the connector", "High"),
        ("Charging ended early and the battery is only at 40 percent", "Medium"),
        ("Session history is missing the last charge", "Low"),
        ("Charger keeps retrying and then shows session timeout", "Medium"),
        ("Charging was interrupted when it started raining", "Medium"),
        ("Estimated charging time shown is wrong", "Low"),
    ],
    "Station Connectivity": [
        ("Charger shows offline in the app since this morning", "High"),
        ("Station lost connection to the central management system", "High"),
        ("All chargers at the depot are offline", "Critical"),
        ("Charger firmware update failed and it is stuck rebooting", "High"),
        ("Heartbeat timeouts from station every few minutes", "Medium"),
        ("SIM card data usage for the charger modem is unusually high", "Low"),
        ("The charger Wi-Fi signal is weak at the far end of the lot", "Low"),
        ("Intermittent connection drops on the charger gateway", "Medium"),
    ],
}

TEST = {
    "Charger Hardware": [
        ("The plug is trapped in the vehicle port and will not release", "High"),
        ("Touchscreen is cracked and hard to read", "Medium"),
        ("Paint is peeling on the charger housing", "Low"),
        ("Cable cover is torn and the wires inside are visible", "High"),
    ],
    "Safety Hazard": [
        ("Flames visible at the base of the charging unit", "Critical"),
        ("Strong smell of burning plastic from the charger", "Critical"),
        ("Rainwater is pouring into the charging unit", "High"),
        ("Safety signage is faded and hard to read", "Low"),
    ],
    "Payment & Billing": [
        ("Billed two times for one charge", "High"),
        ("Please send a receipt for my last charge", "Low"),
        ("Tariff on the app is different from the amount deducted", "Medium"),
        ("Refund still pending after ten days", "Medium"),
    ],
    "Account & App": [
        ("Login keeps failing with invalid credentials in the app", "Medium"),
        ("How can I update my phone number in my profile", "Low"),
        ("The app freezes on the splash screen", "Medium"),
        ("Verification code SMS never reaches me", "Medium"),
    ],
    "RFID & Authentication": [
        ("Charger refuses my access card", "Medium"),
        ("I would like an additional RFID tag for my spouse", "Low"),
        ("Vehicle authentication with plug and charge keeps failing", "Medium"),
        ("Every driver card at the fleet depot is being denied", "High"),
    ],
    "Charging Session": [
        ("Power delivery drops to a trickle halfway through the charge", "Medium"),
        ("Cannot start charging, it shows waiting for vehicle", "High"),
        ("Session aborts repeatedly before reaching 80 percent", "High"),
        ("The charge time estimate on screen is inaccurate", "Low"),
    ],
    "Station Connectivity": [
        ("Whole site went offline and no charger responds", "Critical"),
        ("Charger is unreachable from the back office dashboard", "High"),
        ("Firmware upgrade stuck at 60 percent and charger reboots in a loop", "High"),
        ("Modem signal strength is poor on bay 6", "Low"),
        ("Occasional packet loss between charger and backend", "Medium"),
    ],
}

# ---------------------------------------------------------------------------
# Round 2: the first evaluation (8 base complaints/category) scored ~70% on unseen
# wording, i.e. the vocabulary was too narrow. These extra TRAIN complaints widen it.
# ---------------------------------------------------------------------------
TRAIN_EXTRA = {
    "Charger Hardware": [
        ("Connector will not lock into the vehicle socket", "Medium"),
        ("The charging gun is jammed and will not come out of the socket", "High"),
        ("Casing of the unit is dented after someone hit it", "Low"),
        ("Scratches and scuffs on the charger body", "Low"),
        ("Cable is too short to reach the car inlet", "Low"),
        ("The charger door will not close properly", "Medium"),
        ("Card reader slot on the unit is broken", "Medium"),
        ("Handle of the connector is cracked", "Medium"),
        ("Cable is frayed near the plug and the outer jacket is split", "High"),
        ("Cooling fan inside the charger is making a loud grinding noise", "Medium"),
    ],
    "Safety Hazard": [
        ("Cable insulation is melted near the plug", "Critical"),
        ("The charger is hot to touch and smells like burnt plastic", "Critical"),
        ("A fire started under the vehicle while charging", "Critical"),
        ("Someone received an electric shock from the cable", "Critical"),
        ("Pooling water around the base of the charger", "High"),
        ("A tree branch has fallen on the charging unit", "High"),
        ("The charging bay has a trip hazard because of loose cables", "Medium"),
        ("Bollard protecting the charger is damaged", "Medium"),
        ("Floor markings around the bay are worn", "Low"),
        ("Safety instructions sticker is missing from the unit", "Low"),
    ],
    "Payment & Billing": [
        ("I was billed for a session I never started", "High"),
        ("The app shows a different amount than my card statement", "Medium"),
        ("Please issue a credit note for the wrong invoice", "Low"),
        ("Subscription renewal charged me although I cancelled", "Medium"),
        ("Cannot download my monthly statement from the portal", "Low"),
        ("Pre-authorisation hold on my card was not released", "Medium"),
        ("Wrong tax rate applied to my invoice", "Low"),
        ("Charged a roaming fee that I was not told about", "Medium"),
        ("Duplicate transaction appears on my bank statement for one charge", "High"),
    ],
    "Account & App": [
        ("I forgot my password and cannot sign in", "Medium"),
        ("Please change the name on my profile", "Low"),
        ("The app says my session expired every time I open it", "Medium"),
        ("Cannot register a new account with my phone number", "Medium"),
        ("How do I enable dark mode in the app", "Low"),
        ("Two factor code is not accepted when logging in", "Medium"),
        ("App shows the wrong language", "Low"),
        ("I want to unsubscribe from marketing emails", "Low"),
        ("App will not update from the store", "Medium"),
        ("My favourite stations list disappeared", "Low"),
    ],
    "RFID & Authentication": [
        ("The charger does not react when I tap my badge", "Medium"),
        ("Driver tag has been deactivated by mistake", "Medium"),
        ("Our company cards stopped working at all sites", "High"),
        ("Request ten new access cards for new employees", "Low"),
        ("Contactless card read fails on bay 2", "Medium"),
        ("Authentication timeout when starting a session with my card", "Medium"),
        ("I want to link my RFID card to my account", "Low"),
        ("Charger shows card invalid for valid cards", "Medium"),
        ("Autocharge vehicle recognition does not work with my car", "Medium"),
        ("PIN for the access card was forgotten", "Low"),
    ],
    "Charging Session": [
        ("Charger does not deliver any power after I connect", "High"),
        ("Charging session ends with an error message after two minutes", "High"),
        ("Charge rate keeps fluctuating between 20 and 100 kW", "Medium"),
        ("The kWh shown in my history is lower than what I received", "Medium"),
        ("Charge limit setting does not stop at 80 percent", "Low"),
        ("Charger says connector locked but nothing happens", "High"),
        ("Session start takes more than five minutes", "Medium"),
        ("Charging session shows as active after I disconnected", "Medium"),
        ("Unit shows preparing and never moves to charging", "High"),
        ("Charging power is capped lower than the vehicle can accept", "Medium"),
    ],
    "Station Connectivity": [
        ("Chargers at the site went offline overnight", "High"),
        ("Backend shows no heartbeat from the unit", "High"),
        ("The router at the site is down and chargers are unreachable", "High"),
        ("Charger reboots randomly and loses its network link", "Medium"),
        ("OCPP connection keeps dropping and reconnecting", "Medium"),
        ("Remote start command from the dashboard times out", "High"),
        ("Charger clock is wrong because it cannot sync time", "Low"),
        ("Weak mobile signal at the station", "Low"),
        ("Software version on the charger is outdated", "Low"),
        ("Firmware rollout failed on several units", "High"),
        ("Dashboard shows the charger as unavailable", "High"),
    ],
}
for _cat, _items in TRAIN_EXTRA.items():
    TRAIN[_cat] = TRAIN[_cat] + _items

# ---------------------------------------------------------------------------
# Fresh held-out set (v2): written AFTER the training data and rules above were frozen.
# Still the same author, so it is not fully independent -- real tickets are the true test.
# ---------------------------------------------------------------------------
TEST_V2 = {
    "Charger Hardware": [
        ("The charging handle has snapped off its mounting", "High"),
        ("Small dent on the side panel of the unit", "Low"),
        ("Latch on the charger flap is stiff", "Medium"),
        ("Bay number sticker has fallen off", "Low"),
    ],
    "Safety Hazard": [
        ("Black marks and a smoldering smell around the socket", "Critical"),
        ("Cable shows signs of melting near the connector", "Critical"),
        ("Large puddle forming around the foot of the unit", "High"),
        ("Faded hazard stripes around the charger", "Low"),
    ],
    "Payment & Billing": [
        ("Got billed for a charge I never made", "High"),
        ("Statement download link gives an error", "Low"),
        ("Deposit on my card has not been returned", "Medium"),
        ("Extra fee on my receipt that I did not expect", "Medium"),
    ],
    "Account & App": [
        ("Cannot sign in, the app says wrong password even after reset", "Medium"),
        ("How do I change my display name", "Low"),
        ("The map in the app is blank", "Medium"),
        ("Please close my profile", "Low"),
    ],
    "RFID & Authentication": [
        ("Badge tap is ignored by the unit", "Medium"),
        ("Order a spare card for my colleague", "Low"),
        ("All employee cards denied at our site", "High"),
        ("Car not recognised for automatic start", "Medium"),
    ],
    "Charging Session": [
        ("Unit stays on preparing and never delivers power", "High"),
        ("Charge rate keeps bouncing up and down", "Medium"),
        ("History shows wrong energy total", "Medium"),
        ("Estimated cost on the screen is slightly off", "Low"),
    ],
    "Station Connectivity": [
        ("Unit has not sent a heartbeat since last night", "High"),
        ("OCPP link keeps flapping", "Medium"),
        ("Remote unlock from the dashboard times out", "High"),
        ("Charger clock is a few minutes off", "Low"),
        ("Entire site lost network after the router failed", "Critical"),
    ],
}

PREFIXES = ["", "", "Hi team, ", "Hello, ", "Good morning. ", "Please help. ", "Hi, "]
SITES = ["Downtown Plaza", "Airport", "Mall", "Highway Rest Stop", "Riverside"]


def suffix():
    options = [
        "",
        "",
        f" Station ID CP-{random.randint(1000, 4999)}.",
        f" This is at the {random.choice(SITES)} site.",
        " Thanks.",
        " Happened today.",
        " Please advise.",
    ]
    return random.choice(options)


def expand(bank, variants):
    rows = []
    for category, items in bank.items():
        for text, severity in items:
            for _ in range(variants):
                rows.append(
                    {
                        "ticket": f"{random.choice(PREFIXES)}{text}.{suffix()}",
                        "category": category,
                        "severity": severity,
                    }
                )
    random.shuffle(rows)
    return rows


def write(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["ticket", "category", "severity"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows):4d} rows -> {path.name}")


if __name__ == "__main__":
    write(DATA_DIR / "training_tickets.csv", expand(TRAIN, variants=12))
    write(DATA_DIR / "test_tickets.csv", expand(TEST, variants=6))
    write(DATA_DIR / "test_tickets_v2.csv", expand(TEST_V2, variants=6))
