#!/usr/bin/python3.9
# -*- encoding: utf-8 -*-
import urllib3
import os
import json


def notify_slack_channel(message):

    message = '*DDL CHANGES DETECTED*\n' + message

    url = os.environ["SLACK_CHANNEL_WEBHOOK"]
    slack_data = {
        "username": "DatabaseDDLChangesDetectorBOT",
        "icon_emoji": ":female-detective:",
        "channel" : "#company-alert-ddl-changes",
        "blocks": [
            {
                "type": "section",
                "text": 
                    {
                        "type": "mrkdwn",
                        "text": message
                    } 
            }
        ]
    }
    http = urllib3.PoolManager()
    headers = {'Content-Type': "application/json"}
    response = http.urlopen('POST', url, headers=headers, body=json.dumps(slack_data))
    if response.status != 200:
        raise Exception(response.status, response.data.decode('utf-8'))



