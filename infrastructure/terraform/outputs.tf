output "alb_dns_name" {
  description = "Nombre de dominio publico del Application Load Balancer"
  value       = aws_lb.vigila_alb.dns_name
}

output "s3_bucket_arn" {
  description = "ARN del bucket S3 de almacenamiento de grabaciones"
  value       = aws_s3_bucket.surveillance_recordings.arn
}

output "rds_endpoint" {
  description = "Endpoint de conexion para Amazon RDS PostgreSQL"
  value       = aws_db_instance.vigila_postgres.endpoint
}

output "ssm_role_arn" {
  description = "ARN del rol IAM asignado para administracion mediante AWS Systems Manager"
  value       = aws_iam_role.ec2_ssm_role.arn
}

