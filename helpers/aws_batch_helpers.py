"helper functions and classes"

import logging
import uuid
import time

import boto3


class Batch:
    "encapsulates a Batch job"

    def __init__(self):
        """Set up the connection to AWS Batch."""
        self.session = boto3.Session()
        self.batch_client = self.session.client("batch")
        self.logs_client = self.session.client("logs")

    def get_job_definitions(self):
        """Return a list of job definitions."""

        # Make a list with all of the job definitions
        job_definition_list = []

        # Get the job definitions
        response = self.batch_client.describe_job_definitions()

        # Add the job definitions to the list
        job_definition_list = job_definition_list + response["jobDefinitions"]

        # If there is pagination, get the next page
        while response.get("nextToken") is not None:
            # Get the next page
            response = self.batch_client.describe_job_definitions(
                nextToken=response["nextToken"]
            )

            # Add the next page to the list
            job_definition_list = job_definition_list + response["jobDefinitions"]

        # Return the entire list of job definitions
        return job_definition_list

    def set_up_job_definition(self, docker_image=None, job_role_arn=None):
        """Set up the job definition used for the Nextflow head node."""

        assert (
            docker_image is not None
        ), "Please specify Docker image for Nextflow head node"
        assert job_role_arn is not None, "Please specify --job-role-arn"

        # Get the list of existing job definitions
        logging.info("Checking for a suitable existing job definition")
        job_definitions = self.get_job_definitions()

        # Check to see if there is a job definition that is suitable
        for j in job_definitions:

            # Keep this set to true if all elements match
            keep_this_job_definition = True

            # Iterate over each fixed element
            for k, value in [
                ("type", "container"),
                ("status", "ACTIVE"),
                ("jobRoleArn", job_role_arn),
                ("image", docker_image),
            ]:
                # Check the base namespace, as well as the 'containerProperties'
                # Both 'jobRoleArn' and 'image' are under 'containerProperties'
                if j.get(k, j["containerProperties"].get(k)) != value:
                    # If it doesn't match, set the marker to False
                    keep_this_job_definition = False

            # If everything matches, use this one
            if keep_this_job_definition:
                logging.info("Using existing job definition")
                return "{}:{}".format(j["jobDefinitionName"], j["revision"])
        # Otherwise, make a new job definition
        logging.info("Making new job definition")
        response = self.batch_client.register_job_definition(
            jobDefinitionName="nextflow_head_node",
            type="container",
            containerProperties={
                "image": docker_image,
                "jobRoleArn": job_role_arn,
                "vcpus": 1,
                "memory": 4000,
            },
        )

        return "{}:{}".format(response["jobDefinitionName"], response["revision"])

    def start_job(  # pylint: disable=too-many-arguments, too-many-locals
        self,
        restart_uuid=None,
        working_directory=None,
        job_definition=None,
        workflow=None,
        revision=None,
        config_file=None,
        name=None,
        arguments=None,
        queue=None,
        head_node_cpus=1,
        head_node_mem_mbs=4000,
        job_role_arn=None,
        temporary_volume=None,
        tower_token=None,
        nextflow_version="19.09.0-edge",
    ):
        """Start the job for the Nextflow head node."""

        assert working_directory is not None, "Please specify --working-directory"
        assert job_definition is not None, "Please specify the job definition"
        # this should never happen as there is a default workflow:
        assert workflow is not None, "Please specify --workflow"
        assert config_file is not None, "Please specify --config-file"
        assert name is not None, "Please specify --name"
        assert queue is not None, "Please specify --job-queue"
        assert job_role_arn is not None, "Please specify --job-rile-arn"

        assert working_directory.startswith(
            "s3://"
        ), "Working directory must be an S3 path"
        if working_directory.endswith("/") is False:
            working_directory += "/"

        # Use a logs directory for this particular command
        if restart_uuid is None:
            workflow_uuid = str(uuid.uuid4())

        else:
            workflow_uuid = restart_uuid

        logs_directory = "{}{}".format(working_directory, workflow_uuid)

        # Format the command
        command = [workflow, "-work-dir", working_directory, "-resume"]

        if revision is not None:
            command.extend(['-r', revision])

        if arguments is not None:
            for field in arguments.split(";"):
                if "=" in field:
                    assert len(
                        field.split("=")
                    ) == 2, "Field must only have a single '=' ({})".format(field)
                    command.append("--" + field.split("=")[0])
                    command.append(field.split("=")[1])
                else:
                    command.append("--" + field)

        # Set up the environment variables
        environment = [
            {"name": "NF_JOB_QUEUE", "value": queue},
            {"name": "NF_LOGSDIR", "value": logs_directory},
            {"name": "JOB_ROLE_ARN", "value": job_role_arn},
            {"name": "NXF_VER", "value": nextflow_version},
        ]

        if config_file is not None:
            environment.append({"name": "NF_CONFIG", "value": config_file})

        if temporary_volume is not None:
            environment.append({"name": "TEMP_VOL", "value": temporary_volume})

        if tower_token is not None:
            environment.append({"name": "TOWER_TOKEN", "value": tower_token})
            command.append("-with-tower")

        response = self.batch_client.submit_job(
            jobName=name,
            jobQueue=queue,
            jobDefinition=job_definition,
            containerOverrides={
                "vcpus": head_node_cpus,
                "memory": head_node_mem_mbs,
                "command": command,
                "environment": environment,
            },
        )

        logging.info(
            "Started %s as AWS Batch ID %s (unique Nextflow ID: %s)",
            response["jobName"],
            response["jobId"],
            workflow_uuid,
        )

        return response["jobId"], workflow_uuid

    def watch(self, job_id, polling_frequency=1, printing_frequency=60):
        """Monitor the status and logs of a job on AWS Batch."""

        # Get the job name and job status
        job_name = self.job_name(job_id)
        job_status = self.job_status(job_id)

        # Keep track of the job status from the previous iteration (makes sense below)
        last_job_status = None

        # Keep track of the last time we printed to the screen
        last_print = time.time()

        # Issue periodic updates to the job status
        while job_status not in ["RUNNING", "FAILED", "SUCCEEDED"]:
            if (
                time.time() - last_print
            ) > printing_frequency or job_status != last_job_status:
                logging.info("Job %s (%s) is %s", job_name, job_id, job_status)
                last_print = time.time()
            time.sleep(polling_frequency)
            last_job_status = job_status
            job_status = self.job_status(job_id)

        # Now just print out the logs until the job is done

        # Keep track of how many lines have been printed
        n_log_lines_printed = 0

        # Get the complete set of logs
        logs = self.get_logs(job_id)

        # Keep printing the logs to the screen
        while len(logs) > n_log_lines_printed or job_status == "RUNNING":
            while len(logs) > n_log_lines_printed:
                logging.info(logs[n_log_lines_printed])
                n_log_lines_printed += 1
            # Wait before checking for more logs
            time.sleep(polling_frequency)

            # Refresh the logs
            logs = self.get_logs(job_id)

            # Get the new job status
            job_status = self.job_status(job_id)

        # The job is now over
        logging.info("The final status of %s (%s) is %s", job_name, job_id, job_status)

    def job_status(self, job_id):
        """Get the status of a job on AWS Batch."""

        response = self.batch_client.describe_jobs(jobs=[job_id])
        return response["jobs"][0]["status"]

    def job_name(self, job_id):
        """Get the name of a job on AWS Batch."""

        response = self.batch_client.describe_jobs(jobs=[job_id])
        return response["jobs"][0]["jobName"]

    def get_logs(self, job_id):
        """Get the logs of a job on AWS Batch."""

        # Get the logstream name
        response = self.batch_client.describe_jobs(jobs=[job_id])
        logstream = response["jobs"][0]["container"]["logStreamName"]

        # Keep a list with the log messages
        logs = []

        # Get the logs
        response = self.logs_client.get_log_events(
            logGroupName="/aws/batch/job", logStreamName=logstream
        )

        # Add to the list
        logs.extend([l["message"] for l in response["events"]])

        # Keep getting more pages
        while response["nextForwardToken"] is not None:

            # Keep track of the last token used
            last_token = response["nextForwardToken"]

            # Get the next page
            response = self.logs_client.get_log_events(
                logGroupName="/aws/batch/job",
                logStreamName=logstream,
                nextToken=last_token,
            )

            # If the token is the same, we're done
            if response["nextForwardToken"] == last_token:
                response["nextForwardToken"] = None
            else:
                # Otherwise keep adding to the logs
                logs.extend([l["message"] for l in response["events"]])

        return logs
