# ==============================================================================
# Amazon VPC: Arquitectura Multi-AZ Segura y Segmentada para VIGILA
# ==============================================================================

resource "aws_vpc" "vigila_vpc" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "vigila-production-vpc"
  }
}

# Internet Gateway para subredes públicas (ALB)
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.vigila_vpc.id

  tags = {
    Name = "vigila-igw"
  }
}

# Subredes Públicas (Solo para Application Load Balancer y NAT Gateway)
resource "aws_subnet" "public_1a" {
  vpc_id                  = aws_vpc.vigila_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true

  tags = { Name = "vigila-public-subnet-1a" }
}

resource "aws_subnet" "public_1b" {
  vpc_id                  = aws_vpc.vigila_vpc.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "${var.aws_region}b"
  map_public_ip_on_launch = true

  tags = { Name = "vigila-public-subnet-1b" }
}

# Subredes Privadas para Cómputo (EC2 Auto Scaling - SIN IPs Públicas)
resource "aws_subnet" "app_private_1a" {
  vpc_id            = aws_vpc.vigila_vpc.id
  cidr_block        = "10.0.10.0/24"
  availability_zone = "${var.aws_region}a"

  tags = { Name = "vigila-app-private-subnet-1a" }
}

resource "aws_subnet" "app_private_1b" {
  vpc_id            = aws_vpc.vigila_vpc.id
  cidr_block        = "10.0.11.0/24"
  availability_zone = "${var.aws_region}b"

  tags = { Name = "vigila-app-private-subnet-1b" }
}

# Subredes Aisladas para Amazon RDS Base de Datos Multi-AZ
resource "aws_subnet" "db_private_1a" {
  vpc_id            = aws_vpc.vigila_vpc.id
  cidr_block        = "10.0.20.0/24"
  availability_zone = "${var.aws_region}a"

  tags = { Name = "vigila-db-private-subnet-1a" }
}

resource "aws_subnet" "db_private_1b" {
  vpc_id            = aws_vpc.vigila_vpc.id
  cidr_block        = "10.0.21.0/24"
  availability_zone = "${var.aws_region}b"

  tags = { Name = "vigila-db-private-subnet-1b" }
}

# Elastic IP & NAT Gateway para salida a Internet segura desde instancias privadas
resource "aws_eip" "nat_eip" {
  domain = "vpc"
  tags   = { Name = "vigila-nat-eip" }
}

resource "aws_nat_gateway" "nat_gw" {
  allocation_id = aws_eip.nat_eip.id
  subnet_id     = aws_subnet.public_1a.id

  tags = { Name = "vigila-nat-gateway" }
  depends_on = [aws_internet_gateway.igw]
}

# Tablas de Ruteo
resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.vigila_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = { Name = "vigila-public-rt" }
}

resource "aws_route_table_association" "pub_1a" {
  subnet_id      = aws_subnet.public_1a.id
  route_table_id = aws_route_table.public_rt.id
}

resource "aws_route_table_association" "pub_1b" {
  subnet_id      = aws_subnet.public_1b.id
  route_table_id = aws_route_table.public_rt.id
}

resource "aws_route_table" "private_rt" {
  vpc_id = aws_vpc.vigila_vpc.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat_gw.id
  }

  tags = { Name = "vigila-private-rt" }
}

resource "aws_route_table_association" "app_1a" {
  subnet_id      = aws_subnet.app_private_1a.id
  route_table_id = aws_route_table.private_rt.id
}

resource "aws_route_table_association" "app_1b" {
  subnet_id      = aws_subnet.app_private_1b.id
  route_table_id = aws_route_table.private_rt.id
}

