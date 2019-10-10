#!/usr/bin/env python3

import argparse
import logging
from helpers import aws_batch_helpers

if __name__ == "__main__":

    logFormatter = logging.Formatter(
        '%(asctime)s %(levelname)-8s [Nextflow AWS Batch Squared] %(message)s'
    )
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.INFO)

    # Write logs to STDOUT
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)

    parser = argparse.ArgumentParser(
        description='Run a Nextflow workflow on AWS Batch.')

    parser.add_argument(
        '--workflow',
        type=str,
        default="hello",
        help='Location of the workflow to run'
    )

    parser.add_argument(
        '--working-directory',
        type=str,
        default=None,
        help='Location in S3 to use for temporary files'
    )

    parser.add_argument(
        '--name',
        type=str,
        default="nextflow_workflow",
        help='Name used for this run'
    )

    parser.add_argument(
        '--config-file',
        type=str,
        default=None,
        help='Optional Nextflow config file'
    )

    parser.add_argument(
        '--profile-name',
        type=str,
        default='default',
        help='Profile used to specify AWS credentials'
    )

    parser.add_argument(
        '--region-name',
        type=str,
        default='us-west-2',
        help='AWS Region'
    )

    parser.add_argument(
        '--docker-image',
        type=str,
        default='quay.io/fhcrc-microbiome/nextflow:v0.0.3',
        help='Docker image used for the Nextflow head node'
    )

    parser.add_argument(
        '--job-role-arn',
        type=str,
        default=None,
        help='JobRoleARN used for AWS Batch'
    )

    parser.add_argument(
        '--temporary-volume',
        type=str,
        default=None,
        help='Volume available on the AMI for temporary scratch space'
    )

    parser.add_argument(
        '--job-queue',
        type=str,
        default=None,
        help='Queue used on AWS Batch'
    )

    parser.add_argument(
        '--arguments',
        type=str,
        default=None,
        help='Comma-separated list of arguments in KEY=VALUE format (e.g. foo=bar,next=flow)'
    )

    parser.add_argument(
        '--restart-uuid',
        type=str,
        default=None,
        help='If specified, restart the previously run job with this UUID'
    )

    parser.add_argument(
        '--tower-token',
        type=str,
        default=None,
        help='If specified, use Tower (tower.nf) to monitor the workflow'
    )

    args = parser.parse_args()

    # Set up the connection to AWS Batch
    batch = aws_batch_helpers.Batch(args.profile_name, args.region_name)

    # Get the job definition to use for the Nextflow head node
    job_definition_name = batch.set_up_job_definition(
        profile_name=args.profile_name,
        docker_image=args.docker_image,
        job_role_arn=args.job_role_arn,
    )

    logging.info("Using job definition: {}".format(job_definition_name))

    # Start the job which will run the Nextflow head node
    batch.start_job(
        restart_uuid=args.restart_uuid,
        working_directory=args.working_directory,
        job_definition=job_definition_name,
        workflow=args.workflow,
        name=args.name,
        arguments=args.arguments,
        queue=args.job_queue,
        config_file=args.config_file,
        job_role_arn=args.job_role_arn,
        temporary_volume=args.temporary_volume,
        aws_region=args.region_name,
        tower_token=args.tower_token,
    )
