# ==============================================================================
# Security Groups: Arquitectura Zero-Trust y Mínimo Privilegio (Sin SSH Abierto)
# ==============================================================================

# 1. Security Group para el Application Load Balancer (ALB)
resource "aws_security_group" "alb_sg" {
  name        = "vigila-alb-security-group"
  description = "Permite trafico seguro HTTPS/TLS hacia el balanceador de carga"
  vpc_id      = aws_vpc.vigila_vpc.id

  ingress {
    description = "Trafico web seguro HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Redireccion HTTP a HTTPS"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Permite enviar trafico a los nodos EC2 privados"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "vigila-alb-sg" }
}

# 2. Security Group para Trabajadores EC2 (Procesamiento de Video)
# NOTA DE SEGURIDAD CRÍTICA: NO SE ABRE EL PUERTO 22 (SSH).
# Toda la administración se realiza mediante AWS Systems Manager Session Manager.
resource "aws_security_group" "ec2_workers_sg" {
  name        = "vigila-ec2-workers-security-group"
  description = "Acceso restringido unicamente desde el balanceador ALB"
  vpc_id      = aws_vpc.vigila_vpc.id

  ingress {
    description     = "Trafico de aplicacion proveniente exclusivamente del ALB"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id]
  }

  egress {
    description = "Permite conexion hacia S3, RDS, AWS Systems Manager y APIs externas"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "vigila-ec2-workers-sg" }
}

# 3. Security Group para Amazon RDS PostgreSQL
resource "aws_security_group" "rds_sg" {
  name        = "vigila-rds-database-security-group"
  description = "Aislamiento estricto de base de datos relacional"
  vpc_id      = aws_vpc.vigila_vpc.id

  ingress {
    description     = "Conexion PostgreSQL permitida unicamente desde los trabajadores EC2"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ec2_workers_sg.id]
  }

  egress {
    description = "Sin salida externa"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["10.0.0.0/16"]
  }

  tags = { Name = "vigila-rds-sg" }
}

