# Smart Campus Hostel & Leave Management System (DevOps 7th Sem)

A complete, production-grade DevOps project implementing an enterprise multi-tier web application with Infrastructure as Code (**Terraform**), Configuration Management (**Ansible**), High Availability Load Balancing (**HAProxy**), Relational Clustering (**PostgreSQL**), and Closed-Loop Automated Self-Healing (**Nagios Core + Ansible Event Handlers**).

---

## 🏛️ System Architecture

```
                                  [ Internet / Students & Wardens ]
                                                  │
                                                  ▼
                        ┌──────────────────────────────────────────────────┐
                        │              AWS VPC (10.0.0.0/16)               │
                        │             Public Subnet: 10.0.1.0/24           │
                        └─────────────────────────┬────────────────────────┘
                                                  │
                                                  ▼
                                      ┌───────────────────────┐
                                      │   HAProxy Load Balancer│
                                      │         [lb-01]       │
                                      │   Port 80 (HTTP In)   │
                                      │   Port 8404 (Stats UI)│
                                      └───────────┬───────────┘
                                                  │
                                 Roundrobin Health-Checked (Port 5000)
                                                  │
                         ┌────────────────────────┴────────────────────────┐
                         ▼                                                 ▼
             ┌───────────────────────┐                         ┌───────────────────────┐
             │       [web-01]        │                         │       [web-02]        │
             │ Flask Gunicorn App    │                         │ Flask Gunicorn App    │
             │ Port 5000 (/health)   │                         │ Port 5000 (/health)   │
             └───────────┬───────────┘                         └───────────┬───────────┘
                         │                                                 │
                         └────────────────────────┬────────────────────────┘
                                                  │
                                   PostgreSQL 5432 (VPC Subnet Only)
                                                  │
                                                  ▼
                                      ┌───────────────────────┐
                                      │       [db-01]         │
                                      │ PostgreSQL 16 Server  │
                                      │  Database: hostel_db  │
                                      │   User: hostel_user   │
                                      └───────────────────────┘

══════════════════════════════════════════════════════════════════════════════════════════════
                            OBSERVABILITY & AUTOMATED SELF-HEALING
══════════════════════════════════════════════════════════════════════════════════════════════
 ┌──────────────────────────────────────────────────────────────────────────────────────────┐
 │                                   Operations Node [ops-node]                             │
 │  ┌────────────────────────────────────────────────────────────────────────────────────┐  │
 │  │                                   Nagios Core 4                                    │  │
 │  │  Checks:                                                                           │  │
 │  │   • HTTP 200 on lb-01 (Port 80)                                                    │  │
 │  │   • Hostel App & /health on web-01 & web-02 (Port 5000)                             │  │
 │  │   • PostgreSQL on db-01 (Port 5432)                                                │  │
 │  │   • CPU Load & Disk Usage via NRPE on all nodes                                    │  │
 │  └─────────────────────────────────────────┬──────────────────────────────────────────┘  │
 │                                            │                                             │
 │                     When State == CRITICAL HARD (3/3 failures)                           │
 │                                            │                                             │
 │                                            ▼                                             │
 │                     ┌───────────────────────────────────────────────┐                    │
 │                     │  Nagios Event Handler: restart_web.sh         │                    │
 │                     │  Triggers: ansible-playbook heal-web.yml      │                    │
 │                     └──────────────────────┬────────────────────────┘                    │
 └────────────────────────────────────────────┼─────────────────────────────────────────────┘
                                              │
                       SSH: sudo systemctl restart hostel-app.service
                       Polls: http://127.0.0.1:5000/health == 200
                       Logs: /var/log/self-heal.log
                                              │
                                              ▼
                                 [web-01] or [web-02]
                                 (Self-Healed Automatically)
```

---

## 📋 Prerequisites

Before initiating deployment, verify your workstation has the following tools installed:

1. **AWS CLI** (configured with admin credentials):
   ```bash
   aws configure
   ```
2. **Terraform** >= 1.5.0:
   ```bash
   terraform version
   ```
3. **Ansible** >= 2.14 (or run via WSL / Linux / ops-node):
   ```bash
   ansible --version
   ```
4. **SSH Key Pair**:
   - Ensure you have an AWS EC2 Key Pair (default: `smart-hostel-key`), or set `create_key_pair = true` in Terraform with your public key.

---

## 🚀 Step-by-Step Deployment Workflow

### Step 1: Provision Cloud Infrastructure with Terraform

1. Navigate to the `terraform/` directory:
   ```bash
   cd terraform
   ```
2. Initialize Terraform providers and plugins:
   ```bash
   terraform init
   ```
3. Preview the infrastructure plan:
   ```bash
   terraform plan
   ```
4. Apply the configuration to provision the VPC, Subnet, Security Groups, and 5 EC2 instances:
   ```bash
   terraform apply -auto-approve
   ```
5. **Automated Inventory Generation**:
   Terraform automatically renders `templates/inventory.tpl` and outputs the live Ansible inventory directly to:
   ```
   ../ansible/inventory.ini
   ```
6. Check the deployed public IPs in the Terraform outputs:
   ```bash
   terraform output all_public_ips
   ```

---

### Step 2: Configure Nodes & Deploy Cluster with Ansible

1. Navigate to the `ansible/` directory:
   ```bash
   cd ../ansible
   ```
2. Verify SSH connectivity to all 5 nodes:
   ```bash
   ansible -i inventory.ini all -m ping
   ```
3. Execute the master deployment playbook (`playbooks/site.yml`):
   ```bash
   ansible-playbook -i inventory.ini playbooks/site.yml
   ```

#### What `playbooks/site.yml` Executes Across the Cluster:
- **Stage 1 (`roles/common`)**: Configures UFW firewall (allowing SSH `22`, Nagios NRPE `5666`) and starts the NRPE agent on `lb-01`, `web-01`, `web-02`, and `db-01`.
- **Stage 2 (`roles/database`)**: Installs PostgreSQL on `db-01`, enables VPC network access in `postgresql.conf` and `pg_hba.conf`, and initializes the `hostel_db` database and `hostel_user`.
- **Stage 3 (`roles/webserver`)**: Deploys the Python Flask application from `../app/` to `/opt/hostel-app` on `web-01` and `web-02`, sets up a Python virtual environment, installs dependencies, and enables the `hostel-app.service` Systemd unit running Gunicorn on port `5000`.
- **Stage 4 (`roles/loadbalancer`)**: Installs HAProxy on `lb-01`, configures roundrobin balancing over `web-01:5000` and `web-02:5000` with health checks on `/health`, and opens the Stats UI on port `8404`.
- **Stage 5 (`roles/monitoring`)**: Installs Nagios Core, Apache2, and PHP on `ops-node`, registers all service definitions, and deploys the `restart_web.sh` self-healing event handler.
- **Stage 6**: Executes an automated end-to-end verification probe against HAProxy on port `80`.

---

## 🌐 Web Interface Endpoints & Credentials

Once deployment completes, access the three management portals:

| Service | URL | Default Credentials | Description |
| :--- | :--- | :--- | :--- |
| **Hostel ERP Portal** | `http://<LB_PUBLIC_IP>/` | *Public Student Desk* | Student outing requests, gate passes (curfew 9:00 PM), and maintenance tickets. |
| **Warden Control Desk** | `http://<LB_PUBLIC_IP>/warden` | Master Password: `warden_production_secure_pass_2026` | Authorization dashboard for pending leave approval and maintenance dispatch. |
| **HAProxy Live Stats** | `http://<LB_PUBLIC_IP>:8404/stats` | **User:** `admin`<br>**Pass:** `admin_cluster_pass_2026` | Real-time traffic metrics, session rates, backend server health, and failover status. |
| **Nagios Core Dashboard**| `http://<OPS_NODE_PUBLIC_IP>/nagios4` | **User:** `nagiosadmin`<br>**Pass:** `nagiosadmin_cluster_pass_2026` | Central monitoring view displaying hosts, service state, NRPE metrics, and event handlers. |

> **Load Balancer Verification**: Every page of the Hostel ERP Portal displays the active backend server's `socket.gethostname()` in the footer. Refreshing the browser toggles between `web-01` and `web-02`, visually confirming roundrobin load balancing.

---

## 🔄 Zero-Downtime Rolling Update

To deploy updated application code without taking the service offline:

```bash
cd ansible
ansible-playbook -i inventory.ini playbooks/rolling-update.yml
```

- **Mechanism**: Configured with `serial: 1`. Updates `web-01`, restarts `hostel-app.service`, and waits until `/health` returns HTTP 200 before proceeding to `web-02`. HAProxy routes all traffic to the active healthy server during the update.

---

## 🔥 3-Step Live Chaos-Testing Demo (Self-Healing)

Demonstrate automated detection and closed-loop self-healing by simulating an unexpected service crash on `web-01`.

```
[Crash Simulated] ──> [Nagios Detects Failure] ──> [Event Handler Fires] ──> [Ansible Restores Service]
```

### Step 1: Inject Chaos (Stop Service on `web-01`)

1. SSH into `web-01`:
   ```bash
   ssh ubuntu@<WEB_01_PUBLIC_IP>
   ```
2. Stop the Flask Gunicorn application service:
   ```bash
   sudo systemctl stop hostel-app.service
   ```
3. Confirm the local service is down:
   ```bash
   curl -I http://localhost:5000/health
   # Expected: curl: (7) Failed to connect to localhost port 5000: Connection refused
   ```
4. Observe HAProxy: Refresh the application in your browser. HAProxy instantly detects the failure and seamlessly routes 100% of user traffic to `web-02` with **zero user downtime**.

---

### Step 2: Observe Nagios Detection & Event Handler Trigger

1. SSH into `ops-node`:
   ```bash
   ssh ubuntu@<OPS_NODE_PUBLIC_IP>
   ```
2. Monitor the Nagios event handler log in real-time:
   ```bash
   tail -f /var/log/nagios-eventhandler.log
   ```
3. **What happens under the hood**:
   - **Attempt 1 & 2 (`SOFT CRITICAL`)**: Nagios detects port 5000 /health is unreachable and increments the check counter.
   - **Attempt 3 (`HARD CRITICAL`)**: After reaching `max_check_attempts: 3`, Nagios locks into a `HARD CRITICAL` state and executes the registered event handler:
     ```bash
     /usr/local/nagios/libexec/eventhandlers/restart_web.sh CRITICAL HARD 3 web-01
     ```
   - The script logs the incident and immediately executes:
     ```bash
     sudo -n ansible-playbook -i /opt/infra/ansible/inventory.ini /opt/infra/ansible/playbooks/heal-web.yml --limit web-01
     ```

---

### Step 3: Verify Automated Recovery & Audit Logs

1. On `web-01`, inspect the self-healing audit log:
   ```bash
   cat /var/log/self-heal.log
   ```
   **Expected output**:
   ```text
   [2026-11-24 20:37:00] [HEAL-START] Self-healing initiated on web-01 due to Nagios CRITICAL alert.
   [2026-11-24 20:37:04] [HEAL-SUCCESS] Node web-01 successfully recovered: hostel-app active and /health returned HTTP 200 (Reported Host: web-01).
   ```
2. Verify the Systemd service status on `web-01`:
   ```bash
   sudo systemctl status hostel-app.service
   # Expected: Active: active (running)
   ```
3. Verify the `/health` endpoint responds with HTTP 200:
   ```bash
   curl -s http://localhost:5000/health
   # Expected: {"db":"connected","host":"web-01","status":"healthy"}
   ```
4. Check the HAProxy Stats dashboard at `http://<LB_PUBLIC_IP>:8404/stats`: `web-01` turns green (`UP`), and HAProxy resumes traffic distribution across both replicas.

---

## 🧪 Automated Test Suite

Run the unified test suite verifying application routes, Terraform infrastructure syntax, and Ansible playbooks:

```powershell
py -3 -m pytest tests/ -v
```

```
tests/test_ansible.py .........................  [PASSED]
tests/test_terraform.py .......................  [PASSED]
tests/test_app.py .............................  [PASSED]

============================= 24 passed in 2.46s =============================
```

---

## 🧹 Infrastructure Teardown

To destroy all cloud resources and prevent ongoing AWS charges:

```bash
cd terraform
terraform destroy -auto-approve
```
