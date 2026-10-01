"""Category taxonomy and the team that owns each category (support-policy.pdf s6).

We keep the helpdesk's own 11 categories so the output is directly comparable
with the bot tag. Each category is defined by a list of intents; each intent is
a regex that is matched against the ticket text. Patterns are deliberately
loose (common misspellings, shorthand like 'rfnd', 'dlvry') because the notes
and messages are full of both.
"""
import re

# category -> owning team (policy s6). Frontline categories are owned by the
# channel's frontline team, resolved at run time from the ticket's channel.
OWNER = {
    "Delivery & Shipping": "Logistics",
    "Billing & Payments": "Billing",
    "Returns & Refunds": "Returns Desk",
    "Warranty & Repair": "Escalations & Warranty",
    "Connectivity": "Frontline",
    "Charging & Battery": "Frontline",
    "Audio Quality": "Frontline",
    "App & Firmware": "Frontline",
    "Account & Login": "Frontline",
    "Product Enquiry": "Frontline",
    "Other": "Frontline",
}
CHANNEL_FRONTLINE = {"chat": "Chat Frontline", "social": "Chat Frontline",
                     "email": "Email Frontline", "voice": "Voice Frontline"}
CATEGORIES = list(OWNER)


def owner_team(category, channel):
    team = OWNER.get(category, "Frontline")
    return CHANNEL_FRONTLINE.get(channel, "Chat Frontline") if team == "Frontline" else team


# (intent, category, pattern). Order matters only for ties in score.
INTENTS = [
    # --- Delivery & Shipping (Logistics)
    ("not_delivered", "Delivery & Shipping",
     r"not (?:been )?deliver|(?:ord|order|shipment|package|parcel)\w* not (?:rec|rcv|deliv)|not rece?i?v|nothing (?:in hand|at my door|has come|arrived)|"
     r"haven'?t (?:received|got)|dl?vr?y|deliver\w* delay|delayed|stuck|out for delivery|tracking|courier|awb|rto|"
     r"re-?ship|lost in transit|marked (?:it )?delivered|nobody .*got|where is my|order status|still says processing|"
     r"order has not moved|status has not moved|nothing (?:to )?show up|then nothing|no update on (?:my )?(?:order|delivery)"),
    ("wrong_item", "Delivery & Shipping",
     r"wrong (?:item|product|variant|colou?r (?:sent|delivered|received)|model)|incorrect product|ordered \w+, got \w+|got the wrong|not what i (?:ordered|asked for)"),
    ("transit_damage", "Delivery & Shipping",
     r"transit damage|damaged in transit|(?:rece?i?v|rcv)\w* damaged|damaged (?:product|unit|box|parcel|package)|box (?:was )?(?:crushed|torn|broken)|arrived (?:broken|damaged|cracked)"),
    ("address_change", "Delivery & Shipping",
     r"address (?:update|change)|change (?:the |my )?(?:delivery )?address|wrong pin ?code|pincode"),
    # --- Billing & Payments (Billing)
    ("double_charge", "Billing & Payments",
     r"double (?:charge|payment|debit)|charged twice|duplicate (?:payment|txn|transaction)|same amount twice|debited twice|two (?:payments|debits)|utr"),
    ("payment_no_order", "Billing & Payments",
     r"(?:debited|deducted)\w*,? (?:but )?(?:no|without) ord|amount deducted without|payment debited|failed ord\w* after payment|"
     r"money (?:debit|deduct)\w* but order not|order not showing|shows success,? (?:but )?(?:your )?app shows nothing|upi shows success|payment (?:failed|stuck)|auto-?rfnd"),
    ("invoice", "Billing & Payments",
     r"invoi?c?e|gst|gstin|bill copy|tax invoice"),
    ("coupon", "Billing & Payments",
     r"coupon|promo|discount|offer (?:not|wasn)|price (?:drop|adj|match)|cashback"),
    # --- Returns & Refunds (Returns Desk)
    ("refund_status", "Returns & Refunds",
     r"refund (?:not|still|pending|delay|was promised)|r(?:e)?fu?n?d (?:pending|delay|not credited|reprocessed)|waiting for (?:my )?refund|"
     r"amount is nowhere|refund status|return (?:was )?accepted but|not (?:yet )?credited|where is my refund"),
    ("pickup", "Returns & Refunds",
     r"pick-?up|pkp|nobody came|no one (?:showed|came)|waiting for your courier to collect"),
    ("cancellation", "Returns & Refunds",
     r"cancel|stop the shipment|don'?t ship|change of mind"),
    # --- Warranty & Repair (Tier 2)
    ("rma_status", "Warranty & Repair",
     r"rma|repair|service c(?:e|en)n?tre|warranty claim|wty|sent the unit|claim number|sent (?:it|my \w+) (?:in|for)"),
    ("hardware_fault", "Warranty & Repair",
     r"strap|pin (?:broke|issue)|display (?:unresponsive|not|dead|blank)|unresponsive display|touch (?:issue|not|screen)|"
     r"won'?t (?:power|turn) on|not (?:powering|turning) on|no power|unit dead|dead on arrival|\bdoa\b|screen (?:cracked|dead|blank)"),
    # --- Frontline: product categories
    ("pairing", "Connectivity",
     r"\bpair(?!s? of)|discoverable|not (?:showing|showing up) in bluetooth|bluetooth"),
    ("dropouts", "Connectivity",
     r"disconnect|drop ?outs?|connection (?:drop|lost)|goes silent for a second|cuts? out|stutter|wi-?fi|network setup|connect to (?:my )?(?:wifi|network)"),
    ("battery", "Charging & Battery",
     r"batt?ery|dies by|drain|backup|(?:not|no) charg|won'?t charge|charging case (?:dead|not)|case (?:not charging|no led|dead)|taking charge|charge (?:only|fast|slow)"),
    ("audio", "Audio Quality",
     r"distort|crackl|static|buzz|frying|hiss|(?:one|single|left|right) (?:side|ear)\w*.*(?:silent|mute|no audio|only)|no audio|"
     r"music in one ear|mic\b|microphone|underwater|can'?t hear me|useless for meetings|sound (?:quality|is)|low volume"),
    ("app_fw", "App & Firmware",
     r"\bapp\b|firmware|\bfw\b|update (?:failed|stuck|hang)|progress bar|crash|bricked|recovery mode|beta build"),
    ("login", "Account & Login",
     r"log ?in|otp|login code|account (?:locked|unlock|blocked)|password|sign ?in"),
    ("enquiry", "Product Enquiry",
     r"compatib|will (?:this|it|the watch)|does (?:it|this|\w+ \w*) (?:work|support)|can i (?:connect|use)|before i buy|pre-?sales|"
     r"spec sheet|product enquiry|waterproof|survive a shower|talk to a|which (?:one|model)|is my \w+ compatible|old nokia"),
]
COMPILED = [(i, c, re.compile(p, re.I)) for i, c, p in INTENTS]


def match_intents(text):
    """Return list of (intent, category) whose pattern hits the text."""
    if not text:
        return []
    return [(i, c) for i, c, rx in COMPILED if rx.search(text)]
