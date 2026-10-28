output "vpc_id" {
  value = module.network.vpc_id
}

output "alb_dns_name" {
  value = module.network.alb_dns_name
}

output "ecr_repository_url" {
  value = module.ecs.ecr_repository_url
}

output "ecs_cluster_name" {
  value = module.ecs.cluster_name
}

output "ecs_service_name" {
  value = module.ecs.service_name
}

output "database_endpoint" {
  value = module.data.database_endpoint
}

output "redis_endpoint" {
  value = module.data.redis_endpoint
}

output "db_password_secret_arn" {
  value = module.security.db_password_secret_arn
}

output "redteam_schedule_rule" {
  value = module.security.redteam_schedule_rule
}
