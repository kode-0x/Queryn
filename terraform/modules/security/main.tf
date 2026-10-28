variable "name" {
  type = string
}

variable "bedrock_guardrail_id" {
  type = string
}

variable "bedrock_guardrail_version" {
  type = string
}

variable "redteam_schedule_expression" {
  type = string
}

variable "tags" {
  type = map(string)
}

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

resource "aws_secretsmanager_secret" "db_password" {
  name        = "${var.name}/db-password"
  description = "PostgreSQL password for the Queryn service"
  tags        = var.tags
}

resource "aws_secretsmanager_secret" "openrouter_api_key" {
  name        = "${var.name}/openrouter-api-key"
  description = "Optional OpenRouter API key for the live LLM path"
  tags        = var.tags
}

data "aws_iam_policy_document" "task_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "execution" {
  name               = "${var.name}-execution"
  assume_role_policy = data.aws_iam_policy_document.task_assume.json
  tags               = var.tags
}

resource "aws_iam_role_policy_attachment" "execution_managed" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

data "aws_iam_policy_document" "execution_secrets" {
  statement {
    effect  = "Allow"
    actions = ["secretsmanager:GetSecretValue"]
    resources = [
      aws_secretsmanager_secret.db_password.arn,
      aws_secretsmanager_secret.openrouter_api_key.arn,
    ]
  }
}

resource "aws_iam_role_policy" "execution_secrets" {
  name   = "${var.name}-execution-secrets"
  role   = aws_iam_role.execution.id
  policy = data.aws_iam_policy_document.execution_secrets.json
}

resource "aws_iam_role" "task" {
  name               = "${var.name}-task"
  assume_role_policy = data.aws_iam_policy_document.task_assume.json
  tags               = var.tags
}

data "aws_iam_policy_document" "task" {
  statement {
    effect = "Allow"
    actions = [
      "bedrock:ApplyGuardrail",
    ]
    resources = [
      "arn:aws:bedrock:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:guardrail/*",
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
    ]
    resources = [
      aws_secretsmanager_secret.db_password.arn,
      aws_secretsmanager_secret.openrouter_api_key.arn,
    ]
  }
}

resource "aws_iam_role_policy" "task" {
  name   = "${var.name}-task-policy"
  role   = aws_iam_role.task.id
  policy = data.aws_iam_policy_document.task.json
}

data "aws_iam_policy_document" "redteam_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["scheduler.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "redteam" {
  name               = "${var.name}-redteam"
  assume_role_policy = data.aws_iam_policy_document.redteam_assume.json
  tags               = var.tags
}

resource "aws_cloudwatch_event_rule" "redteam" {
  name                = "${var.name}-redteam"
  description         = "Scheduled adversarial red-team run"
  schedule_expression = var.redteam_schedule_expression
  tags                = var.tags
}

output "task_role_arn" {
  value = aws_iam_role.task.arn
}

output "execution_role_arn" {
  value = aws_iam_role.execution.arn
}

output "db_password_secret_id" {
  value = aws_secretsmanager_secret.db_password.id
}

output "db_password_secret_arn" {
  value = aws_secretsmanager_secret.db_password.arn
}

output "bedrock_guardrail_reference" {
  value = {
    id      = var.bedrock_guardrail_id
    version = var.bedrock_guardrail_version
  }
}

output "redteam_schedule_rule" {
  value = aws_cloudwatch_event_rule.redteam.name
}
