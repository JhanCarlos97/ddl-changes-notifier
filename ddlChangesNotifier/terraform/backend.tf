terraform {
  backend "s3" {
    bucket      = "company-data-terraform"
    key         = "ddl-changes-notifier/terraform.tfstate"
    region      = "us-east-1"
    encrypt     = true
    role_arn    = "arn:aws:iam::account_number:role/DataAdminFromParentOrg"
  }
}
provider "aws" {
  region = "us-east-1"
}