# ==============================================================================
# Amazon EC2 Auto Scaling & Load Balancing: Escalado Dinámico y Optimización
# ==============================================================================

# 1. Application Load Balancer (ALB) Multi-AZ
resource "aws_lb" "vigila_alb" {
  name               = "vigila-production-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = [aws_subnet.public_1a.id, aws_subnet.public_1b.id]

  enable_deletion_protection = false

  tags = { Name = "vigila-alb" }
}

resource "aws_lb_target_group" "vigila_tg" {
  name        = "vigila-workers-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.vigila_vpc.id
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/health"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
    matcher             = "200"
  }
}

resource "aws_lb_listener" "http_listener" {
  load_balancer_arn = aws_lb.vigila_alb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.vigila_tg.arn
  }
}

# 2. Launch Template para Trabajadores de Video (AWS Graviton 3)
resource "aws_launch_template" "worker_lt" {
  name_prefix   = "vigila-worker-graviton-"
  image_id      = "ami-0123456789abcdef0" # Amazon Linux 2023 ARM64
  instance_type = var.ec2_instance_type    # c7g.xlarge (Graviton 3)

  iam_instance_profile {
    arn = aws_iam_instance_profile.ec2_instance_profile.arn
  }

  network_interfaces {
    associate_public_ip_address = false
    security_groups             = [aws_security_group.ec2_workers_sg.id]
  }

  # Configuración de inicialización con AWS Systems Manager habilitado
  user_data = base64encode(<<-EOF
              #!/bin/bash
              dnf update -y
              dnf install -y amazon-ssm-agent
              systemctl enable amazon-ssm-agent
              systemctl start amazon-ssm-agent
              echo "VIGILA Video Processing Worker Initialized via Graviton 3" > /var/log/vigila-init.log
              EOF
  )

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "vigila-video-worker-graviton"
      Role = "Video-Processing-Engine"
    }
  }
}

# 3. Auto Scaling Group con Estrategia Mixta (Savings Plans + Spot)
resource "aws_autoscaling_group" "workers_asg" {
  name_prefix         = "vigila-asg-workers-"
  vpc_zone_identifier = [aws_subnet.app_private_1a.id, aws_subnet.app_private_1b.id]
  target_group_arns   = [aws_lb_target_group.vigila_tg.arn]

  min_size         = 2
  max_size         = 10
  desired_capacity = 3

  # Política de instancias mixtas: Carga base On-Demand con Savings Plan y picos en Spot
  mixed_instances_policy {
    instances_distribution {
      on_demand_base_capacity                  = 2
      on_demand_percentage_above_base_capacity = 30
      spot_allocation_strategy                 = "price-capacity-optimized"
    }

    launch_template {
      launch_template_specification {
        launch_template_id = aws_launch_template.worker_lt.id
        version            = "$Latest"
      }

      override {
        instance_type     = "c7g.xlarge"
        weighted_capacity = "1"
      }
      override {
        instance_type     = "c7g.2xlarge"
        weighted_capacity = "2"
      }
    }
  }

  lifecycle {
    create_before_destroy = true
  }
}

# 4. Target Tracking Scaling Policy (Mantener CPU al 70%)
resource "aws_autoscaling_policy" "cpu_target_tracking" {
  name                   = "vigila-cpu-target-tracking-70"
  policy_type            = "TargetTrackingScaling"
  autoscaling_group_name = aws_autoscaling_group.workers_asg.name

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = 70.0
  }
}

