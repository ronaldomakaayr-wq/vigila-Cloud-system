# ==============================================================================
# Amazon S3: Almacenamiento Seguro de Grabaciones con Políticas de Ciclo de Vida
# ==============================================================================

resource "aws_s3_bucket" "surveillance_recordings" {
  bucket        = var.s3_recordings_bucket_name
  force_destroy = false

  tags = {
    Name        = "vigila-surveillance-recordings"
    Purpose     = "CCTV-Continuous-Archive"
    Compliance  = "ISO27001-Evidence-Protection"
  }
}

# 1. Bloqueo Total de Acceso Público (Zero Public Access)
resource "aws_s3_bucket_public_access_block" "block_public" {
  bucket = aws_s3_bucket.surveillance_recordings.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# 2. Habilitación de Versiones de Objetos (Anti-Tampering)
resource "aws_s3_bucket_versioning" "versioning" {
  bucket = aws_s3_bucket.surveillance_recordings.id
  versioning_configuration {
    status = "Enabled"
  }
}

# 3. Cifrado en Reposo con AWS KMS
resource "aws_s3_bucket_server_side_encryption_configuration" "kms_encryption" {
  bucket = aws_s3_bucket.surveillance_recordings.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

# 4. POLÍTICA DE CICLO DE VIDA (S3 LIFECYCLE RULE) - REDUCCIÓN MASIVA DE COSTOS
resource "aws_s3_bucket_lifecycle_configuration" "tiering_policy" {
  bucket = aws_s3_bucket.surveillance_recordings.id

  rule {
    id     = "VigilaVideoLifecycleAutomatedTiering"
    status = "Enabled"

    filter {
      prefix = "recordings/"
    }

    # Transición a Standard-Infrequent Access a los 30 días
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    # Transición a Glacier Flexible Retrieval a los 90 días (Auditoría legal)
    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    # Transición a Glacier Deep Archive al cumplir 1 año (365 días)
    transition {
      days          = 365
      storage_class = "DEEP_ARCHIVE"
    }

    # Expiración y eliminación automática de versiones previas no actuales tras 60 días
    noncurrent_version_expiration {
      noncurrent_days = 60
    }
  }
}

