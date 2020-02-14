#!/usr/bin/env python3

"""
Script to run a job in Batch Squared
"""

import argparse
import logging
from helpers import aws_batch_helpers  # pylint: disable=no-name-in-module


def main():
    "do the work"
    log_formatter = logging.Formatter(
        "%(asctime)s %(levelname)-8s [Nextflow AWS Batch Squared] %(message)s"
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Write logs to STDOUT
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

    parser = argparse.ArgumentParser(
        description="Run a Nextflow workflow on AWS Batch."
    )

    parser.add_argument(
        "--workflow", type=str, default="hello", help="Location of the workflow to run"
    )

    parser.add_argument(
        "--main-script", type=str, default=None, help="Optional: Location of script in repository, if not the default main script"
    )

    parser.add_argument(
        "--revision", type=str, default=None, help="Revision of the workflow to run"
    )

    parser.add_argument(
        "--working-directory",
        type=str,
        default=None,
        help="Location in S3 to use for temporary files",
    )

    parser.add_argument(
        "--name", type=str, default="nextflow_workflow", help="Name used for this run"
    )

    parser.add_argument(
        "--config-file", type=str, default=None, help="Optional Nextflow config file"
    )

    parser.add_argument(
        "--params-file", type=str, default=None, help="Optional Nextflow params file (-params-file)"
    )

    parser.add_argument(
        "--docker-image",
        type=str,
        default="quay.io/fhcrc-microbiome/nextflow:v0.0.12",
        help="Docker image used for the Nextflow head node",
    )

    parser.add_argument(
        "--job-role-arn", type=str, default=None, help="JobRoleARN used for AWS Batch"
    )

    parser.add_argument(
        "--temporary-volume",
        type=str,
        default=None,
        help="Volume available on the AMI for temporary scratch space",
    )

    parser.add_argument(
        "--job-queue", type=str, default=None, help="Queue used on AWS Batch"
    )

    parser.add_argument(
        "--arguments",
        type=str,
        default=None,
        help='Semi-colon-separated list of arguments in KEY=VALUE format (e.g. "foo=bar;next=flow")'
    )

    parser.add_argument(
        "--restart-uuid",
        type=str,
        default=None,
        help="If specified, restart the previously run job with this UUID",
    )

    parser.add_argument(
        "--tower-token",
        type=str,
        default=None,
        help="If specified, use Tower (tower.nf) to monitor the workflow",
    )

    parser.add_argument(
        "--watch",
        action="store_true",
        help="With this flag, monitor the status of the workflow until completion",
    )

    parser.add_argument(
        "--nextflow-version",
        type=str,
        default="19.09.0-edge",
        help="Version of Nextflow to use",
    )

    args = parser.parse_args()

    # Set up the connection to AWS Batch
    batch = aws_batch_helpers.Batch()

    # Get the job definition to use for the Nextflow head node
    job_definition_name = batch.set_up_job_definition(
        docker_image=args.docker_image, job_role_arn=args.job_role_arn
    )

    logging.info("Using job definition: %s", job_definition_name)

    # Start the job which will run the Nextflow head node
    job_id, workflow_uuid = batch.start_job(
        restart_uuid=args.restart_uuid,
        working_directory=args.working_directory,
        job_definition=job_definition_name,
        workflow=args.workflow,
        main_script=args.main_script,
        revision=args.revision,
        name=args.name,
        arguments=args.arguments,
        queue=args.job_queue,
        config_file=args.config_file,
        params_file=args.params_file,
        job_role_arn=args.job_role_arn,
        temporary_volume=args.temporary_volume,
        tower_token=args.tower_token,
        nextflow_version=args.nextflow_version,
    )

    if args.watch:
        batch.watch(job_id)

    logging.info(
        "The workflow is no longer running. To restart, use --restart-uuid {}".format(workflow_uuid))

if __name__ == "__main__":
    main()
