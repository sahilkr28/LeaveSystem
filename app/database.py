from datetime import datetime, timezone
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base
try:
    from .config import Config
except (ImportError, ValueError):
    from config import Config

# Create SQLAlchemy Database Engine
database_url = Config.SQLALCHEMY_DATABASE_URI

engine_kwargs = {"future": True}
if database_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Production PostgreSQL connection pooling parameters
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

engine = create_engine(database_url, **engine_kwargs)

# Scoped Thread-Safe Session
db_session = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        future=True
    )
)

Base = declarative_base()
Base.query = db_session.query_property()

def check_db_connection() -> bool:
    """Verifies live database connectivity for health checks."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"[DB HEALTH ERROR] Failed to connect to database: {e}")
        return False

def init_db(seed: bool = True):
    """Initializes tables and optionally seeds realistic initial university ERP records."""
    try:
        from .models import Leave, MaintenanceTicket
    except (ImportError, ValueError):
        from models import Leave, MaintenanceTicket
    Base.metadata.create_all(bind=engine)
    
    if seed:
        try:
            # Seed only if database table is currently empty
            existing_leaves = db_session.query(Leave).first()
            if not existing_leaves:
                sample_leaves = [
                    Leave(
                        student_name="Aarav Sharma",
                        roll_number="21BCE1042",
                        hostel_block="Block A (Aryabhatta)",
                        room_number="A-304",
                        contact_number="+91-9876543210",
                        parent_contact="+91-9876500001",
                        leave_type="Day Leave",
                        start_date="2026-11-25",
                        out_time="15:00",
                        expected_return_date="2026-11-25",
                        expected_return_time="20:30",
                        destination="City Central Library",
                        reason="Attending IEEE research seminar and reference book issue",
                        status="Pending",
                        warden_remarks=None
                    ),
                    Leave(
                        student_name="Rohan Verma",
                        roll_number="21BIT0892",
                        hostel_block="Block B (Vidyasagar)",
                        room_number="B-112",
                        contact_number="+91-9811223344",
                        parent_contact="+91-9811220000",
                        leave_type="Night Leave",
                        start_date="2026-11-28",
                        out_time="08:00",
                        expected_return_date="2026-11-30",
                        expected_return_time="20:00",
                        destination="Home - Sector 14, Gurugram",
                        reason="Family wedding ceremony. Parent letter submitted.",
                        status="Approved",
                        warden_remarks="Parent confirmation verified via telephonic log."
                    ),
                    Leave(
                        student_name="Devika Nair",
                        roll_number="22BME0341",
                        hostel_block="Block C (Gargi)",
                        room_number="C-208",
                        contact_number="+91-9744332211",
                        parent_contact="+91-9744330000",
                        leave_type="Day Leave",
                        start_date="2026-11-24",
                        out_time="16:30",
                        expected_return_date="2026-11-24",
                        expected_return_time="20:45",
                        destination="University Medical Centre",
                        reason="Dental checkup and routine health follow-up",
                        status="Approved",
                        warden_remarks="Allowed till 21:00 strictly."
                    )
                ]
                for leave in sample_leaves:
                    db_session.add(leave)

            existing_tickets = db_session.query(MaintenanceTicket).first()
            if not existing_tickets:
                sample_tickets = [
                    MaintenanceTicket(
                        student_name="Siddharth Malhotra",
                        roll_number="21BCE1105",
                        hostel_block="Block A (Aryabhatta)",
                        room_number="A-214",
                        category="Electrical",
                        urgency="High",
                        description="Ceiling fan regulator short-circuit and main switch sparking upon toggle.",
                        status="Pending",
                        warden_notes=None
                    ),
                    MaintenanceTicket(
                        student_name="Kunal Deshmukh",
                        roll_number="22BIT0412",
                        hostel_block="Block B (Vidyasagar)",
                        room_number="B-405",
                        category="Wi-Fi",
                        urgency="Medium",
                        description="Hostel LAN wall port loose; Wi-Fi access point dropping connection continuously.",
                        status="In Progress",
                        warden_notes="Forwarded to Campus Network Operations ticket #IT-4921."
                    ),
                    MaintenanceTicket(
                        student_name="Meera Iyer",
                        roll_number="21ECE0198",
                        hostel_block="Block C (Gargi)",
                        room_number="C-102",
                        category="Plumbing",
                        urgency="Emergency",
                        description="Bathroom tap valve leakage causing water accumulation near doorway.",
                        status="Resolved",
                        warden_notes="Technician replaced washer valve. Flow tested and cleared.",
                        resolved_at=datetime.now(timezone.utc)
                    )
                ]
                for ticket in sample_tickets:
                    db_session.add(ticket)

            db_session.commit()
        except Exception as e:
            db_session.rollback()
            print(f"[DB SEED WARNING] Non-fatal seeding notice: {e}")
