import os
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TERRAFORM_DIR = BASE_DIR / "terraform"

def test_terraform_files_exist():
    """Verify all modular terraform files and templates exist."""
    required_files = [
        "main.tf",
        "variables.tf",
        "outputs.tf",
        "providers.tf",
        "terraform.tfvars.example",
        "templates/inventory.tpl",
        "README.md"
    ]
    for rel_path in required_files:
        file_path = TERRAFORM_DIR / rel_path
        assert file_path.exists(), f"Missing required file: {rel_path}"

def test_vpc_and_subnet_configuration():
    """Verify custom VPC 10.0.0.0/16 and public subnet with map_public_ip_on_launch."""
    main_tf = (TERRAFORM_DIR / "main.tf").read_text(encoding="utf-8")
    vars_tf = (TERRAFORM_DIR / "variables.tf").read_text(encoding="utf-8")

    assert 'resource "aws_vpc"' in main_tf
    assert 'resource "aws_internet_gateway"' in main_tf
    assert 'resource "aws_subnet"' in main_tf
    assert 'map_public_ip_on_launch = true' in main_tf
    assert '10.0.0.0/16' in vars_tf or '10.0.0.0/16' in main_tf
    assert 'resource "aws_route_table"' in main_tf
    assert 'resource "aws_route_table_association"' in main_tf

def test_security_groups_ports():
    """
    Verify security groups allow:
    - SSH (22)
    - HTTP (80)
    - Flask (5000)
    - PostgreSQL (5432 restricted to VPC CIDR)
    - HAProxy Stats (8404)
    - Nagios NRPE (5666)
    """
    main_tf = (TERRAFORM_DIR / "main.tf").read_text(encoding="utf-8")

    # Port 22 (SSH)
    assert 'from_port   = 22' in main_tf and 'to_port     = 22' in main_tf
    # Port 80 (HTTP)
    assert 'from_port   = 80' in main_tf and 'to_port     = 80' in main_tf
    # Port 5000 (Flask)
    assert 'from_port   = 5000' in main_tf and 'to_port     = 5000' in main_tf
    # Port 5432 (PostgreSQL restricted to VPC)
    assert 'from_port   = 5432' in main_tf and 'to_port     = 5432' in main_tf
    assert 'cidr_blocks = [var.vpc_cidr]' in main_tf
    # Port 8404 (HAProxy Stats)
    assert 'from_port   = 8404' in main_tf and 'to_port     = 8404' in main_tf
    # Port 5666 (Nagios NRPE)
    assert 'from_port   = 5666' in main_tf and 'to_port     = 5666' in main_tf

def test_ec2_instances_and_tags():
    """
    Verify 5 EC2 instances are defined with exact names:
    ops-node, lb-01, web-01, web-02, and db-01.
    """
    main_tf = (TERRAFORM_DIR / "main.tf").read_text(encoding="utf-8")
    vars_tf = (TERRAFORM_DIR / "variables.tf").read_text(encoding="utf-8")

    required_names = ["ops-node", "lb-01", "web-01", "web-02", "db-01"]
    for name in required_names:
        pattern = rf'Name\s*=\s*"{re.escape(name)}"'
        assert re.search(pattern, main_tf), f"Instance name tag '{name}' not found in main.tf"

    # Verify Ubuntu 24.04 and t3.micro
    assert 'data "aws_ami" "ubuntu_24_04"' in main_tf
    assert 'ubuntu-noble-24.04' in main_tf
    assert 't3.micro' in vars_tf or 't3.micro' in main_tf

def test_ansible_inventory_template_and_resource():
    """
    Verify template/inventory.tpl and local_file resource generates ../ansible/inventory.ini
    grouped into [ops], [loadbalancer], [webservers], and [database] with public & private IPs.
    """
    main_tf = (TERRAFORM_DIR / "main.tf").read_text(encoding="utf-8")
    tpl_file = (TERRAFORM_DIR / "templates" / "inventory.tpl").read_text(encoding="utf-8")

    assert 'resource "local_file" "ansible_inventory"' in main_tf
    assert '../ansible/inventory.ini' in main_tf
    assert 'templatefile(' in main_tf

    # Verify inventory template groups
    assert '[ops]' in tpl_file
    assert '[loadbalancer]' in tpl_file
    assert '[webservers]' in tpl_file
    assert '[database]' in tpl_file

    # Verify both public and private IP representations
    assert 'ansible_host=' in tpl_file
    assert 'private_ip=' in tpl_file

def test_outputs_file():
    """Verify all public IPs are clearly output in outputs.tf."""
    outputs_tf = (TERRAFORM_DIR / "outputs.tf").read_text(encoding="utf-8")

    expected_outputs = [
        "ops_node_public_ip",
        "lb_01_public_ip",
        "web_01_public_ip",
        "web_02_public_ip",
        "db_01_public_ip",
        "all_public_ips",
        "all_private_ips"
    ]
    for out in expected_outputs:
        assert f'output "{out}"' in outputs_tf, f"Output '{out}' missing from outputs.tf"
