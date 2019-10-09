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
        help='Location of the workflow to run'
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
        default='quay.io/fhcrc-microbiome/nextflow:v0.0.1',
        help='Docker image used for the Nextflow head node'
    )

    parser.add_argument(
        '--job-role-arn',
        type=str,
        default=None,
        help='JobRoleARN used for AWS Batch'
    )

    args = parser.parse_args()

    # Set up the connection to AWS Batch
    batch = aws_batch_helpers.Batch(args.profile_name, args.region_name)

    # Get the job definition to use for the Nextflow head node
    job_definition_name = aws_batch_helpers.set_up_job_definition(
        batch,
        profile_name=args.profile_name,
        docker_image=args.docker_image,
        region_name=args.region_name,
        job_role_arn=args.job_role_arn,
    )

    logging.info("Using job definition: {}".format(job_definition_name))
