import boto3
import json
import logging
import uuid


class Batch:

    def __init__(self, profile_name, region_name):
        """Set up the connection to AWS Batch."""
        self.session = boto3.Session(profile_name=profile_name)
        self.client = self.session.client("batch", region_name=region_name)

    def get_job_definitions(self):
        """Return a list of job definitions."""

        # Make a list with all of the job definitions
        job_definition_list = []

        # Get the job definitions
        response = self.client.describe_job_definitions()

        # Add the job definitions to the list
        job_definition_list = job_definition_list + response["jobDefinitions"]

        # If there is pagination, get the next page
        while response.get("nextToken") is not None:
            # Get the next page
            response = self.client.describe_job_definitions(
                nextToken=response["nextToken"]
            )

            # Add the next page to the list
            job_definition_list = job_definition_list + \
                response["jobDefinitions"]

        # Return the entire list of job definitions
        return job_definition_list

    def set_up_job_definition(
        self,
        profile_name="default",
        docker_image=None,
        job_role_arn=None
    ):
        """Set up the job definition used for the Nextflow head node."""

        assert docker_image is not None, "Please specify Docker image for Nextflow head node"
        assert job_role_arn is not None, "Please specify job role ARN"

        # Get the list of existing job definitions
        logging.info("Checking for a suitable existing job definition")
        job_definitions = self.get_job_definitions()

        # Check to see if there is a job definition that is suitable
        for j in job_definitions:

            # Keep this set to true if all elements match
            keep_this_job_definition = True

            # Iterate over each fixed element
            for k, v in [
                ("type", "container"),
                ("status", "ACTIVE"),
                ("jobRoleArn", job_role_arn),
                ("image", docker_image)
            ]:
                # Check the base namespace, as well as the 'containerProperties'
                # Both 'jobRoleArn' and 'image' are under 'containerProperties'
                if j.get(k, j["containerProperties"].get(k)) != v:
                    # If it doesn't match, set the marker to False
                    keep_this_job_definition = False

            # If everything matches, use this one
            if keep_this_job_definition:
                logging.info("Using existing job definition")
                return "{}:{}".format(
                    j["jobDefinitionName"], j["revision"]
                )
        # Otherwise, make a new job definition
        logging.info("Making new job definition")
        response = self.client.register_job_definition(
            jobDefinitionName="nextflow_head_node",
            type="container",
            containerProperties={
                "image": docker_image,
                "jobRoleArn": job_role_arn,
                "vcpus": 1,
                "memory": 4000,
            }
        )

        return "{}:{}".format(
            response["jobDefinitionName"], response["revision"]
        )

    def start_job(
        self,
        restart_uuid=None,
        working_directory=None,
        job_definition=None,
        workflow=None,
        config_file=None,
        name=None,
        arguments=None,
        queue=None,
        head_node_cpus=1,
        head_node_mem_mbs=4000,
        job_role_arn=None,
        temporary_volume=None,
        aws_region=None,
        tower_token=None
    ):
        """Start the job for the Nextflow head node."""

        assert working_directory is not None, "Please specify the working directory"
        assert job_definition is not None, "Please specify the job definition"
        assert workflow is not None, "Please specify the workflow"
        assert config_file is not None, "Please specify the config_file"
        assert name is not None, "Please specify the name"
        assert queue is not None, "Please specify the queue"
        assert job_role_arn is not None, "Please specify the job_role_arn"
        assert aws_region is not None, "Please specify the aws_region"

        assert working_directory.startswith(
            "s3://"), "Working directory must be an S3 path"
        if working_directory.endswith("/") is False:
            working_directory += "/"

        # Use a logs directory for this particular command
        if restart_uuid is None:
            workflow_uuid = str(uuid.uuid4())

        else:
            workflow_uuid = restart_uuid

        logs_directory = "{}{}".format(
            working_directory,
            workflow_uuid
        )

        # Format the command
        command = [
            workflow,
            "-work-dir",
            working_directory,
            "-resume"
        ]

        if arguments is not None:
            for field in arguments.split(","):
                if "=" in field:
                    assert len(field.split(
                        "=")) == 1, "Field must only have a single '=' ({})".format(field)
                    arguments.append("--" + field.split("=")[0])
                    arguments.append(field.split("=")[1])
                else:
                    arguments.append("--" + field)

        # Set up the environment variables
        environment = [
            {
                "name": "NF_JOB_QUEUE",
                "value": queue
            },
            {
                "name": "NF_LOGSDIR",
                "value": logs_directory
            },
            {
                "name": "JOB_ROLE_ARN",
                "value": job_role_arn
            },
            {
                "name": "AWS_REGION",
                "value": aws_region
            }
        ]

        if config_file is not None:
            environment.append({
                "name": "NF_CONFIG",
                "value": config_file
            })

        if temporary_volume is not None:
            environment.append({
                "name": "TEMP_VOL",
                "value": temporary_volume
            })

        if tower_token is not None:
            environment.append({
                "name": "TOWER_TOKEN",
                "value": tower_token
            })

        response = self.client.submit_job(
            jobName=name,
            jobQueue=queue,
            jobDefinition=job_definition,
            containerOverrides={
                "vcpus": head_node_cpus,
                "memory": head_node_mem_mbs,
                "command": command,
                "environment": environment
            }
        )

        logging.info("Started {} as {} (unique ID: {})".format(
            response["jobName"],
            response["jobId"],
            workflow_uuid
        ))
