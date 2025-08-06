# AWS Cloud Deployment & Scaling for CHAMAlink

## 1. Push Docker Image to ECR
- Use `scripts/push_to_ecr.sh <aws_account_id> <region> <repo_name>`

## 2. ECS Fargate Deployment
- Register `aws/ecs_task_definition.json` in ECS (replace placeholders).
- Create ECS service using this task definition.
- Attach to a load balancer for HA.

## 3. Managed Database (RDS)
- Provision PostgreSQL RDS (see `aws/rds_config_sample.txt`).
- Update your app’s DB URI.

## 4. S3 for Uploads
- Create an S3 bucket (e.g., `chamalink-uploads`).
- Set `S3_BUCKET` in your app config.
- Use `app/utils/s3_utils.py` for file operations.

## 5. Auto-Scaling & Monitoring
- Use `aws/ecs_service_autoscaling.json` for ECS scaling policy.
- Use `aws/cloudwatch_alarm_cpu.json` for CloudWatch alarm.

## 6. Secrets Management
- Use AWS Secrets Manager for DB and app secrets.

## 7. Logging & Monitoring
- Enable CloudWatch logs for ECS and RDS.

---

**Follow this guide and use the provided scripts/configs for a production-grade, scalable, and highly available deployment.**
