# DDL Changes Notifier

# Description

![Diagram](https://i.imgur.com/zLz91lu.png)

This project has the purpose of detecting any schema changes made on any databases and sending them as Slack notifications. It is important because if a primary table is changed, Airbyte must be updated so that Cube.js also reflects these changes. 

# Infrastructure outside of this repo

There are two important parts to this project that needs to be changed outside of this repo. The first one is the parameter store (inside AWS SSM) which contains the Passbolt credentials for each env user. 

Under the `/company-reporting-system/ddl-changes/passbolt` parameter, there is this specific JSON:

```json
{
    "base_url": "https://passbolt.example",
    "private_key": "-----BEGIN PGP PRIVATE KEY BLOCK-----example-----END PGP PRIVATE KEY BLOCK-----",
    "passphrase": "example"
}
```

The `base_url` can be found under the bod-company Passbolt URL; the `private_key` can be found under the user configuration (when you log in to that user); finally, the `passphrase` is saved inside Passbolt credential named `company-reporting-system <env>`.

The second important part is the databases that will be checked by the DDL Changes Notifier. Currently the only way to include new passwords is to share it in Passbolt with the user `company-reporting-system <env>` and add the `db_name` in the description as a string (or as a list if there is more than one DB per credential).

# Upgrading to a new version/redeploying

1. Install Terraform/latest version of Python
2. If changes were made to the Python code under the folder `lambdas/` run `source utils/lambda-layer-builder.sh` to create the new Lambda layer (make sure to add new libs to the requirements if needed) and add a new description to the lambda layer under `terraform/modules/lambda-layer/main.tf` so that it triggers a new update on Terraform.
3. Create Terraform workspaces running `terraform workspace new dev`, `terraform workspace new stg` and `terraform workspace new prd` and select the environment in which you want to deploy running `terraform workspace select <env>`.
4. Paste the AWS credentials as environment variables in your terminal.
5. Run `terraform init`.
6. Run `terraform plan`.
7. Run `terraform apply`.

Currently you can't run it locally because every environment has at least one database that needs to be inside a VPC to be able to be ran.

# Roadmap

- Adding support to passwords directly inside Parameter Store/SSM.
- Check if tables were actually deleted from the original schema instead of just comparing the existing ones with the S3 bucket.
- Give support to other DB languages outside of PostgreSQL.
- Add alarms/notifications for errors.
  
# Authors

If you have any doubt, contact Guilherme Passos or Gabriel Martelloti.