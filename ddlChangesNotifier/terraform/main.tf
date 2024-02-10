data "aws_region" "current_region" {}

locals {
  PROJECT_NAME                 = "company-reporting-system"
  ENV                          = terraform.workspace
  AWS_REGION                   = data.aws_region.current_region.name
  AWS_TAGS                     = var.AWS_TAGS
}

########################################################################################################################
# S3
########################################################################################################################

#S3 region
module "bucket-database-schemas-repository" {
  source          = "./modules/s3"
  ENV             = local.ENV
  PROJECT_NAME    = local.PROJECT_NAME
  RESOURCE_SUFFIX = "database-schemas-repository"
  AWS_TAGS        = local.AWS_TAGS
}
#endregion

########################################################################################################################
# Secret manager
########################################################################################################################


#These resources are defined manually in each account
data "aws_secretsmanager_secret" "reporting-common-airbyte" {
  name  = "company/reporting/${local.ENV}/common/airbyte"
}

data "aws_secretsmanager_secret" "reporting-dh-airbyte" {
  name  = "company/reporting/${local.ENV}/dh/airbyte"
}

data "aws_secretsmanager_secret" "reporting-iot-airbyte" {
  name  = "company/reporting/${local.ENV}/iot/airbyte"
}


########################################################################################################################
# LAMBDAS
########################################################################################################################
#lambda region
module "lambda-database-ddl-changes-notifier" {
  source                          = "./modules/lambda"
  ENV                             = local.ENV
  PROJECT_NAME                    = local.PROJECT_NAME
  RESOURCE_SUFFIX                 = "database-ddl-changes-notifier"
  LAMBDA_LAYER                    = [module.lambda-layer.arn]
  LAMBDA_SETTINGS                 = {
    "description"                 = "This function orchestrates the ddl schema changes detection process"
    "handler"                     = "database-ddl-changes-notifier.lambda_handler"
    "runtime"                     = "python3.8"
    "timeout"                     = 600
    "memory_size"                 = 128
    "lambda_script_folder"        = "../lambdas/"
  }
  VPC_SETTINGS = {
    "vpc_subnets"                 = var.DB-SUBNETS[local.ENV]
    "security_group_ids"          = var.DB-SECURITY-GROUPS[local.ENV]
  }
  SECRET_MANAGERS_ARN             = [
      data.aws_secretsmanager_secret.reporting-common-airbyte.arn,
      data.aws_secretsmanager_secret.reporting-dh-airbyte.arn,
      data.aws_secretsmanager_secret.reporting-iot-airbyte.arn
  ]
  BUCKET_ARN                      = module.bucket-database-schemas-repository.arn
  LAMBDA_ENVIRONMENT_VARIABLES    = {
    "SLACK_CHANNEL_WEBHOOK"       = "https://hooks.slack.com/services/rest_of_url_webhook"
    "BUCKET_NAME"                 = module.bucket-database-schemas-repository.id
    "SECRET_MANAGER_NAMES"        = <<EOF
       ${data.aws_secretsmanager_secret.reporting-common-airbyte.name},
       ${data.aws_secretsmanager_secret.reporting-iot-airbyte.name},
       ${data.aws_secretsmanager_secret.reporting-dh-airbyte.name}

EOF
    "ENV"                         = local.ENV
  }
  CREATE_INVOKER_TRIGGER          = true
  LAMBDA_EXECUTION_FREQUENCY      = {
    dev = {
      rate                       = "1440"
      unity                      = "minutes"
    }
    qa = {
      rate                       = "1440"
      unity                      = "minutes"
    }
    stg = {
      rate                       = "1440"
      unity                      = "minutes"
    }
    prd = {
      rate                       = "720"
      unity                      = "minutes"
    }
  }
  AWS_TAGS                        = local.AWS_TAGS
}

#region lambda-layer
module "lambda-layer" {
  source                = "./modules/lambda-layer"
  ENV                   = local.ENV
  PROJECT_NAME          = local.PROJECT_NAME
  RESOURCE_SUFFIX       = "lambda-layer"
  BUILDER_SCRIPT_PATH   = "../utils/lambda-layer-builder.sh"
  REQUIREMENTS_PATH     = "requirements.txt"
  PACKAGE_OUTPUT_NAME   = "lambda-layer"
}
#endregion

