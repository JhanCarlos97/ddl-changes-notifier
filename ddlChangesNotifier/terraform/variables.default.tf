variable "DB-SECURITY-GROUPS" {
  type = map(list(string))
  default = {
    dev = ["sg-dev-securitygroup"]
    stg = ["sg-stg-securitygroup"]
    prd = ["sg-prd-securitygroup"]
  }
}

variable "DB-SUBNETS" {
  type = map(list(string))
  default = {
    dev = ["subnet-dev-subnet"]
    stg = ["subnet-dev-subnet"]
    prd = ["subnet-dev-subnet"]
  }
}

variable "AWS_TAGS" {
  type = map(string)
  default = {
      "Project Name"        = "company-reporting"
      "Project Description" = "This project implements a bot to detect DDL changes on RDS databases"
      "Sector"              = "Data Engineering"
      "Company"             = "company - main company"
      "Cost center"         = "1010"
  }
}