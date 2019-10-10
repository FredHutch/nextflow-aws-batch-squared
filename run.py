#!/usr/bin/env python3

"""
Script to run a job in Batch Squared
"""

import argparse
import logging
from helpers import aws_batch_helpers  # pylint: disable=no-name-in-module

if __name__ == "__main__":

    LOG_FORMATTER = logging.Formatter(
        "%(asctime)s %(levelname)-8s [Nextflow AWS Batch Squared] %(message)s"
    )
    ROOT_LOGGER = logging.getLogger()
    ROOT_LOGGER.setLevel(logging.INFO)

    # Write logs to STDOUT
    CONSOLE_HANDLER = logging.StreamHandler()
    CONSOLE_HANDLER.setFormatter(LOG_FORMATTER)
    ROOT_LOGGER.addHandler(CONSOLE_HANDLER)

    PARSER = argparse.ArgumentParser(
        description="Run a Nextflow workflow on AWS Batch."
    )

    PARSER.add_argument(
        "--workflow", type=str, default="hello", help="Location of the workflow to run"
    )

    PARSER.add_argument(
        "--working-directory",
        type=str,
        default=None,
        help="Location in S3 to use for temporary files",
    )

    PARSER.add_argument(
        "--name", type=str, default="nextflow_workflow", help="Name used for this run"
    )

    PARSER.add_argument(
        "--config-file", type=str, default=None, help="Optional Nextflow config file"
    )

    PARSER.add_argument(
        "--docker-image",
        type=str,
        default="quay.io/fhcrc-microbiome/nextflow:v0.0.4",
        help="Docker image used for the Nextflow head node",
    )

    PARSER.add_argument(
        "--job-role-arn", type=str, default=None, help="JobRoleARN used for AWS Batch"
    )

    PARSER.add_argument(
        "--temporary-volume",
        type=str,
        default=None,
        help="Volume available on the AMI for temporary scratch space",
    )

    PARSER.add_argument(
        "--job-queue", type=str, default=None, help="Queue used on AWS Batch"
    )

    PARSER.add_argument(
        "--arguments",
        type=str,
        default=None,
        help="Comma-separated list of arguments in KEY=VALUE format (e.g. foo=bar,next=flow)",
    )

    PARSER.add_argument(
        "--restart-uuid",
        type=str,
        default=None,
        help="If specified, restart the previously run job with this UUID",
    )

    PARSER.add_argument(
        "--tower-token",
        type=str,
        default=None,
        help="If specified, use Tower (tower.nf) to monitor the workflow",
    )

    PARSER.add_argument(
        "--watch",
        action="store_true",
        help="With this flag, monitor the status of the workflow until completion",
    )

    PARSER.add_argument(
        "--nextflow-version",
        type=str,
        default="19.09.0-edge",
        help="Version of Nextflow to use",
    )

    ARGS = PARSER.parse_args()

    # Set up the connection to AWS Batch
    ARGS = aws_batch_helpers.Batch()

    # Get the job definition to use for the Nextflow head node
    JOB_DEFINITION_NAME = ARGS.set_up_job_definition(
        docker_image=ARGS.docker_image, job_role_arn=ARGS.job_role_arn
    )

    logging.info("Using job definition: %s", JOB_DEFINITION_NAME)

    # Start the job which will run the Nextflow head node
    JOB_ID = ARGS.start_job(
        restart_uuid=ARGS.restart_uuid,
        working_directory=ARGS.working_directory,
        job_definition=JOB_DEFINITION_NAME,
        workflow=ARGS.workflow,
        name=ARGS.name,
        arguments=ARGS.arguments,
        queue=ARGS.job_queue,
        config_file=ARGS.config_file,
        job_role_arn=ARGS.job_role_arn,
        temporary_volume=ARGS.temporary_volume,
        tower_token=ARGS.tower_token,
        nextflow_version=ARGS.nextflow_version,
    )

    if ARGS.watch:
        ARGS.watch(JOB_ID)
