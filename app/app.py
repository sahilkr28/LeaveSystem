import os
import socket
from pathlib import Path
from datetime import datetime, date, timezone
from flask import (
    Flask, render_template, request, redirect, url_for, 
    flash, session, jsonify, abort, current_app
)
try:
    from .config import Config
    from .database import engine, db_session, init_db, check_db_connection
    from .models import Leave, MaintenanceTicket
except (ImportError, ValueError):
    from config import Config
    from database import engine, db_session, init_db, check_db_connection
    from models import Leave, MaintenanceTicket

def create_app(test_config=None):
    """Application Factory Pattern for Smart Campus Hostel ERP"""
    base_dir = Path(__file__).resolve().parent
    templates_dir = base_dir / "templates"
    static_dir = base_dir / "static"

    app = Flask(
        __name__, 
        template_folder=str(templates_dir), 
        static_folder=str(static_dir)
    )
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    # Initialize Database Schema & Seed Data safely
    with app.app_context():
        try:
            init_db(seed=True)
        except Exception as e:
            print(f"[STARTUP DB INIT NOTICE] {e}")

    # Cleanup Database Session on Request Teardown
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    # Context Processor for Global ERP Telemetry & Footer Metadata
    @app.context_processor
    def inject_telemetry():
        db_type = "PostgreSQL" if "postgresql" in Config.SQLALCHEMY_DATABASE_URI else "SQLite (Local Dev Engine)"
        return {
            "server_hostname": socket.gethostname(),
            "db_engine_name": db_type,
            "app_version": Config.PORTAL_VERSION,
            "app_name": Config.APP_NAME,
            "campus_name": Config.CAMPUS_NAME,
            "system_now": datetime.now().strftime("%d-%b-%Y %H:%M:%S")
        }

    # ==========================================
    # 1. Health & Node Telemetry Endpoint
    # ==========================================
    @app.route("/health", methods=["GET"])
    def health_check():
        """
        Telemetry Endpoint: returns live backend status, host socket node,
        and database connectivity status.
        """
        is_db_connected = check_db_connection()
        hostname = socket.gethostname()

        if is_db_connected:
            return jsonify({
                "status": "healthy",
                "host": hostname,
                "db": "connected"
            }), 200
        else:
            return jsonify({
                "status": "unhealthy",
                "host": hostname,
                "db": "disconnected"
            }), 503

    # ==========================================
    # 2. Student Portal & Live ERP Tables (/)
    # ==========================================
    @app.route("/", methods=["GET"])
    def student_portal():
        """
        Student View: Form to apply for Day/Night Leave, submit Maintenance Ticket,
        and view live tables of submitted requests directly from PostgreSQL/SQLite.
        """
        today_str = date.today().isoformat()
        
        # Fetch live records from database with auto-initialization for serverless cold starts
        try:
            leaves = db_session.query(Leave).order_by(Leave.created_at.desc()).all()
            tickets = db_session.query(MaintenanceTicket).order_by(MaintenanceTicket.created_at.desc()).all()
        except Exception:
            db_session.rollback()
            try:
                init_db(seed=True)
                leaves = db_session.query(Leave).order_by(Leave.created_at.desc()).all()
                tickets = db_session.query(MaintenanceTicket).order_by(MaintenanceTicket.created_at.desc()).all()
            except Exception:
                leaves = []
                tickets = []

        # Compute Dashboard Metrics
        total_leaves = len(leaves)
        pending_leaves = sum(1 for l in leaves if l.status == "Pending")
        approved_leaves = sum(1 for l in leaves if l.status == "Approved")
        
        total_tickets = len(tickets)
        pending_tickets = sum(1 for t in tickets if t.status == "Pending")
        resolved_tickets = sum(1 for t in tickets if t.status == "Resolved")

        return render_template(
            "student.html",
            leaves=leaves,
            tickets=tickets,
            today_str=today_str,
            stats={
                "total_leaves": total_leaves,
                "pending_leaves": pending_leaves,
                "approved_leaves": approved_leaves,
                "total_tickets": total_tickets,
                "pending_tickets": pending_tickets,
                "resolved_tickets": resolved_tickets
            }
        )

    # ------------------------------------------
    # Student Form Submissions
    # ------------------------------------------
    @app.route("/leave/apply", methods=["POST"])
    def apply_leave():
        """Submit a new Day or Night Leave Request."""
        try:
            student_name = request.form.get("student_name", "").strip()
            roll_number = request.form.get("roll_number", "").strip().upper()
            hostel_block = request.form.get("hostel_block", "").strip()
            room_number = request.form.get("room_number", "").strip()
            contact_number = request.form.get("contact_number", "").strip()
            parent_contact = request.form.get("parent_contact", "").strip()
            leave_type = request.form.get("leave_type", "Day Leave").strip()
            start_date = request.form.get("start_date", "").strip()
            out_time = request.form.get("out_time", "").strip()
            expected_return_date = request.form.get("expected_return_date", "").strip()
            expected_return_time = request.form.get("expected_return_time", "").strip()
            destination = request.form.get("destination", "").strip()
            reason = request.form.get("reason", "").strip()

            # Validation
            if not all([student_name, roll_number, hostel_block, room_number, 
                        contact_number, parent_contact, start_date, out_time, 
                        expected_return_date, expected_return_time, reason]):
                flash("All mandatory fields must be completed.", "danger")
                return redirect(url_for("student_portal"))

            # Enforce Day Leave Curfew Rule: Up to 9:00 PM (21:00) on the same date
            if leave_type == "Day Leave":
                expected_return_date = start_date  # Same day return
                # Parse return time hour
                try:
                    ret_h, ret_m = map(int, expected_return_time.split(":"))
                    if ret_h > 21 or (ret_h == 21 and ret_m > 0):
                        flash("Day Leave curfew restriction: Return time cannot exceed 9:00 PM (21:00). For night outings, apply for Night Leave.", "warning")
                        return redirect(url_for("student_portal"))
                except ValueError:
                    flash("Invalid return time format entered.", "danger")
                    return redirect(url_for("student_portal"))
                
                if not destination:
                    destination = "Local Outing / Campus Vicinity"

            elif leave_type == "Night Leave":
                if not destination:
                    flash("Destination address is strictly required for Night Leave.", "warning")
                    return redirect(url_for("student_portal"))
                
                if expected_return_date < start_date:
                    flash("Night Leave return date cannot be before departure date.", "warning")
                    return redirect(url_for("student_portal"))

            new_leave = Leave(
                student_name=student_name,
                roll_number=roll_number,
                hostel_block=hostel_block,
                room_number=room_number,
                contact_number=contact_number,
                parent_contact=parent_contact,
                leave_type=leave_type,
                start_date=start_date,
                out_time=out_time,
                expected_return_date=expected_return_date,
                expected_return_time=expected_return_time,
                destination=destination,
                reason=reason,
                status="Pending"
            )
            db_session.add(new_leave)
            db_session.commit()

            flash(f"Leave Application #{new_leave.id} ({leave_type}) submitted successfully. Awaiting Warden approval.", "success")
        except Exception as e:
            db_session.rollback()
            flash(f"Error submitting leave request: {str(e)}", "danger")

        return redirect(url_for("student_portal"))

    @app.route("/maintenance/submit", methods=["POST"])
    def submit_maintenance():
        """Submit a new Room Maintenance Ticket (Electrical, Plumbing, Wi-Fi, etc.)."""
        try:
            student_name = request.form.get("student_name", "").strip()
            roll_number = request.form.get("roll_number", "").strip().upper()
            hostel_block = request.form.get("hostel_block", "").strip()
            room_number = request.form.get("room_number", "").strip()
            category = request.form.get("category", "").strip()
            urgency = request.form.get("urgency", "Medium").strip()
            description = request.form.get("description", "").strip()

            if not all([student_name, roll_number, hostel_block, room_number, category, description]):
                flash("Please fill in all required maintenance ticket details.", "danger")
                return redirect(url_for("student_portal"))

            new_ticket = MaintenanceTicket(
                student_name=student_name,
                roll_number=roll_number,
                hostel_block=hostel_block,
                room_number=room_number,
                category=category,
                urgency=urgency,
                description=description,
                status="Pending"
            )
            db_session.add(new_ticket)
            db_session.commit()

            flash(f"Room Maintenance Ticket #{new_ticket.id} ({category}) logged with Campus Works Dept.", "success")
        except Exception as e:
            db_session.rollback()
            flash(f"Error submitting maintenance ticket: {str(e)}", "danger")

        return redirect(url_for("student_portal"))

    # ==========================================
    # 3. Warden Dashboard & Administration (/warden)
    # ==========================================
    @app.route("/warden", methods=["GET"])
    def warden_dashboard():
        """
        Warden Dashboard: Password-protected administration portal
        to review, approve/reject leaves and resolve maintenance tickets.
        """
        # Enforce Warden Password Authentication
        if not session.get("warden_authenticated"):
            return render_template("warden_login.html")

        # Filters
        leave_filter = request.args.get("leave_filter", "all")
        ticket_filter = request.args.get("ticket_filter", "all")

        # Query Leaves
        leave_query = db_session.query(Leave).order_by(Leave.created_at.desc())
        if leave_filter == "pending":
            leave_query = leave_query.filter(Leave.status == "Pending")
        elif leave_filter == "approved":
            leave_query = leave_query.filter(Leave.status == "Approved")
        elif leave_filter == "rejected":
            leave_query = leave_query.filter(Leave.status == "Rejected")
        leaves = leave_query.all()

        # Query Maintenance Tickets
        ticket_query = db_session.query(MaintenanceTicket).order_by(MaintenanceTicket.created_at.desc())
        if ticket_filter == "pending":
            ticket_query = ticket_query.filter(MaintenanceTicket.status == "Pending")
        elif ticket_filter == "in_progress":
            ticket_query = ticket_query.filter(MaintenanceTicket.status == "In Progress")
        elif ticket_filter == "resolved":
            ticket_query = ticket_query.filter(MaintenanceTicket.status == "Resolved")
        tickets = ticket_query.all()

        # Aggregate Statistics
        all_leaves = db_session.query(Leave).all()
        all_tickets = db_session.query(MaintenanceTicket).all()

        stats = {
            "pending_leaves": sum(1 for l in all_leaves if l.status == "Pending"),
            "approved_leaves": sum(1 for l in all_leaves if l.status == "Approved"),
            "rejected_leaves": sum(1 for l in all_leaves if l.status == "Rejected"),
            "total_leaves": len(all_leaves),
            "pending_tickets": sum(1 for t in all_tickets if t.status == "Pending"),
            "in_progress_tickets": sum(1 for t in all_tickets if t.status == "In Progress"),
            "resolved_tickets": sum(1 for t in all_tickets if t.status == "Resolved"),
            "total_tickets": len(all_tickets)
        }

        return render_template(
            "warden.html",
            leaves=leaves,
            tickets=tickets,
            stats=stats,
            current_leave_filter=leave_filter,
            current_ticket_filter=ticket_filter
        )

    @app.route("/warden/login", methods=["POST"])
    def warden_login():
        """Authenticate warden using WARDEN_PASSWORD environment variable or config."""
        entered_password = request.form.get("password", "").strip()
        expected_password = current_app.config.get("WARDEN_PASSWORD", Config.WARDEN_PASSWORD)

        if entered_password == expected_password:
            session["warden_authenticated"] = True
            flash("Welcome, Warden Administrator. Access granted.", "success")
        else:
            flash("Invalid Warden Master Password. Access Denied.", "danger")

        return redirect(url_for("warden_dashboard"))

    @app.route("/warden/logout", methods=["GET", "POST"])
    def warden_logout():
        """Terminate warden authenticated session."""
        session.pop("warden_authenticated", None)
        flash("You have been signed out of the Warden Administration Portal.", "info")
        return redirect(url_for("warden_dashboard"))

    @app.route("/warden/leave/<int:leave_id>/action", methods=["POST"])
    def warden_leave_action(leave_id):
        """Approve or Reject a student leave application."""
        if not session.get("warden_authenticated"):
            flash("Session expired. Please sign in again.", "warning")
            return redirect(url_for("warden_dashboard"))

        action = request.form.get("action", "").strip()
        remarks = request.form.get("remarks", "").strip()

        leave = db_session.get(Leave, leave_id)
        if not leave:
            flash(f"Leave record #{leave_id} not found.", "danger")
            return redirect(url_for("warden_dashboard"))

        if action in ["Approved", "Rejected"]:
            leave.status = action
            if remarks:
                leave.warden_remarks = remarks
            elif action == "Approved" and not leave.warden_remarks:
                leave.warden_remarks = "Approved by Hostel Warden."
            elif action == "Rejected" and not leave.warden_remarks:
                leave.warden_remarks = "Declined as per campus hostel regulations."
            
            leave.updated_at = datetime.now(timezone.utc)
            db_session.commit()
            flash(f"Leave application #{leave.id} ({leave.student_name}) marked as {action}.", "success" if action == "Approved" else "warning")
        else:
            flash("Unrecognized warden leave action.", "danger")

        return redirect(url_for("warden_dashboard"))

    @app.route("/warden/ticket/<int:ticket_id>/action", methods=["POST"])
    def warden_ticket_action(ticket_id):
        """Update Maintenance Ticket status (In Progress, Resolved, Pending)."""
        if not session.get("warden_authenticated"):
            flash("Session expired. Please sign in again.", "warning")
            return redirect(url_for("warden_dashboard"))

        new_status = request.form.get("status", "").strip()
        notes = request.form.get("notes", "").strip()

        ticket = db_session.get(MaintenanceTicket, ticket_id)
        if not ticket:
            flash(f"Maintenance ticket #{ticket_id} not found.", "danger")
            return redirect(url_for("warden_dashboard"))

        if new_status in ["Pending", "In Progress", "Resolved"]:
            ticket.status = new_status
            if notes:
                ticket.warden_notes = notes
            
            if new_status == "Resolved":
                ticket.resolved_at = datetime.now(timezone.utc)
                if not ticket.warden_notes:
                    ticket.warden_notes = "Issue inspected, serviced, and marked resolved by maintenance supervisor."
            
            db_session.commit()
            flash(f"Ticket #{ticket.id} ({ticket.category} - Room {ticket.room_number}) updated to '{new_status}'.", "success")
        else:
            flash("Invalid ticket status requested.", "danger")

        return redirect(url_for("warden_dashboard"))

    return app

# Instantiate Default App for Gunicorn / WSGI
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
