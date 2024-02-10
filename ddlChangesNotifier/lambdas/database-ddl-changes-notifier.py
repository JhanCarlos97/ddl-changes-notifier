#!/usr/bin/python3.9
# -*- encoding: utf-8 -*-
import os
import boto3
import logging
import traceback
import json

from handlers.connector import DatabaseConnectionManager
from handlers import checker
from handlers import notifier

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_S3_CLIENT = boto3.resource("s3")
_BUCKET_NAME = os.environ["BUCKET_NAME"]
_SESSION = boto3.Session(region_name='us-east-1')
_SSM_CLIENT = _SESSION.client('ssm')
_SECRET_MANAGER_NAMES = os.environ["SECRET_MANAGER_NAMES"]
_ENV = os.environ["ENV"]


def get_database_credentials():
    # Retrieve snowflake credentials from SSM parameter store
    client = _SESSION.client(
        service_name="secretsmanager",
        region_name="us-east-1"
    )

    secrets = [secret.strip() for secret in _SECRET_MANAGER_NAMES.split(',')]
    credentials = []

    for secret_name in secrets:
        logger.info(f"Retrieving credentials from secret {secret_name}")
        response = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(response["SecretString"])

        databases = [database.strip() for database in secret['database'].split(',')]

        for db in databases:
            logger.info(f"Building credentials for {db} database")
            credential = {
                'db_user': secret['username'],
                'db_password': secret['password'],
                'db_host': secret['host'],
                'db_name': db
            }
            credentials.append(credential)

    return credentials


def fetch_all_schemas(cursor):
    cursor.execute("SELECT nspname FROM pg_catalog.pg_namespace", ('BADGES_SFR',))
    response = cursor.fetchall()
    return [f"'{response[i][0]}'" for i in range(len(response)-1, 4, -1)]


def fetch_all_columns(schemas, cursor):
    query = "SELECT table_schema, table_name, column_name, data_type FROM INFORMATION_SCHEMA.COLUMNS where " \
            "table_schema in " + f"({' ,'.join(schemas)}) "
    cursor.execute(query, ('BADGES_SFR',))
    return cursor.fetchall()


def lambda_handler(event, context):

    try:
        notifier_message = ""
        credentials = get_database_credentials()

        change_counter = 1
        for credential in credentials:
            if credential["db_host"] != 'None':
                dbc = DatabaseConnectionManager(credential, logger)

                if dbc.cursor:
                    logger.info("Fetching database schemas")
                    schemas = fetch_all_schemas(dbc.cursor)

                    if schemas:
                        logger.info("Fetching database columns")
                        response = fetch_all_columns(schemas, dbc.cursor)

                        logger.info("Building schemas")
                        tables = {}

                        for tuple_object in response:
                            table_key = f"{tuple_object[0].replace('_','-')}-{tuple_object[1].replace('_','-')}"
                            if table_key not in tables:
                                tables[table_key] = {}

                            tables[table_key][tuple_object[2]] = tuple_object[3]

                        logger.info(f"{len(tables)} tables found in database {credential['db_name']}")

                        for table_key, table_schema in tables.items():

                            logger.info(f"Processing schema {table_key}")
                            object_key = f"{credential['db_name']}/{table_key}.json"
                            change = checker.compare_schema(_S3_CLIENT, _BUCKET_NAME, object_key, table_schema)
                            if change:
                                notifier_message += f"{change_counter}. *Database*: {_ENV.upper()} {credential['db_name'].upper()} | *Table*: {table_key} | *Change*: {change} \n"
                                logger.info(f"{change_counter}. Database: {_ENV.upper()} {credential['db_name'].upper()} | Table: {table_key} | Change: {change}")
                                change_counter += 1

                            if change_counter % 20 == 0 and notifier_message:
                                try:
                                    notifier.notify_slack_channel(notifier_message)
                                    notifier_message = ""
                                except:
                                    logger.error(traceback.format_exc())
                else:
                    logger.info(f"There is no schemas in {credential['db_name']} database")

        if notifier_message:
            try:
                notifier.notify_slack_channel(notifier_message)
            except:
                logger.error(traceback.format_exc())

    except Exception as error:
        logger.error(traceback.format_exc())

