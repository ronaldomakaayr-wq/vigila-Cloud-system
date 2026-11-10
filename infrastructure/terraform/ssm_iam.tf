# ==============================================================================
# AWS IAM & Systems Manager (SSM): Acceso Administrativo Seguro sin SSH
# ==============================================================================

# Rol IAM asumido por las instancias EC2
resource "aws_iam_role" "ec2_ssm_role" {
  name = "vigila-ec2-ssm-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

# 1. Política administrada para AWS Systems Manager (Session Manager y Run Command)
resource "aws_iam_role_policy_attachment" "ssm_core_attach" {
  role       = aws_iam_role.ec2_ssm_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# 2. Política de Mínimo Privilegio para Amazon S3 (Solo bucket de grabaciones)
resource "aws_iam_policy" "s3_vigila_policy" {
  name        = "vigila-s3-rw-recordings-policy"
  description = "Permisos de escritura y lectura de video en el bucket S3 de VIGILA"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:PutObjectTagging"
        ]
        Resource = [
          "arn:aws:s3:::${var.s3_recordings_bucket_name}",
          "arn:aws:s3:::${var.s3_recordings_bucket_name}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "s3_attach" {
  role       = aws_iam_role.ec2_ssm_role.name
  policy_arn = aws_iam_policy.s3_vigila_policy.arn
}

# 3. Política para leer credenciales de Systems Manager Parameter Store
resource "aws_iam_policy" "ssm_parameter_store_policy" {
  name        = "vigila-ssm-parameter-store-read"
  description = "Lectura segura de parametros en /vigila/production/*"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:GetParametersByPath"
        ]
        Resource = "arn:aws:ssm:${var.aws_region}:*:parameter/vigila/production/*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ssm_param_attach" {
  role       = aws_iam_role.ec2_ssm_role.name
  policy_arn = aws_iam_policy.ssm_parameter_store_policy.arn
}

# Instance Profile para asignar a Launch Template
resource "aws_iam_instance_profile" "ec2_instance_profile" {
  name = "vigila-ec2-worker-instance-profile"
  role = aws_iam_role.ec2_ssm_role.name
}

