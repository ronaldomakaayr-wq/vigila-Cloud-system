# ==============================================================================
# Amazon RDS PostgreSQL Multi-AZ (Alta Disponibilidad y Rendimiento Optimizado)
# ==============================================================================

resource "aws_db_subnet_group" "rds_subnet_group" {
  name        = "vigila-rds-db-subnet-group"
  description = "Subredes privadas y aisladas para RDS Multi-AZ"
  subnet_ids  = [aws_subnet.db_private_1a.id, aws_subnet.db_private_1b.id]

  tags = { Name = "vigila-db-subnet-group" }
}

resource "aws_db_instance" "vigila_postgres" {
  identifier                  = "vigila-postgres-production"
  engine                      = "postgres"
  engine_version              = "16.2"
  instance_class              = var.db_instance_class  # db.m7g.large (AWS Graviton 3)
  allocated_storage           = 50                     # GB
  max_allocated_storage       = 500                    # Auto-escalado de almacenamiento
  storage_type                = "gp3"
  
  db_name                     = "vigila_cloud_db"
  username                    = var.db_username
  manage_master_user_password = true                   # Gestión automática mediante AWS Secrets Manager

  # Configuración Multi-AZ para tolerancia a fallos y alta disponibilidad
  multi_az               = true
  db_subnet_group_name   = aws_db_subnet_group.rds_subnet_group.name
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  publicly_accessible    = false

  # Seguridad y Cifrado
  storage_encrypted = true
  copy_tags_to_snapshot = true

  # Ventanas de Mantenimiento y Backups
  backup_retention_period   = 14
  backup_window             = "03:00-04:00"
  maintenance_window        = "sun:04:30-sun:05:30"
  auto_minor_version_upgrade = true
  deletion_protection       = true
  skip_final_snapshot       = false
  final_snapshot_identifier = "vigila-rds-final-snapshot"

  tags = {
    Name = "vigila-rds-postgres-multiaz"
  }
}

