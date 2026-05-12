import os

import resend
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.environ.get("RESEND_API_KEY")


def send_otp(to: str, otp: str):
    try:
        params: resend.Emails.SendParams = {
            "from": "Verify Email <verify@updates.memer.in>",
            "to": [to],
            "subject": "Verify Email",
            "html": f"<p>Your OTP is: {otp}</p>",
        }
        return resend.Emails.send(params)
    except Exception as e:
        print(f"Error sending OTP: {e}")
        raise Exception("Failed to send OTP")
