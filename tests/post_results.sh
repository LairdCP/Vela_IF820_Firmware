#!/bin/bash

# XRAY_CLIENT_ID and XRAY_CLIENT_SECRET need to be set in your environment
XRAY_TOKEN=$(curl -s -H "Content-Type: application/json" -X POST --data '{ "client_id": "'$XRAY_CLIENT_ID'","client_secret": "'$XRAY_CLIENT_SECRET'" }' https://xray.cloud.getxray.app/api/v2/authenticate | tr -d '"')
# Set project
PROJECT_KEY='L2VV'
# Set test plan
TEST_PLAN='?'
# Test output to upload
OUTPUT_FILE=./mfg_output/output-20230504-111033.xml

curl -H "Content-Type: text/xml" -X POST -H "Authorization: Bearer $XRAY_TOKEN" --data @"$OUTPUT_FILE" "https://xray.cloud.getxray.app/api/v2/import/execution/robot?projectKey=$PROJECT_KEY&testPlanKey=$TEST_PLAN"
