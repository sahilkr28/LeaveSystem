from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime
try:
    from .database import Base
except (ImportError, ValueError):
    from database import Base

def current_time_utc():
    return datetime.now(timezone.utc)

class Leave(Base):
    """Hostel Outing and Leave Application Model"""
    __tablename__ = "leaves"

    id = Column(Integer, primary_key=True, index=True)
    student_name = Column(String(100), nullable=False)
    roll_number = Column(String(50), nullable=False, index=True)
    hostel_block = Column(String(50), nullable=False)
    room_number = Column(String(20), nullable=False)
    contact_number = Column(String(20), nullable=False)
    parent_contact = Column(String(20), nullable=False)
    leave_type = Column(String(20), nullable=False) # 'Day Leave' or 'Night Leave'
    start_date = Column(String(20), nullable=False)
    out_time = Column(String(10), nullable=False)
    expected_return_date = Column(String(20), nullable=False)
    expected_return_time = Column(String(10), nullable=False) # For Day Leave: <= 21:00
    destination = Column(String(255), nullable=True)
    reason = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default='Pending', index=True) # 'Pending', 'Approved', 'Rejected'
    warden_remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=current_time_utc, index=True)
    updated_at = Column(DateTime, default=current_time_utc, onupdate=current_time_utc)

    def to_dict(self):
        return {
            "id": self.id,
            "student_name": self.student_name,
            "roll_number": self.roll_number,
            "hostel_block": self.hostel_block,
            "room_number": self.room_number,
            "contact_number": self.contact_number,
            "parent_contact": self.parent_contact,
            "leave_type": self.leave_type,
            "start_date": self.start_date,
            "out_time": self.out_time,
            "expected_return_date": self.expected_return_date,
            "expected_return_time": self.expected_return_time,
            "destination": self.destination or "Local Outing",
            "reason": self.reason,
            "status": self.status,
            "warden_remarks": self.warden_remarks or "",
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else ""
        }

class MaintenanceTicket(Base):
    """Hostel Room Maintenance Ticket Model"""
    __tablename__ = "maintenance_tickets"

    id = Column(Integer, primary_key=True, index=True)
    student_name = Column(String(100), nullable=False)
    roll_number = Column(String(50), nullable=False, index=True)
    hostel_block = Column(String(50), nullable=False)
    room_number = Column(String(20), nullable=False)
    category = Column(String(50), nullable=False, index=True) # 'Electrical', 'Plumbing', 'Wi-Fi', 'Carpentry', 'Other'
    urgency = Column(String(20), nullable=False, default='Medium') # 'Low', 'Medium', 'High', 'Emergency'
    description = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default='Pending', index=True) # 'Pending', 'In Progress', 'Resolved'
    warden_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=current_time_utc, index=True)
    resolved_at = Column(DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "student_name": self.student_name,
            "roll_number": self.roll_number,
            "hostel_block": self.hostel_block,
            "room_number": self.room_number,
            "category": self.category,
            "urgency": self.urgency,
            "description": self.description,
            "status": self.status,
            "warden_notes": self.warden_notes or "",
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else "",
            "resolved_at": self.resolved_at.strftime("%Y-%m-%d %H:%M") if self.resolved_at else ""
        }
