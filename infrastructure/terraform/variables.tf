variable "aws_region" {
  description = "Región de AWS para el despliegue"
  type        = str
  default     = "us-east-1"
}

variable "environment" {
  description = "Ambiente de despliegue (prod / dev / staging)"
  type        = string
  default     = "production"
}

variable "vpc_cidr" {
  description = "Rango CIDR para la VPC de VIGILA"
  type        = string
  default     = "10.0.0.0/16"
}

variable "s3_recordings_bucket_name" {
  description = "Nombre único del bucket S3 para grabaciones y evidencia de videovigilancia"
  type        = string
  default     = "vigila-surveillance-recordings-archive-prod"
}

variable "db_instance_class" {
  description = "Clase de instancia para RDS PostgreSQL (Graviton 3)"
  type        = string
  default     = "db.m7g.large"
}

variable "db_username" {
  description = "Usuario administrador de Amazon RDS"
  type        = string
  default     = "vigila_admin"
}

variable "ec2_instance_type" {
  description = "Tipo de instancia para trabajadores EC2 de procesamiento de video (Graviton 3)"
  type        = string
  default     = "c7g.xlarge"
}

