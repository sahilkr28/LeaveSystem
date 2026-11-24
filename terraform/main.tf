# ==============================================================================
# Smart Campus Hostel DevOps Infrastructure - Terraform Configuration
# Provisions 5-node cluster on AWS (us-east-1, Ubuntu 24.04 LTS, t3.micro)
# ==============================================================================

# ------------------------------------------------------------------------------
# 1. Ubuntu 24.04 LTS (Noble Numbat) AMI Data Source
# ------------------------------------------------------------------------------
data "aws_ami" "ubuntu_24_04" {
  most_recent = true
  owners      = ["099720109477"] # Canonical Official

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
}

# ------------------------------------------------------------------------------
# 2. Key Pair (Optional generation or existing key usage)
# ------------------------------------------------------------------------------
resource "aws_key_pair" "hostel_key" {
  count      = var.create_key_pair && var.public_key != "" ? 1 : 0
  key_name   = "${var.project_name}-key"
  public_key = var.public_key

  tags = {
    Name = "${var.project_name}-key"
  }
}

locals {
  selected_key_name = var.create_key_pair && var.public_key != "" ? aws_key_pair.hostel_key[0].key_name : var.key_name
}

# ------------------------------------------------------------------------------
# 3. Custom VPC & Internet Gateway
# ------------------------------------------------------------------------------
resource "aws_vpc" "smart_hostel_vpc" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

resource "aws_internet_gateway" "smart_hostel_igw" {
  vpc_id = aws_vpc.smart_hostel_vpc.id

  tags = {
    Name = "${var.project_name}-igw"
  }
}

# ------------------------------------------------------------------------------
# 4. Public Subnet & Route Table Association
# ------------------------------------------------------------------------------
resource "aws_subnet" "public_subnet" {
  vpc_id                  = aws_vpc.smart_hostel_vpc.id
  cidr_block              = var.public_subnet_cidr
  availability_zone       = var.availability_zone
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-subnet"
  }
}

resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.smart_hostel_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.smart_hostel_igw.id
  }

  tags = {
    Name = "${var.project_name}-public-rt"
  }
}

resource "aws_route_table_association" "public_rta" {
  subnet_id      = aws_subnet.public_subnet.id
  route_table_id = aws_route_table.public_rt.id
}

# ------------------------------------------------------------------------------
# 5. Security Groups (Role-segregated & Comprehensive)
# ------------------------------------------------------------------------------

# Common Security Group: SSH (22), Nagios NRPE (5666), and Outbound Egress
resource "aws_security_group" "common_sg" {
  name        = "${var.project_name}-common-sg"
  description = "Common security group for SSH and Nagios NRPE monitoring"
  vpc_id      = aws_vpc.smart_hostel_vpc.id

  # SSH Access
  ingress {
    description = "SSH administrative access"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allowed_ssh_cidr
  }

  # Nagios NRPE Agent Monitoring
  ingress {
    description = "Nagios NRPE monitoring daemon"
    from_port   = 5666
    to_port     = 5666
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  # All outbound traffic
  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-common-sg"
  }
}

# Load Balancer Security Group: HTTP (80) & HAProxy Stats (8404)
resource "aws_security_group" "lb_sg" {
  name        = "${var.project_name}-lb-sg"
  description = "Security group for HAProxy Load Balancer (HTTP 80, Stats 8404)"
  vpc_id      = aws_vpc.smart_hostel_vpc.id

  # Public HTTP Traffic
  ingress {
    description = "Public HTTP web traffic"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HAProxy Monitoring & Statistics Dashboard
  ingress {
    description = "HAProxy Statistics Dashboard"
    from_port   = 8404
    to_port     = 8404
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-lb-sg"
  }
}

# Web Nodes Security Group: Flask Application (5000)
resource "aws_security_group" "web_sg" {
  name        = "${var.project_name}-web-sg"
  description = "Security group for Flask application webservers (Port 5000)"
  vpc_id      = aws_vpc.smart_hostel_vpc.id

  # Flask Application Port
  ingress {
    description = "Flask Application incoming traffic (from Load Balancer and VPC)"
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-web-sg"
  }
}

# Database Security Group: PostgreSQL (5432 RESTRICTED TO VPC CIDR)
resource "aws_security_group" "db_sg" {
  name        = "${var.project_name}-db-sg"
  description = "Security group for PostgreSQL Database strictly restricted to VPC CIDR"
  vpc_id      = aws_vpc.smart_hostel_vpc.id

  # PostgreSQL Access (Strictly isolated to 10.0.0.0/16 VPC CIDR)
  ingress {
    description = "PostgreSQL database restricted to internal VPC CIDR"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  tags = {
    Name = "${var.project_name}-db-sg"
  }
}

# Operations Security Group: Nagios / Ansible Management Node
resource "aws_security_group" "ops_sg" {
  name        = "${var.project_name}-ops-sg"
  description = "Security group for Operations & Nagios central server"
  vpc_id      = aws_vpc.smart_hostel_vpc.id

  ingress {
    description = "Nagios NRPE inbound checks"
    from_port   = 5666
    to_port     = 5666
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  tags = {
    Name = "${var.project_name}-ops-sg"
  }
}

# ------------------------------------------------------------------------------
# 6. EC2 Instances (5 Linux Nodes: Ubuntu 24.04 LTS, t3.micro)
# ------------------------------------------------------------------------------

# Node 1: Operations Node (Nagios Monitoring, Ansible Orchestration, CI/CD)
resource "aws_instance" "ops_node" {
  ami                         = data.aws_ami.ubuntu_24_04.id
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.public_subnet.id
  key_name                    = local.selected_key_name
  vpc_security_group_ids      = [aws_security_group.common_sg.id, aws_security_group.ops_sg.id]
  associate_public_ip_address = true

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 20
    delete_on_termination = true
  }

  tags = {
    Name = "ops-node"
    Role = "operations"
  }
}

# Node 2: Load Balancer Node (HAProxy, HTTP 80, Stats 8404)
resource "aws_instance" "lb_01" {
  ami                         = data.aws_ami.ubuntu_24_04.id
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.public_subnet.id
  key_name                    = local.selected_key_name
  vpc_security_group_ids      = [aws_security_group.common_sg.id, aws_security_group.lb_sg.id]
  associate_public_ip_address = true

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 20
    delete_on_termination = true
  }

  tags = {
    Name = "lb-01"
    Role = "loadbalancer"
  }
}

# Node 3: Web Server 01 (Flask Web Application Instance 1)
resource "aws_instance" "web_01" {
  ami                         = data.aws_ami.ubuntu_24_04.id
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.public_subnet.id
  key_name                    = local.selected_key_name
  vpc_security_group_ids      = [aws_security_group.common_sg.id, aws_security_group.web_sg.id]
  associate_public_ip_address = true

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 20
    delete_on_termination = true
  }

  tags = {
    Name = "web-01"
    Role = "webserver"
  }
}

# Node 4: Web Server 02 (Flask Web Application Instance 2)
resource "aws_instance" "web_02" {
  ami                         = data.aws_ami.ubuntu_24_04.id
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.public_subnet.id
  key_name                    = local.selected_key_name
  vpc_security_group_ids      = [aws_security_group.common_sg.id, aws_security_group.web_sg.id]
  associate_public_ip_address = true

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 20
    delete_on_termination = true
  }

  tags = {
    Name = "web-02"
    Role = "webserver"
  }
}

# Node 5: Database Server (PostgreSQL Instance, Port 5432 restricted to VPC)
resource "aws_instance" "db_01" {
  ami                         = data.aws_ami.ubuntu_24_04.id
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.public_subnet.id
  key_name                    = local.selected_key_name
  vpc_security_group_ids      = [aws_security_group.common_sg.id, aws_security_group.db_sg.id]
  associate_public_ip_address = true

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 20
    delete_on_termination = true
  }

  tags = {
    Name = "db-01"
    Role = "database"
  }
}

# ------------------------------------------------------------------------------
# 7. Automated Ansible Inventory Generation (../ansible/inventory.ini)
# ------------------------------------------------------------------------------
resource "local_file" "ansible_inventory" {
  filename        = "${path.module}/../ansible/inventory.ini"
  file_permission = "0644"

  content = templatefile("${path.module}/templates/inventory.tpl", {
    project_name     = var.project_name
    environment      = var.environment
    timestamp        = timestamp()
    ops_name         = aws_instance.ops_node.tags["Name"]
    ops_public_ip    = aws_instance.ops_node.public_ip
    ops_private_ip   = aws_instance.ops_node.private_ip
    lb_name          = aws_instance.lb_01.tags["Name"]
    lb_public_ip     = aws_instance.lb_01.public_ip
    lb_private_ip    = aws_instance.lb_01.private_ip
    web01_name       = aws_instance.web_01.tags["Name"]
    web01_public_ip  = aws_instance.web_01.public_ip
    web01_private_ip = aws_instance.web_01.private_ip
    web02_name       = aws_instance.web_02.tags["Name"]
    web02_public_ip  = aws_instance.web_02.public_ip
    web02_private_ip = aws_instance.web_02.private_ip
    db_name          = aws_instance.db_01.tags["Name"]
    db_public_ip     = aws_instance.db_01.public_ip
    db_private_ip    = aws_instance.db_01.private_ip
  })

  depends_on = [
    aws_instance.ops_node,
    aws_instance.lb_01,
    aws_instance.web_01,
    aws_instance.web_02,
    aws_instance.db_01
  ]
}
