import socket
import pytest
from app.app import create_app
from app.database import db_session, Base, engine
from app.models import Leave, MaintenanceTicket

@pytest.fixture(scope="module")
def app_instance():
    """Create test application configured with SQLite testing database."""
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret-key",
        "WARDEN_PASSWORD": "test_warden_pass_123"
    })
    
    with app.app_context():
        Base.metadata.create_all(bind=engine)
        yield app

@pytest.fixture
def client(app_instance):
    """Test client for HTTP requests."""
    return app_instance.test_client()

def test_health_telemetry_endpoint(client):
    """
    Test /health endpoint returns JSON {"status": "healthy", "host": "<hostname>", "db": "connected"}.
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data is not None
    assert data.get("status") == "healthy"
    assert data.get("db") == "connected"
    assert data.get("host") == socket.gethostname()

def test_student_view_page_and_footer_telemetry(client):
    """
    Test Student View (/) loads successfully and includes socket.gethostname() in footer.
    """
    response = client.get("/")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    
    # Check university portal headers and features
    assert "HOSTEL ERP PORTAL" in html
    assert "Student Residential Desk" in html
    
    # Check socket.gethostname() is displayed in the footer for load balancer verification
    current_hostname = socket.gethostname()
    assert current_hostname in html

def test_day_leave_submission_valid(client):
    """
    Test Day Leave application with valid return time before 9:00 PM (21:00).
    """
    payload = {
        "student_name": "Test Student Alpha",
        "roll_number": "21BCE9999",
        "hostel_block": "Block A (Aryabhatta)",
        "room_number": "A-101",
        "contact_number": "+91-9999888877",
        "parent_contact": "+91-9999888800",
        "leave_type": "Day Leave",
        "start_date": "2026-11-25",
        "out_time": "14:00",
        "expected_return_date": "2026-11-25",
        "expected_return_time": "20:30",
        "destination": "Campus Stationery Mart",
        "reason": "Purchasing engineering drawing materials"
    }
    response = client.post("/leave/apply", data=payload, follow_redirects=True)
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "submitted successfully" in html
    assert "21BCE9999" in html

def test_day_leave_curfew_enforcement(client):
    """
    Test that Day Leave rejects return times exceeding 9:00 PM (21:00).
    """
    payload = {
        "student_name": "Late Student",
        "roll_number": "21BCE0001",
        "hostel_block": "Block B (Vidyasagar)",
        "room_number": "B-201",
        "contact_number": "+91-9999111122",
        "parent_contact": "+91-9999111100",
        "leave_type": "Day Leave",
        "start_date": "2026-11-25",
        "out_time": "18:00",
        "expected_return_date": "2026-11-25",
        "expected_return_time": "22:30", # Exceeds 21:00 curfew!
        "destination": "City Mall Cinema",
        "reason": "Late movie show"
    }
    response = client.post("/leave/apply", data=payload, follow_redirects=True)
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Day Leave curfew restriction: Return time cannot exceed 9:00 PM" in html

def test_night_leave_submission(client):
    """
    Test Night Leave application with destination and multi-day window.
    """
    payload = {
        "student_name": "Night Outstation Student",
        "roll_number": "21BME8888",
        "hostel_block": "Block C (Gargi)",
        "room_number": "C-305",
        "contact_number": "+91-9876112233",
        "parent_contact": "+91-9876112200",
        "leave_type": "Night Leave",
        "start_date": "2026-11-26",
        "out_time": "09:00",
        "expected_return_date": "2026-11-29",
        "expected_return_time": "18:00",
        "destination": "Home - Pune, Maharashtra",
        "reason": "Sister marriage celebrations"
    }
    response = client.post("/leave/apply", data=payload, follow_redirects=True)
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "submitted successfully" in html
    assert "Night Leave" in html

def test_maintenance_ticket_submission(client):
    """
    Test Room Maintenance Ticket creation (Electrical / Plumbing / Wi-Fi).
    """
    payload = {
        "student_name": "Defect Reporter",
        "roll_number": "22ECE1122",
        "hostel_block": "Block D (Ramanujan)",
        "room_number": "D-410",
        "category": "Wi-Fi",
        "urgency": "High",
        "description": "Ethernet wall socket broken and LAN cable loose."
    }
    response = client.post("/maintenance/submit", data=payload, follow_redirects=True)
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Room Maintenance Ticket" in html
    assert "Wi-Fi" in html

def test_warden_authentication_and_dashboard(client):
    """
    Test Warden dashboard password protection and successful authentication.
    """
    # 1. Unauthenticated access redirects to login card
    resp_unauth = client.get("/warden")
    assert resp_unauth.status_code == 200
    assert "Warden Administration Portal" in resp_unauth.data.decode("utf-8")
    assert "Master Warden Authorization Key" in resp_unauth.data.decode("utf-8")

    # 2. Login with incorrect password fails
    resp_bad_login = client.post("/warden/login", data={"password": "wrong_password"}, follow_redirects=True)
    assert "Invalid Warden Master Password" in resp_bad_login.data.decode("utf-8")

    # 3. Login with correct password succeeds
    resp_good_login = client.post("/warden/login", data={"password": "test_warden_pass_123"}, follow_redirects=True)
    assert resp_good_login.status_code == 200
    dashboard_html = resp_good_login.data.decode("utf-8")
    assert "Warden Operations & Authorization Control" in dashboard_html
    assert "Warden Session Active" in dashboard_html

def test_warden_leave_actions(client):
    """
    Test Warden approving and rejecting student leave applications.
    """
    # First authenticate warden
    client.post("/warden/login", data={"password": "test_warden_pass_123"})

    # Fetch a pending leave
    leave = db_session.query(Leave).filter(Leave.status == "Pending").first()
    assert leave is not None

    # Approve leave
    resp_approve = client.post(
        f"/warden/leave/{leave.id}/action",
        data={"action": "Approved", "remarks": "Approved with verified parent SMS."},
        follow_redirects=True
    )
    assert resp_approve.status_code == 200
    assert "marked as Approved" in resp_approve.data.decode("utf-8")

    # Verify DB state
    updated_leave = db_session.get(Leave, leave.id)
    assert updated_leave.status == "Approved"
    assert "verified parent SMS" in updated_leave.warden_remarks

def test_warden_ticket_status_update(client):
    """
    Test Warden marking maintenance ticket as Resolved.
    """
    # First authenticate warden
    client.post("/warden/login", data={"password": "test_warden_pass_123"})

    # Fetch ticket
    ticket = db_session.query(MaintenanceTicket).first()
    assert ticket is not None

    resp_ticket = client.post(
        f"/warden/ticket/{ticket.id}/action",
        data={"status": "Resolved", "notes": "Technician replaced faulty component."},
        follow_redirects=True
    )
    assert resp_ticket.status_code == 200
    html = resp_ticket.data.decode("utf-8")
    assert "updated to" in html and "Resolved" in html

    updated_ticket = db_session.get(MaintenanceTicket, ticket.id)
    assert updated_ticket.status == "Resolved"
    assert updated_ticket.resolved_at is not None
