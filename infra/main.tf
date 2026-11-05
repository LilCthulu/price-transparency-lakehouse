data "aws_caller_identity" "current" {}

locals {
  account_id     = data.aws_caller_identity.current.account_id
  lake_bucket    = "${var.name_prefix}-lake-${local.account_id}"
  results_bucket = "${var.name_prefix}-athena-results-${local.account_id}"
  databases      = ["bronze", "silver", "gold"]
}

# Lake bucket: raw/, staged/, and Iceberg table data
resource "aws_s3_bucket" "lake" {
  bucket = local.lake_bucket
}

resource "aws_s3_bucket_public_access_block" "lake" {
  bucket                  = aws_s3_bucket.lake.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "lake" {
  bucket = aws_s3_bucket.lake.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "lake" {
  bucket = aws_s3_bucket.lake.id

  rule {
    id     = "raw-to-cheaper-storage"
    status = "Enabled"
    filter {
      prefix = "raw/"
    }
    transition {
      days          = 60
      storage_class = "GLACIER_IR"
    }
  }

  rule {
    id     = "staged-expiry"
    status = "Enabled"
    filter {
      prefix = "staged/"
    }
    expiration {
      days = 30
    }
  }

  rule {
    id     = "abort-incomplete-uploads"
    status = "Enabled"
    filter {}
    abort_incomplete_multipart_upload {
      days_after_initiation = 2
    }
  }
}

# Athena results bucket
resource "aws_s3_bucket" "athena_results" {
  bucket = local.results_bucket
}

resource "aws_s3_bucket_public_access_block" "athena_results" {
  bucket                  = aws_s3_bucket.athena_results.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "athena_results" {
  bucket = aws_s3_bucket.athena_results.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "athena_results" {
  bucket = aws_s3_bucket.athena_results.id
  rule {
    id     = "results-expiry"
    status = "Enabled"
    filter {}
    expiration {
      days = 7
    }
  }
}

# Catalog and query engine
resource "aws_glue_catalog_database" "layers" {
  for_each = toset(local.databases)
  name     = each.key
}

resource "aws_athena_workgroup" "main" {
  name = var.name_prefix

  configuration {
    enforce_workgroup_configuration = true
    bytes_scanned_cutoff_per_query  = var.athena_bytes_scanned_cutoff

    engine_version {
      selected_engine_version = "Athena engine version 3"
    }

    result_configuration {
      output_location = "s3://${aws_s3_bucket.athena_results.bucket}/results/"
      encryption_configuration {
        encryption_option = "SSE_S3"
      }
    }
  }
}

# Spend alerts
resource "aws_budgets_budget" "monthly" {
  name         = "${var.name_prefix}-monthly"
  budget_type  = "COST"
  limit_amount = "10"
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 5
    threshold_type             = "ABSOLUTE_VALUE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.budget_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 10
    threshold_type             = "ABSOLUTE_VALUE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.budget_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 10
    threshold_type             = "ABSOLUTE_VALUE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.budget_email]
  }
}

# GitHub Actions role: OIDC only, no static keys
resource "aws_iam_openid_connect_provider" "github" {
  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
}

data "aws_iam_policy_document" "ci_trust" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_repo}:*"]
    }
  }
}

resource "aws_iam_role" "ci" {
  name                 = "${var.name_prefix}-github-ci"
  assume_role_policy   = data.aws_iam_policy_document.ci_trust.json
  max_session_duration = 3600
}

data "aws_iam_policy_document" "ci_access" {
  statement {
    sid       = "ListBuckets"
    actions   = ["s3:ListBucket", "s3:GetBucketLocation"]
    resources = [aws_s3_bucket.lake.arn, aws_s3_bucket.athena_results.arn]
  }
  statement {
    sid       = "ReadWriteObjects"
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:AbortMultipartUpload"]
    resources = ["${aws_s3_bucket.lake.arn}/*", "${aws_s3_bucket.athena_results.arn}/*"]
  }
  statement {
    sid = "GlueCatalog"
    actions = [
      "glue:GetCatalog", "glue:GetDatabase", "glue:GetDatabases",
      "glue:GetTable", "glue:GetTables", "glue:CreateTable", "glue:UpdateTable", "glue:DeleteTable",
      "glue:GetPartition", "glue:GetPartitions",
    ]
    resources = concat(
      ["arn:aws:glue:${var.region}:${local.account_id}:catalog"],
      [for d in local.databases : "arn:aws:glue:${var.region}:${local.account_id}:database/${d}"],
      [for d in local.databases : "arn:aws:glue:${var.region}:${local.account_id}:table/${d}/*"],
      # dbt's ci target writes here (B10), so the schema needs the same access without being a lake layer
      ["arn:aws:glue:${var.region}:${local.account_id}:database/gold_ci"],
      ["arn:aws:glue:${var.region}:${local.account_id}:table/gold_ci/*"],
    )
  }
  statement {
    sid = "AthenaWorkgroup"
    actions = [
      "athena:StartQueryExecution", "athena:StopQueryExecution", "athena:GetQueryExecution",
      "athena:GetQueryResults", "athena:GetWorkGroup",
    ]
    resources = [aws_athena_workgroup.main.arn]
  }
}

resource "aws_iam_role_policy" "ci" {
  name   = "ci-access"
  role   = aws_iam_role.ci.id
  policy = data.aws_iam_policy_document.ci_access.json
}
