from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select, func
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models import Medication, User
from app.services.notifications import send_ntfy_alert

async def check_medication_levels():
    """Daily job to check pill counts and send alerts."""
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        meds = db.query(Medication).all()

        for med in meds:
            if med.current_count <= 0:
                continue

            daily_usage = med.pills_per_dose * med.doses_per_day
            if daily_usage == 0: continue

            days_left = med.current_count / daily_usage

            if days_left <= med.alert_threshold_days:
                # Check if we already sent an alert today to avoid spamming within the same day
                # Or logic: Send daily until resolved.
                # Here: Send if last alert was > 23 hours ago or never sent
                should_send = False
                if not med.last_alert_sent:
                    should_send = True
                elif (now - med.last_alert_sent).total_seconds() > 86400: # 24 hours
                    should_send = True

                if should_send:
                    owner = db.query(User).filter(User.id == med.owner_id).first()
                    await send_ntfy_alert(med.brand_name, int(days_left), owner.name)
                    med.last_alert_sent = now
                    med.alert_active = True
                    db.commit()
            else:
                # Reset alert status if stock is healthy
                if med.alert_active:
                    med.alert_active = False
                    db.commit()
    finally:
        db.close()

scheduler = AsyncIOScheduler()
scheduler.add_job(check_medication_levels, CronTrigger(hour=9, minute=0)) # Run daily at 9 AM
