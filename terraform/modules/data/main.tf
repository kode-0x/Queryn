variable "name" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "service_sg_id" {
  type = string
}

variable "db_instance_class" {
  type = string
}

variable "db_name" {
  type = string
}

variable "db_username" {
  type = string
}

variable "db_password_secret_id" {
  type = string
}

variable "redis_node_type" {
  type = string
}

variable "tags" {
  type = map(string)
}

data "aws_secretsmanager_secret_version" "db_password" {
  secret_id = var.db_password_secret_id
}

resource "aws_db_subnet_group" "this" {
  name       = "${var.name}-db-subnets"
  subnet_ids = var.private_subnet_ids
  tags       = var.tags
}

resource "aws_elasticache_subnet_group" "this" {
  name       = "${var.name}-redis-subnets"
  subnet_ids = var.private_subnet_ids
  tags       = var.tags
}

resource "aws_security_group" "database" {
  name        = "${var.name}-db-sg"
  description = "PostgreSQL access from the service"
  vpc_id      = var.vpc_id

  ingress {
    description     = "PostgreSQL from the service"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.service_sg_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, { Name = "${var.name}-db-sg" })
}

resource "aws_security_group" "redis" {
  name        = "${var.name}-redis-sg"
  description = "Redis access from the service"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Redis from the service"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [var.service_sg_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, { Name = "${var.name}-redis-sg" })
}

resource "aws_db_parameter_group" "pgvector" {
  name   = "${var.name}-pgvector"
  family = "postgres16"

  parameter {
    name  = "shared_preload_libraries"
    value = "vector"
  }

  tags = var.tags
}

resource "aws_db_instance" "this" {
  identifier                   = "${var.name}-postgres"
  engine                       = "postgres"
  engine_version               = "16.4"
  instance_class               = var.db_instance_class
  allocated_storage            = 20
  storage_encrypted            = true
  db_name                      = var.db_name
  username                     = var.db_username
  password                     = data.aws_secretsmanager_secret_version.db_password.secret_string
  db_subnet_group_name         = aws_db_subnet_group.this.name
  vpc_security_group_ids       = [aws_security_group.database.id]
  parameter_group_name         = aws_db_parameter_group.pgvector.name
  multi_az                     = true
  skip_final_snapshot          = false
  final_snapshot_identifier    = "${var.name}-postgres-final"
  performance_insights_enabled = true
  deletion_protection          = true
  tags                         = var.tags
}

resource "aws_elasticache_replication_group" "this" {
  replication_group_id       = "${var.name}-redis"
  description                = "Queryn short-term memory and cache"
  node_type                  = var.redis_node_type
  engine                     = "redis"
  engine_version             = "7.1"
  num_cache_clusters         = 2
  automatic_failover_enabled = true
  subnet_group_name          = aws_elasticache_subnet_group.this.name
  security_group_ids         = [aws_security_group.redis.id]
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  tags                       = var.tags
}

output "database_endpoint" {
  value = aws_db_instance.this.address
}

output "redis_endpoint" {
  value = aws_elasticache_replication_group.this.primary_endpoint_address
}
