#!/usr/bin/python3.9
# -*- encoding: utf-8 -*-
import os
import psycopg2
import traceback


class DatabaseConnectionManager(object):

    _conn = None

    def __init__(self, connection_dict, logger=None):

        try:
            postgres_conn = psycopg2.connect(
                database=connection_dict['db_name'],
                host=connection_dict['db_host'],
                user=connection_dict['db_user'],
                password=connection_dict['db_password']
            )
            self.cursor = postgres_conn.cursor()
        except psycopg2.OperationalError as e:
            logger.error(f"Error while trying to connect to {connection_dict['db_name']} database")
            logger.error(traceback.format_exc())
            self.cursor = None


        