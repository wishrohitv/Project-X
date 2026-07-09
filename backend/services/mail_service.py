import resend
from settings import Settings

resend.api_key = Settings.RESEND_API_KEY


def send_otp(to: str, otp: str):
    try:
        params: resend.Emails.SendParams = {
            "from": "Verify email <verify@updates.memer.in>",
            "to": [to],
            "subject": "Verify your email",
            "html": f"<p>Your OTP is: {otp}</p>",
        }
        return resend.Emails.send(params)
    except Exception as e:
        print(f"Error sending OTP: {e}")
        raise Exception("Failed to send OTP")
