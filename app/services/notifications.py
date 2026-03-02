import httpx
from app.config import settings

async def send_ntfy_alert(med_name: str, days_left: int, user_name: str):
    """Sends a push notification via ntfy."""
    title = f"💊 Reorder Alert: {med_name}"
    message = f"{user_name} is running low! Only {days_left} days left."
    tags = "warning,pharmacy"
    priority = "urgent"
    click_url = settings.POCKET_ID_REDIRECT_URI.replace("/callback", "/") # Link back to app

    headers = {
        "Title": title,
        "Message": message,
        "Tags": tags,
        "Priority": priority,
        "Click": click_url,
        "Attach": "",
        "Filename": ""
    }

    url = f"{settings.NTFY_SERVER}/{settings.NTFY_TOPIC}"

    async with httpx.AsyncClient() as client:
        try:
            await client.post(url, headers=headers)
            print(f"Alert sent for {med_name}")
        except Exception as e:
            print(f"Failed to send ntfy alert: {e}")
