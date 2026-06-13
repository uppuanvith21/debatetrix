from __future__ import annotations


LANGUAGES = [
    "English",
    "Hindi",
    "Telugu",
    "Tamil",
    "Kannada",
    "Malayalam",
    "Bengali",
    "Marathi",
    "Gujarati",
    "Punjabi",
    "Urdu",
    "Arabic",
    "French",
    "German",
    "Spanish",
    "Portuguese",
    "Japanese",
    "Korean",
    "Chinese",
]


TEXT = {
    "English": {
        "title": "Debates End. Facts Begin.",
        "subtitle": "AI-powered rivalry, controversy, debate, and viral-claim intelligence with transparent evidence scoring.",
        "fact_check": "Fact Verification Engine",
        "claim_label": "Paste a claim, post, debate point, or controversy",
        "analyze": "Analyze Claim",
        "debate": "Debate and Rivalry Analysis",
        "sources": "Trusted Verification Sources",
    },
    "Hindi": {
        "title": "बहस खत्म. तथ्य शुरू.",
        "subtitle": "पारदर्शी प्रमाण स्कोरिंग के साथ AI आधारित विवाद, बहस और वायरल दावों का विश्लेषण.",
        "fact_check": "तथ्य सत्यापन इंजन",
        "claim_label": "दावा, पोस्ट, बहस बिंदु या विवाद पेस्ट करें",
        "analyze": "दावे का विश्लेषण करें",
        "debate": "बहस और प्रतिद्वंद्विता विश्लेषण",
        "sources": "विश्वसनीय सत्यापन स्रोत",
    },
}


def t(language: str, key: str) -> str:
    return TEXT.get(language, TEXT["English"]).get(key, TEXT["English"][key])
