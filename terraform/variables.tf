variable "project_name" {
  type    = string
  default = "queryn"
}

variable "environment" {
  type    = string
  default = "production"
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  type    = list(string)
  default = ["10.0.0.0/24", "10.0.1.0/24"]
}

variable "private_subnet_cidrs" {
  type    = list(string)
  default = ["10.0.10.0/24", "10.0.11.0/24"]
}

variable "availability_zones" {
  type    = list(string)
  default = ["us-east-1a", "us-east-1b"]
}

variable "container_image" {
  type    = string
  default = "queryn:latest"
}

variable "container_port" {
  type    = number
  default = 8000
}

variable "service_desired_count" {
  type    = number
  default = 2
}

variable "task_cpu" {
  type    = number
  default = 512
}

variable "task_memory" {
  type    = number
  default = 1024
}

variable "db_instance_class" {
  type    = string
  default = "db.t4g.micro"
}

variable "db_name" {
  type    = string
  default = "queryn"
}

variable "db_username" {
  type    = string
  default = "queryn"
}

variable "redis_node_type" {
  type    = string
  default = "cache.t4g.micro"
}

variable "bedrock_guardrail_id" {
  type    = string
  default = ""
}

variable "bedrock_guardrail_version" {
  type    = string
  default = "DRAFT"
}

variable "redteam_schedule_expression" {
  type    = string
  default = "rate(7 days)"
}

variable "tags" {
  type = map(string)
  default = {
    Project   = "queryn"
    ManagedBy = "terraform"
  }
}
