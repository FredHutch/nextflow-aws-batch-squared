# nextflow-aws-batch-squared
Run Nextflow on AWS Batch (Squared)

## Prerequisites

### AWS Credentials / Setup

Make sure that you have AWS credentials available on your computer,
and that those credentials give you access to an AWS Batch queue with
the appropriate configuration. Those configuration details will be
added to this documentation in the future, but they essentially provide
an AWS Batch queue with the added feature that the jobs can start
additional jobs. Depending on your use case, it may also be useful
to provide a configuration which includes some temporary scratch storage
space.

If you are having trouble, make sure that your configuration is specified
by either the `AWS_PROFILE` and `AWS_DEFAULT_REGION` environment variables,
or by running `aws configure`.


## Execution Syntax

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
                        Semi-colon-separated list of arguments in KEY=VALUE
                        format (e.g. "foo=bar;next=flow")
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

## Detailed Explanation of Fields

### Workflow

The `--workflow` can either be a GitHub repository, or a S3 URL pointing to the 
'folder' which contains the entire workflow. If you use an S3 URL, the entire
'folder' will be copied down to the head node and executed as a project. All
that means is that you can have a `main.nf` and `nextflow.config` or whatever
other file structure you expect to have use of for a Nextflow project.

### Working Directory

The `--working-directory` is the location on S3 where temporary files are stored.

### Name

The `--name` is the name used for this run -- it doesn't have to be anything special.

### Config File

The `--config-file` can be used to add more configuration options to the execution.
Don't use the config file for anything that you can specify with this workflow
submission tool (e.g. `jobRoleARN`, `jobQueue`, `towerToken`). The additional config
file must be located on S3.

### Docker Image

The `--docker-image` is the Docker image used to run the Nextflow head node. The
image hosted at `quay.io/fhcrc-microbiome/nextflow` is generated from the Dockerfile
contained in this repo, with tags used to ensure that the most up-to-date version
is being used appropriately.

### Job Role ARN

The `--job-role-arn` is used to specify the jobRoleARN associated with your AWS Batch
configuration. Not all configurations use the jobRoleARN, and so this is optional.

### Temporary Volume

The `--temporary-volume` is used to specify the partition on the host machines
which can be used for temporary scratch space. This is usually a folder set up
in the AMI which has enough space for large-scale file manipulation and emphemeral
storage.

### Job Queue

The `--job-queue` refers to the AWS Batch job queue used for execution. Both the head
node and the workers will be executed on the same queue.

### Arguments

The `--arguments` are used to specify workflow-specific arguments which will be
included when the workflow is invoked. The syntax is:

If you want to invoke a workflow with:

```
--input_files s3://bucket/folder/file1.txt,s3://bucket/folder/file1.txt \
--output_file s3://bucket/folder/output.txt \
--conservative
```

Then you would use

```
--arguments "input_files=s3://bucket/folder/file1.txt,s3://bucket/folder/file1.txt;output_file=s3://bucket/folder/output.txt;conservative"
```

### Restart UUID

The `--restart-uuid` is used to restart previous workflows. When a workflow finishes, 
it tells you the unique identifier (uuid) assigned to that workflow. If you specify
that value when you run the workflow again then it will attempt to resume and pick
up from where the previous job left off.

### Tower Token

The `--tower-token` is used for monitoring workflow progress with [Tower](tower.nf).

### Watch

If you specify `--watch`, then all of the logs of the workflow will be printed to
the screen and you can watch the progress of the workflow.

### Nextflow Version

Use `--nextflow-version` to specify a specific version of Nextflow to run. Note that
the default (`19.09.0-edge` is being used currently due to compatibility with Tower).
