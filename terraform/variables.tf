variable "aws_region" {
  type        = string
  description = "Target AWS deployment region"
  default     = "us-east-1"
}

variable "project_name" {
  type        = string
  description = "Project name prefix applied to all AWS resources"
  default     = "smart-hostel"
}

variable "environment" {
  type        = string
  description = "Deployment environment (e.g. production, staging, dev)"
  default     = "production"
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the custom VPC"
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  type        = string
  description = "CIDR block for the public subnet"
  default     = "10.0.1.0/24"
}

variable "availability_zone" {
  type        = string
  description = "AWS Availability Zone for the public subnet"
  default     = "us-east-1a"
}

variable "instance_type" {
  type        = string
  description = "EC2 instance type for all 5 cluster nodes"
  default     = "t3.micro"
}

variable "key_name" {
  type        = string
  description = "Existing AWS EC2 Key Pair name for SSH authentication"
  default     = "smart-hostel-key"
}

variable "create_key_pair" {
  type        = bool
  description = "Set to true to create a new AWS Key Pair resource from public_key"
  default     = false
}

variable "public_key" {
  type        = string
  description = "SSH public key content used if create_key_pair is true"
  default     = ""
}

variable "allowed_ssh_cidr" {
  type        = list(string)
  description = "CIDR blocks allowed for incoming SSH access on port 22"
  default     = ["0.0.0.0/0"]
}
