import resend
from modules import APP_NAME
from settings import Settings

resend.api_key = Settings.RESEND_API_KEY


def send_otp(to: str, otp: str):
    try:
        params: resend.Emails.SendParams = {
            "from": "Verify email <verify@updates.memer.in>",
            "to": [to],
            "subject": f"Verify your email - {APP_NAME}",
            "html": f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
            </head>
            <body style="margin:0;padding:40px;font-family:Arial,Helvetica,sans-serif;background:#f5f5f5;">
                <div style="max-width:420px;margin:0 auto;background:#ffffff;padding:32px;border-radius:8px;text-align:center;">
                    <h2 style="margin:0 0 16px;color:#222;">Verify Your Email</h2>

                    <p style="margin:0 0 24px;color:#555;font-size:15px;">
                        Use the verification code below to continue.
                    </p>

                    <div style="display:inline-block;padding:14px 28px;background:#f1f3f5;border-radius:6px;
                                font-size:28px;font-weight:bold;letter-spacing:6px;color:#111;">
                        {otp}
                    </div>

                    <p style="margin:24px 0 0;color:#777;font-size:13px;">
                        This code expires in <strong>10 minutes</strong>.
                    </p>

                    <p style="margin:8px 0 0;color:#999;font-size:12px;">
                        If you didn't request this, you can safely ignore this email.
                    </p>
                </div>
            </body>
            </html>
            """,
        }
        return resend.Emails.send(params)
    except Exception as e:
        print(f"Error sending OTP: {e}")
        raise Exception("Failed to send OTP")
