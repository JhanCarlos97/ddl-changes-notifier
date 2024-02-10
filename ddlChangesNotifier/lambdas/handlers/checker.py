#!/usr/bin/python3.9
# -*- encoding: utf-8 -*-
import json
import botocore
import logging

from jsondiff import diff

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_current_schema_version(s3, bucket_name, object_key):
    content_object = s3.Object(bucket_name, object_key)
    file_content = content_object.get()['Body'].read().decode('utf-8')
    return json.loads(file_content)


def upload_new_schema(s3, bucket_name, object_key, schema):
    s3object = s3.Object(bucket_name, object_key)
    s3object.put(
        Body=(bytes(json.dumps(schema).encode('UTF-8')))
    )


def compare_schema(s3, bucket_name, object_key, new_schema):
    schema_changes = None
    try:
        current_schema = get_current_schema_version(s3, bucket_name, object_key)
        schema_changes = diff(current_schema, new_schema, syntax="explicit")
    except botocore.exceptions.ClientError:
        logger.info(f"No schema found for {object_key}, uploading schema")
        upload_new_schema(s3, bucket_name, object_key, new_schema)
        schema_changes = 'NEW TABLE CREATED'

    if schema_changes:
        logger.info(f"Schema changed for {object_key}, uploading new version")
        upload_new_schema(s3, bucket_name, object_key, new_schema)

    return schema_changes