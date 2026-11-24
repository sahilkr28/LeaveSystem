# ==============================================================================
# Smart Campus Hostel DevOps Infrastructure - Terraform Outputs
# ==============================================================================

# ------------------------------------------------------------------------------
# 1. Individual Public IP Outputs
# ------------------------------------------------------------------------------
output "ops_node_public_ip" {
  description = "Public IPv4 address of the ops-node (Nagios/Ansible/CI-CD)"
  value       = aws_instance.ops_node.public_ip
}

output "lb_01_public_ip" {
  description = "Public IPv4 address of the lb-01 (HAProxy Load Balancer)"
  value       = aws_instance.lb_01.public_ip
}

output "web_01_public_ip" {
  description = "Public IPv4 address of web-01 (Flask Web Node 1)"
  value       = aws_instance.web_01.public_ip
}

output "web_02_public_ip" {
  description = "Public IPv4 address of web-02 (Flask Web Node 2)"
  value       = aws_instance.web_02.public_ip
}

output "db_01_public_ip" {
  description = "Public IPv4 address of db-01 (PostgreSQL Database Node)"
  value       = aws_instance.db_01.public_ip
}

# ------------------------------------------------------------------------------
# 2. Aggregated Public & Private IP Maps
# ------------------------------------------------------------------------------
output "all_public_ips" {
  description = "Dictionary mapping all 5 node names to their public IPv4 addresses"
  value = {
    "ops-node" = aws_instance.ops_node.public_ip
    "lb-01"    = aws_instance.lb_01.public_ip
    "web-01"   = aws_instance.web_01.public_ip
    "web-02"   = aws_instance.web_02.public_ip
    "db-01"    = aws_instance.db_01.public_ip
  }
}

output "all_private_ips" {
  description = "Dictionary mapping all 5 node names to their internal VPC private IPs"
  value = {
    "ops-node" = aws_instance.ops_node.private_ip
    "lb-01"    = aws_instance.lb_01.private_ip
    "web-01"   = aws_instance.web_01.private_ip
    "web-02"   = aws_instance.web_02.private_ip
    "db-01"    = aws_instance.db_01.private_ip
  }
}

# ------------------------------------------------------------------------------
# 3. Service Access Endpoints
# ------------------------------------------------------------------------------
output "service_endpoints" {
  description = "Key HTTP and service URLs for the Smart Hostel cluster"
  value = {
    "haproxy_public_url"      = "http://${aws_instance.lb_01.public_ip}"
    "haproxy_stats_url"       = "http://${aws_instance.lb_01.public_ip}:8404"
    "web_01_direct_flask_url" = "http://${aws_instance.web_01.public_ip}:5000"
    "web_02_direct_flask_url" = "http://${aws_instance.web_02.public_ip}:5000"
    "db_postgres_connection"  = "postgresql://hostel_admin:<PASSWORD>@${aws_instance.db_01.private_ip}:5432/hostel_erp_db"
  }
}

# ------------------------------------------------------------------------------
# 4. Ansible Inventory Path
# ------------------------------------------------------------------------------
output "ansible_inventory_file" {
  description = "Absolute path of the auto-generated Ansible inventory file"
  value       = abspath(local_file.ansible_inventory.filename)
}

# ------------------------------------------------------------------------------
# 5. SSH Connection Commands
# ------------------------------------------------------------------------------
output "ssh_commands" {
  description = "Convenient SSH commands to connect to each node"
  value = {
    "ops-node" = "ssh ubuntu@${aws_instance.ops_node.public_ip}"
    "lb-01"    = "ssh ubuntu@${aws_instance.lb_01.public_ip}"
    "web-01"   = "ssh ubuntu@${aws_instance.web_01.public_ip}"
    "web-02"   = "ssh ubuntu@${aws_instance.web_02.public_ip}"
    "db-01"    = "ssh ubuntu@${aws_instance.db_01.public_ip}"
  }
}
