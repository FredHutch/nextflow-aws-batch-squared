# nextflow-aws-batch-squared
Run Nextflow on AWS Batch (Squared)

```
usage: run.py [-h] [--workflow WORKFLOW]
              [--working-directory WORKING_DIRECTORY] [--name NAME]
              [--config-file CONFIG_FILE] [--docker-image DOCKER_IMAGE]
              [--job-role-arn JOB_ROLE_ARN]
              [--temporary-volume TEMPORARY_VOLUME] [--job-queue JOB_QUEUE]
              [--arguments ARGUMENTS] [--restart-uuid RESTART_UUID]
              [--tower-token TOWER_TOKEN] [--watch]
              [--nextflow-version NEXTFLOW_VERSION]

Run a Nextflow workflow on AWS Batch.

optional arguments:
  -h, --help            show this help message and exit
  --workflow WORKFLOW   Location of the workflow to run
  --working-directory WORKING_DIRECTORY
                        Location in S3 to use for temporary files
  --name NAME           Name used for this run
  --config-file CONFIG_FILE
                        Optional Nextflow config file
  --docker-image DOCKER_IMAGE
                        Docker image used for the Nextflow head node
  --job-role-arn JOB_ROLE_ARN
                        JobRoleARN used for AWS Batch
  --temporary-volume TEMPORARY_VOLUME
                        Volume available on the AMI for temporary scratch
                        space
  --job-queue JOB_QUEUE
                        Queue used on AWS Batch
  --arguments ARGUMENTS
                        Comma-separated list of arguments in KEY=VALUE format
                        (e.g. foo=bar,next=flow)
  --restart-uuid RESTART_UUID
                        If specified, restart the previously run job with this
                        UUID
  --tower-token TOWER_TOKEN
                        If specified, use Tower (tower.nf) to monitor the
                        workflow
  --watch               With this flag, monitor the status of the workflow
                        until completion
  --nextflow-version NEXTFLOW_VERSION
                        Version of Nextflow to use
```