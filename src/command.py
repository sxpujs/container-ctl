"""Command execution operations for Docker containers."""

import logging
from typing import Tuple

import docker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CommandError(Exception):
    """Base exception for command execution operations."""
    pass


def _get_container(container_name: str):
    """
    Get Docker container instance.

    Args:
        container_name (str): Name of the target Docker container

    Returns:
        Docker container instance

    Raises:
        CommandError: If container cannot be accessed
    """
    try:
        client = docker.from_env()
    except docker.errors.DockerException as e:
        raise CommandError(f"Error connecting to Docker: {str(e)}") from e

    try:
        return client.containers.get(container_name)
    except docker.errors.NotFound as e:
        raise CommandError(f"Container '{container_name}' not found") from e
    except docker.errors.APIError as e:
        raise CommandError(f"Docker API error: {str(e)}") from e


def execute_command(command: str, timeout_ms: int, container_name: str) -> Tuple[int, str]:
    """
    Execute a terminal command in a Docker container.

    Args:
        command (str): The command to execute
        timeout_ms (int): Timeout in milliseconds (kept for interface compatibility)
        container_name (str): Name of the target Docker container

    Returns:
        Tuple[int, str]: A tuple containing (exit_code, output)
            - exit_code: The exit code of the command (0 for success, non-zero for failure)
            - output: The command output as a string

    Raises:
        CommandError: If command execution fails
    """
    # Validate parameters
    if not command or not isinstance(command, str):
        raise CommandError("Invalid command")

    try:
        # Get container
        container = _get_container(container_name)

        # Execute the command with shell=True to handle redirections properly
        exit_code, output = container.exec_run(
            ["sh", "-c", command],
            detach=False
        )

        # Decode the output
        output_str = output.decode('utf-8', errors='replace') if output else ""

        # Log the execution result
        logger.info("Command execution result - exit_code: %d, output: %s", exit_code, output_str)

        # If the command contains redirection, verify the file was created/modified
        if '>' in command:
            # Extract the target file path from the command
            target_file = command.split('>')[-1].strip()
            try:
                # Check if the file exists and has content
                file_check_cmd = f"test -s {target_file}"
                file_check_exit_code, _ = container.exec_run(
                    ["sh", "-c", file_check_cmd],
                    detach=False
                )
                if file_check_exit_code != 0:
                    raise CommandError(f"File {target_file} was not created or is empty")
            except Exception as e:
                raise CommandError(f"Failed to verify file creation: {str(e)}") from e

        return exit_code, output_str
    except CommandError as e:
        logger.error("Command execution error: %s", str(e))
        raise
    except Exception as e:
        error_msg = f"Unexpected error during command execution: {str(e)}"
        logger.error("%s", error_msg)
        raise CommandError(error_msg) from e
