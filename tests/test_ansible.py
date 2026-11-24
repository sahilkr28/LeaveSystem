import re
import yaml
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ANSIBLE_DIR = BASE_DIR / "ansible"

def test_ansible_files_exist():
    """Verify all required Ansible files, roles, and playbooks exist."""
    required_files = [
        "ansible.cfg",
        "inventory.ini",
        "group_vars/all.yml",
        "site.yml",
        "rolling-update.yml",
        "playbooks/site.yml",
        "playbooks/rolling-update.yml",
        "roles/common/tasks/main.yml",
        "roles/common/handlers/main.yml",
        "roles/common/defaults/main.yml",
        "roles/common/templates/nrpe.cfg.j2",
        "roles/database/tasks/main.yml",
        "roles/database/handlers/main.yml",
        "roles/database/defaults/main.yml",
        "roles/webserver/tasks/main.yml",
        "roles/webserver/handlers/main.yml",
        "roles/webserver/defaults/main.yml",
        "roles/webserver/templates/hostel-app.service.j2",
        "roles/loadbalancer/tasks/main.yml",
        "roles/loadbalancer/handlers/main.yml",
        "roles/loadbalancer/defaults/main.yml",
        "roles/loadbalancer/templates/haproxy.cfg.j2",
        "roles/monitoring/tasks/main.yml",
        "roles/monitoring/handlers/main.yml",
        "roles/monitoring/defaults/main.yml",
        "roles/monitoring/templates/commands.cfg.j2",
        "roles/monitoring/templates/smart_hostel_cluster.cfg.j2",
        "roles/monitoring/templates/restart_web.sh.j2",
        "playbooks/heal-web.yml",
        "heal-web.yml",
        "README.md"
    ]
    for rel_path in required_files:
        p = ANSIBLE_DIR / rel_path
        assert p.exists(), f"Missing required Ansible file: {rel_path}"

def test_yaml_syntax_validity():
    """Verify all Ansible YAML files are syntactically valid YAML."""
    yaml_files = list(ANSIBLE_DIR.glob("**/*.yml")) + list(ANSIBLE_DIR.glob("**/*.yaml"))
    assert len(yaml_files) >= 12, "Expected at least 12 YAML files in ansible directory"

    for yml in yaml_files:
        content = yml.read_text(encoding="utf-8")
        try:
            parsed = yaml.safe_load(content)
            assert parsed is not None or yml.name.endswith(".yml"), f"Failed parsing {yml}"
        except Exception as e:
            assert False, f"Syntax error in YAML file {yml}: {e}"

def test_common_role():
    """Verify roles/common updates apt cache, configures UFW, and installs nagios-nrpe."""
    tasks_content = (ANSIBLE_DIR / "roles/common/tasks/main.yml").read_text(encoding="utf-8")
    assert "apt:" in tasks_content or "ansible.builtin.apt:" in tasks_content
    assert "update_cache: yes" in tasks_content or "update_cache: true" in tasks_content
    assert "ufw" in tasks_content
    assert "nagios-nrpe-server" in tasks_content
    assert "nagios-plugins" in tasks_content
    assert "port: '22'" in tasks_content or "port: 22" in tasks_content
    assert "port: '5666'" in tasks_content or "port: 5666" in tasks_content

def test_database_role():
    """Verify roles/database installs postgresql, configures pg_hba.conf, and creates hostel_db."""
    tasks_content = (ANSIBLE_DIR / "roles/database/tasks/main.yml").read_text(encoding="utf-8")
    assert "postgresql" in tasks_content
    assert "postgresql.conf" in tasks_content
    assert "listen_addresses" in tasks_content
    assert "pg_hba.conf" in tasks_content
    assert "postgresql_user:" in tasks_content
    assert "postgresql_db:" in tasks_content
    assert "db_user" in tasks_content
    assert "db_name" in tasks_content

def test_webserver_role():
    """
    Verify roles/webserver:
    - Copies ../app/ to /opt/hostel-app
    - Sets up Python venv
    - Installs requirements.txt
    - Configures hostel-app.service running Gunicorn on port 5000 pointing DATABASE_URL to db-01 private IP
    - Enables and starts service
    """
    tasks_content = (ANSIBLE_DIR / "roles/webserver/tasks/main.yml").read_text(encoding="utf-8")
    service_template = (ANSIBLE_DIR / "roles/webserver/templates/hostel-app.service.j2").read_text(encoding="utf-8")

    assert "/opt/hostel-app" in tasks_content
    assert "copy:" in tasks_content or "ansible.builtin.copy:" in tasks_content
    assert "../app/" in tasks_content
    assert "venv" in tasks_content
    assert "requirements.txt" in tasks_content
    assert "hostel-app.service" in tasks_content
    assert "gunicorn" in service_template
    assert "0.0.0.0:{{ app_port }}" in service_template or "5000" in service_template
    assert "DATABASE_URL=postgresql://" in service_template
    assert "db_host" in service_template

def test_loadbalancer_role():
    """
    Verify roles/loadbalancer:
    - Installs HAProxy
    - Deploys haproxy.cfg.j2
    - Load balances port 80 across web-01:5000 and web-02:5000
    - HTTP health check on /health
    - Enables HAProxy Stats on port 8404 (/stats)
    """
    tasks_content = (ANSIBLE_DIR / "roles/loadbalancer/tasks/main.yml").read_text(encoding="utf-8")
    cfg_template = (ANSIBLE_DIR / "roles/loadbalancer/templates/haproxy.cfg.j2").read_text(encoding="utf-8")

    assert "haproxy" in tasks_content
    assert "haproxy.cfg.j2" in tasks_content
    assert "haproxy_port" in tasks_content or "80" in tasks_content
    assert "8404" in tasks_content

    # Check HAProxy configuration contents
    assert "frontend http-in" in cfg_template
    assert "bind *:{{ haproxy_port }}" in cfg_template
    assert "backend flask-backend" in cfg_template
    assert "option httpchk GET /health" in cfg_template
    assert "http-check expect status 200" in cfg_template
    assert "groups['webservers']" in cfg_template
    assert "listen stats" in cfg_template
    assert "bind *:{{ haproxy_stats_port }}" in cfg_template
    assert "stats uri {{ haproxy_stats_uri }}" in cfg_template

def test_playbooks():
    """
    Verify:
    - playbooks/site.yml runs full deployment across all roles
    - playbooks/rolling-update.yml uses serial: 1 on webservers with zero downtime
    """
    site_playbook = (ANSIBLE_DIR / "playbooks/site.yml").read_text(encoding="utf-8")
    rolling_playbook = (ANSIBLE_DIR / "playbooks/rolling-update.yml").read_text(encoding="utf-8")

    # site.yml role executions
    assert "role: common" in site_playbook
    assert "role: database" in site_playbook
    assert "role: webserver" in site_playbook
    assert "role: loadbalancer" in site_playbook
    assert "role: monitoring" in site_playbook

    # rolling-update.yml configuration
    assert "serial: 1" in rolling_playbook
    assert "hosts: webservers" in rolling_playbook
    assert "hostel-app" in rolling_playbook
    assert "/health" in rolling_playbook


def test_monitoring_role_and_nagios_services():
    """
    Verify roles/monitoring:
    - Installs Nagios Core, Apache2, PHP
    - Configures Nagios host & service definitions:
      * HTTP 200 OK on lb-01
      * hostel-app port 5000 and /health on web-01 & web-02
      * PostgreSQL port 5432 on db-01
      * CPU Load and Disk Usage via NRPE across all nodes
    - Configures event_handler script (/usr/local/nagios/libexec/eventhandlers/restart_web.sh)
    """
    tasks_content = (ANSIBLE_DIR / "roles/monitoring/tasks/main.yml").read_text(encoding="utf-8")
    cluster_cfg = (ANSIBLE_DIR / "roles/monitoring/templates/smart_hostel_cluster.cfg.j2").read_text(encoding="utf-8")
    commands_cfg = (ANSIBLE_DIR / "roles/monitoring/templates/commands.cfg.j2").read_text(encoding="utf-8")
    restart_script = (ANSIBLE_DIR / "roles/monitoring/templates/restart_web.sh.j2").read_text(encoding="utf-8")

    # Package installation
    assert "nagios4" in tasks_content
    assert "apache2" in tasks_content
    assert "php" in tasks_content

    # Service definitions
    assert "lb-01" in cluster_cfg and "HTTP_Port_80_Status_200" in cluster_cfg
    assert "web-01" in cluster_cfg and "Hostel_App_Port_5000_Health" in cluster_cfg
    assert "web-02" in cluster_cfg
    assert "5000" in cluster_cfg and "/health" in cluster_cfg
    assert "db-01" in cluster_cfg and "5432" in cluster_cfg
    assert "CPU_Load_NRPE" in cluster_cfg
    assert "Disk_Usage_NRPE" in cluster_cfg
    assert "check_nrpe" in cluster_cfg

    # Event handler binding in Nagios
    assert "event_handler" in cluster_cfg and "restart_web_service" in cluster_cfg
    assert "restart_web_service" in commands_cfg
    assert "/usr/local/nagios/libexec/eventhandlers/restart_web.sh" in tasks_content or "restart_web.sh" in tasks_content

    # Event handler script logic
    assert "CRITICAL" in restart_script
    assert "HARD" in restart_script
    assert "ansible-playbook" in restart_script
    assert "/opt/infra/ansible/inventory.ini" in restart_script
    assert "/opt/infra/ansible/playbooks/heal-web.yml" in restart_script
    assert "--limit" in restart_script


def test_heal_web_playbook():
    """
    Verify playbooks/heal-web.yml:
    - Connects to the affected web server
    - Restarts hostel-app.service
    - Verifies http://localhost:5000/health returns 200
    - Logs recovery timestamp to /var/log/self-heal.log
    """
    heal_playbook = (ANSIBLE_DIR / "playbooks/heal-web.yml").read_text(encoding="utf-8")

    assert "hosts: webservers" in heal_playbook
    assert "hostel-app" in heal_playbook
    assert "restarted" in heal_playbook
    assert "http://127.0.0.1:{{ app_port }}/health" in heal_playbook or "5000/health" in heal_playbook
    assert "status_code: 200" in heal_playbook or "200" in heal_playbook
    assert "/var/log/self-heal.log" in heal_playbook

