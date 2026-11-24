# Smart Campus Hostel DevOps - AWS Terraform Infrastructure

This directory contains modular Terraform configuration to provision a production-grade 5-node Linux infrastructure on AWS for the Smart Campus Hostel & Leave Management project.

---

## 🏛️ Infrastructure Architecture

```
AWS VPC (10.0.0.0/16) - us-east-1
│
├── Internet Gateway (smart-hostel-igw)
├── Public Subnet (10.0.1.0/24 in us-east-1a)
│
├── EC2 Node 1: ops-node   (Ubuntu 24.04 LTS, t3.micro) - Nagios NRPE / Ansible Control / CI-CD
├── EC2 Node 2: lb-01      (Ubuntu 24.04 LTS, t3.micro) - HAProxy Load Balancer (HTTP 80, Stats 8404)
├── EC2 Node 3: web-01     (Ubuntu 24.04 LTS, t3.micro) - Flask Web Application Node 1 (Port 5000)
├── EC2 Node 4: web-02     (Ubuntu 24.04 LTS, t3.micro) - Flask Web Application Node 2 (Port 5000)
└── EC2 Node 5: db-01      (Ubuntu 24.04 LTS, t3.micro) - PostgreSQL Database (Port 5432 - VPC Only)
```

---

## 🔒 Security Group Segregation

| Security Group | Port(s) | Protocol | Source CIDR | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `smart-hostel-common-sg` | `22` | TCP | `var.allowed_ssh_cidr` (`0.0.0.0/0`) | SSH administrative management |
| `smart-hostel-common-sg` | `5666` | TCP | `10.0.0.0/16` (VPC CIDR) | Nagios NRPE monitoring daemon |
| `smart-hostel-lb-sg` | `80` | TCP | `0.0.0.0/0` | Public HTTP web ingress |
| `smart-hostel-lb-sg` | `8404` | TCP | `0.0.0.0/0` | HAProxy health & statistics dashboard |
| `smart-hostel-web-sg` | `5000` | TCP | `0.0.0.0/0` (or VPC) | Flask Gunicorn service |
| `smart-hostel-db-sg` | `5432` | TCP | **`10.0.0.0/16` (Strictly VPC only)** | PostgreSQL relational database |
| `smart-hostel-ops-sg` | `5666` | TCP | `10.0.0.0/16` | Nagios server inbound monitoring |

---

## 📁 Modular File Layout

- **`providers.tf`**: AWS provider (~> 5.0) and Local provider (~> 2.4) configuration with default tags.
- **`variables.tf`**: Configurable parameters (region, VPC/subnet CIDRs, instance type, key pair name).
- **`main.tf`**:
  - AMI query for Ubuntu 24.04 LTS (`Canonical 099720109477`).
  - VPC, Subnet, Internet Gateway, and Route Table.
  - Security Groups with precise ingress/egress rules.
  - 5 EC2 instances tagged with `Name` and `Role`.
  - `local_file` resource generating `../ansible/inventory.ini`.
- **`templates/inventory.tpl`**: Ansible inventory template mapping public and private IPs into `[ops]`, `[loadbalancer]`, `[webservers]`, and `[database]`.
- **`outputs.tf`**: Clear outputs for all public IPs, private IPs, service URLs, and SSH commands.
- **`terraform.tfvars.example`**: Example variable overrides.

---

## ⚡ Deployment Instructions

### 1. Prerequisites
- [Terraform](https://developer.hashicorp.com/terraform/downloads) >= 1.5.0
- Configured AWS CLI credentials (`aws configure`) with permissions for EC2 and VPC

### 2. Initialization
```bash
cd terraform
terraform init
```

### 3. Review Plan
```bash
terraform plan
```

### 4. Provision Infrastructure
```bash
terraform apply -auto-approve
```

### 5. Automated Ansible Inventory Output
Upon completion, Terraform automatically writes `../ansible/inventory.ini`:
```ini
[ops]
ops-node ansible_host=54.x.x.x private_ip=10.0.1.x ansible_user=ubuntu node_role=operations

[loadbalancer]
lb-01 ansible_host=34.x.x.x private_ip=10.0.1.x ansible_user=ubuntu node_role=loadbalancer

[webservers]
web-01 ansible_host=44.x.x.x private_ip=10.0.1.x ansible_user=ubuntu node_role=webserver node_id=1
web-02 ansible_host=18.x.x.x private_ip=10.0.1.x ansible_user=ubuntu node_role=webserver node_id=2

[database]
db-01 ansible_host=52.x.x.x private_ip=10.0.1.x ansible_user=ubuntu node_role=database
```

### 6. Clean Up (Teardown)
```bash
terraform destroy -auto-approve
```
