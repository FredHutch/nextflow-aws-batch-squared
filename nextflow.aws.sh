#!/bin/bash

set -e  # fail on any error

echo "=== ENVIRONMENT ==="
echo `env`

echo "=== RUN COMMAND ==="
echo "$@"

NEXTFLOW_PROJECT=$1
shift
NEXTFLOW_PARAMS="$@"

# If the NF_CONFIG has been set, copy down the config file
if [ ! -z "$NF_CONFIG" ]; then
    echo Downloading config file from $NF_CONFIG
    aws s3 cp $NF_CONFIG ~/.nextflow/config
else
    touch ~/.nextflow/config
fi
# Now use the local copy of the config file
NF_CONFIG=~/.nextflow/config

# If the NF_PARAMS_REMOTE has been set, copy down the params file
if [ ! -z "$NF_PARAMS_REMOTE" ]; then
    echo Downloading params file from $NF_PARAMS_REMOTE to params.json
    aws s3 cp $NF_PARAMS_REMOTE /root/.nextflow/params.json

    cat /root/.nextflow/params.json
fi

# Add in config parameters specified from environment variables
# Make sure to overwite any existing values
function remove_line() {
    cat $1 | grep -v $2 > TEMP && mv TEMP $1 
}

remove_line $NF_CONFIG workDir
remove_line $NF_CONFIG process.executor
remove_line $NF_CONFIG process.queue
remove_line $NF_CONFIG aws.region
remove_line $NF_CONFIG aws.batch.cliPath
remove_line $NF_CONFIG aws.batch.jobRole

cat << EOF >> $NF_CONFIG
workDir = "$NF_WORKDIR"
process.executor = "awsbatch"
process.queue = "$NF_JOB_QUEUE"
aws.region = "$AWS_REGION"
aws.batch.cliPath = "/home/ec2-user/miniconda/bin/aws"
aws.batch.jobRole = "$JOB_ROLE_ARN"
EOF

if [ ! -z "$TEMP_VOL" ]; then
    remove_line $NF_CONFIG aws.batch.volumes
    cat << EOF >> $NF_CONFIG
aws.batch.volumes = ['$TEMP_VOL:/tmp:rw']
EOF
fi

if [ ! -z "$TOWER_TOKEN" ]; then
    remove_line $NF_CONFIG tower.accessToken
    remove_line $NF_CONFIG tower.enabled
    cat << EOF >> $NF_CONFIG
tower.accessToken = '$TOWER_TOKEN'
tower.enabled = true
EOF
fi

echo "=== CONFIGURATION ==="
cat $NF_CONFIG

# AWS Batch places multiple jobs on an instance
# To avoid file path clobbering use the JobID and JobAttempt
# to create a unique path
GUID="$AWS_BATCH_JOB_ID/$AWS_BATCH_JOB_ATTEMPT"

if [ "$GUID" = "/" ]; then
    GUID=`date | md5sum | cut -d " " -f 1`
fi

mkdir -p /opt/work/$GUID
cd /opt/work/$GUID

# stage in session cache
# .nextflow directory holds all session information for the current and past runs.
# it should be `sync`'d with an s3 uri, so that runs from previous sessions can be 
# resumed
echo "== Restoring Session Cache =="
aws s3 sync --only-show-errors $NF_LOGSDIR/.nextflow .nextflow

function preserve_session() {
    # stage out session cache
    if [ -d .nextflow ]; then
        echo "== Preserving Session Cache =="
        aws s3 sync --only-show-errors .nextflow $NF_LOGSDIR/.nextflow
    fi

    # .nextflow.log file has more detailed logging from the workflow run and is
    # nominally unique per run.
    #
    # when run locally, .nextflow.logs are automatically rotated
    # when syncing to S3 uniquely identify logs by the batch GUID
    if [ -f .nextflow.log ]; then
        echo "== Preserving Session Log =="
        aws s3 cp --only-show-errors .nextflow.log $NF_LOGSDIR/.nextflow.log.${GUID/\//.}
    fi
}

trap preserve_session EXIT

# stage workflow definition
if [[ "$NEXTFLOW_PROJECT" =~ ^s3://.* ]]; then
    echo "== Staging S3 Project =="
    aws s3 sync --only-show-errors --exclude 'runs/*' --exclude '.*' $NEXTFLOW_PROJECT ./project
    NEXTFLOW_PROJECT=./project
fi

echo "== Running Workflow =="
echo "nextflow run -c $NF_CONFIG $NEXTFLOW_PROJECT $NEXTFLOW_PARAMS"
nextflow run -c $NF_CONFIG $NEXTFLOW_PROJECT $NEXTFLOW_PARAMS