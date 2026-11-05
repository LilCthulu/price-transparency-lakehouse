variable "region" {
  type    = string
  default = "us-east-1"
}

variable "name_prefix" {
  description = "Prefix for bucket names. The account ID is appended, since S3 names are global."
  type        = string
  default     = "ptl"
}

variable "budget_email" {
  description = "Address for budget alerts. Set it in a gitignored terraform.tfvars."
  type        = string
}

variable "github_repo" {
  description = "owner/repo allowed to assume the CI role."
  type        = string
  default     = "LilCthulu/price-transparency-lakehouse"
}

variable "athena_bytes_scanned_cutoff" {
  description = "Per-query scan limit, the guard against a runaway Athena bill."
  type        = number
  default     = 10737418240 # 10 GiB
}
