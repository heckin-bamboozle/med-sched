from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    pocket_id_sub = Column(String, unique=True, index=True) # Subject ID from Pocket ID
    name = Column(String)
    email = Column(String)
    is_admin = Column(Boolean, default=False)

    medications = relationship("Medication", back_populates="owner")

class Medication(Base):
    __tablename__ = "medications"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))

    # Drug Info
    ndc_code = Column(String)
    brand_name = Column(String)
    generic_name = Column(String)
    form = Column(String) # Tablet, Liquid, etc.
    dose_strength = Column(String) # 500mg, etc.

    # Regimen
    pills_per_dose = Column(Integer)
    doses_per_day = Column(Integer)
    taken_at = Column(String) # Comma separated times e.g., "08:00,20:00"

    # Inventory
    current_count = Column(Integer)
    initial_count = Column(Integer)
    last_restocked = Column(DateTime, default=datetime.utcnow)

    # Alerts
    alert_threshold_days = Column(Integer, default=5)
    alert_active = Column(Boolean, default=False) # True if currently below threshold
    last_alert_sent = Column(DateTime, nullable=True)

    owner = relationship("User", back_populates="medications")

class DoseLog(Base):
    __tablename__ = "dose_logs"
    id = Column(Integer, primary_key=True)
    medication_id = Column(Integer, ForeignKey("medications.id"))
    scheduled_time = Column(DateTime)
    taken = Column(Boolean, default=True) # False if missed
    logged_at = Column(DateTime, default=datetime.utcnow)
    logged_by_id = Column(Integer, ForeignKey("users.id"))
