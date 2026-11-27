"""Builds data/tickets.csv: IT tickets labelled with category, sub-category and severity."""
import random
from pathlib import Path
import pandas as pd

LEVELS = ["Low", "Medium", "High", "Critical"]
# (category, sub_category, base severity index): typical phrasings
TAXONOMY = {
    ("Network Connectivity", "VPN Access", 2): ["VPN connection failing on corporate network", "unable to connect to VPN, connection timed out", "VPN client keeps disconnecting", "cannot reach the VPN gateway from home"],
    ("Network Connectivity", "WiFi", 1): ["office WiFi keeps dropping", "cannot connect to the guest WiFi", "WiFi is very slow on the third floor"],
    ("Network Connectivity", "LAN / Internet", 2): ["no internet access at my desk", "ethernet port is not working", "the network is down in the whole office"],
    ("Software", "Installation", 1): ["software installation error", "installer fails with error 1603", "cannot install the latest update"],
    ("Software", "Licensing", 0): ["license key has expired", "need my design software license activated", "Office activation failed"],
    ("Software", "Application Error", 1): ["application crashes on launch", "ERP application freezes while saving", "error message when opening the CRM"],
    ("Access", "Account", 1): ["password reset required", "my account is locked out", "forgot my password and cannot log in"],
    ("Access", "Permissions", 0): ["need access to the shared drive", "request admin rights on my laptop", "access denied on the SharePoint folder"],
    ("Hardware", "Printer", 0): ["printer not responding", "printer jams repeatedly", "cannot print to the floor printer"],
    ("Hardware", "Laptop", 1): ["laptop will not boot", "laptop battery drains very fast", "screen keeps flickering on my laptop"],
    ("Hardware", "Peripherals", 0): ["monitor shows no signal", "keyboard is not working", "mouse is unresponsive"],
}
UP = ["Unable to work: ", "Urgent - ", "All users affected: ", "Since this morning, "]
MID = ["", "Hi team, ", "Issue: ", "Please help - "]
DOWN = ["Whenever possible, ", "Minor issue: ", "Question: ", "Not urgent - "]
END = ["", " Tried restarting but it persists.", " Started yesterday.", " An error message appears."]


def build(path, n=2500, seed=42):
    rnd, rows = random.Random(seed), []
    for _ in range(n):
        (cat, sub, base), phrases = rnd.choice(list(TAXONOMY.items()))
        delta, pre = rnd.choice([(1, UP), (0, MID), (0, MID), (-1, DOWN)])
        text = rnd.choice(pre) + rnd.choice(phrases) + "." + rnd.choice(END)
        rows.append((text[0].upper() + text[1:], cat, sub, LEVELS[min(3, max(0, base + delta))]))
    df = pd.DataFrame(rows, columns=["text", "category", "sub_category", "severity"]).drop_duplicates()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return df
