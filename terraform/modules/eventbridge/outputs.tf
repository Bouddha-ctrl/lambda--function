output "rule_name" {
  description = "EventBridge scheduler name"
  value       = aws_scheduler_schedule.this.name
}

output "rule_arn" {
  description = "EventBridge scheduler ARN"
  value       = aws_scheduler_schedule.this.arn
}