output "api_id" {
  description = "ID of the API Gateway"
  value       = aws_api_gateway_rest_api.api.id
}

output "api_endpoint" {
  description = "Base endpoint URL of the API Gateway"
  value       = aws_api_gateway_stage.api.invoke_url
}

output "api_url_get_latest" {
  description = "URL to get latest 30 oil prices"
  value       = "${aws_api_gateway_stage.api.invoke_url}/oil-prices"
}
