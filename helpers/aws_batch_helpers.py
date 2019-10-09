import boto3
import json
import logging


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
            job_definition_list = job_definition_list + response["jobDefinitions"]

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
