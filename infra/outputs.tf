output "lake_bucket" {
  value = aws_s3_bucket.lake.bucket
}

output "athena_results_bucket" {
  value = aws_s3_bucket.athena_results.bucket
}

output "athena_workgroup" {
  value = aws_athena_workgroup.main.name
}

output "ci_role_arn" {
  value = aws_iam_role.ci.arn
}
