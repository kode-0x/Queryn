locals {
  name = "${var.project_name}-${var.environment}"
  tags = merge(var.tags, {
    Environment = var.environment
  })
}

module "network" {
  source = "./modules/network"

  name                 = local.name
  vpc_cidr             = var.vpc_cidr
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  availability_zones   = var.availability_zones
  container_port       = var.container_port
  tags                 = local.tags
}

module "security" {
  source = "./modules/security"

  name                        = local.name
  bedrock_guardrail_id        = var.bedrock_guardrail_id
  bedrock_guardrail_version   = var.bedrock_guardrail_version
  redteam_schedule_expression = var.redteam_schedule_expression
  tags                        = local.tags
}

module "data" {
  source = "./modules/data"

  name                  = local.name
  vpc_id                = module.network.vpc_id
  private_subnet_ids    = module.network.private_subnet_ids
  service_sg_id         = module.network.service_security_group_id
  db_instance_class     = var.db_instance_class
  db_name               = var.db_name
  db_username           = var.db_username
  db_password_secret_id = module.security.db_password_secret_id
  redis_node_type       = var.redis_node_type
  tags                  = local.tags
}

module "ecs" {
  source = "./modules/ecs"

  name                  = local.name
  aws_region            = var.aws_region
  vpc_id                = module.network.vpc_id
  private_subnet_ids    = module.network.private_subnet_ids
  service_sg_id         = module.network.service_security_group_id
  target_group_arn      = module.network.target_group_arn
  alb_listener_arn      = module.network.alb_listener_arn
  container_image       = var.container_image
  container_port        = var.container_port
  service_desired_count = var.service_desired_count
  task_cpu              = var.task_cpu
  task_memory           = var.task_memory
  task_role_arn         = module.security.task_role_arn
  execution_role_arn    = module.security.execution_role_arn
  tags                  = local.tags
}
