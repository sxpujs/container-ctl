"""File system operations for Docker containers."""

import base64
import io
import logging
import os
import re
import tarfile
from typing import Union

import docker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileSystemError(Exception):
    """Base exception for filesystem operations."""
    pass

def _get_container(container_name: str):
    """Get Docker container instance."""
    try:
        client = docker.from_env()
    except docker.errors.DockerException as e:
        raise FileSystemError(f"Error connecting to Docker: {str(e)}") from e

    try:
        return client.containers.get(container_name)
    except docker.errors.NotFound as e:
        raise FileSystemError(f"Container '{container_name}' not found") from e
    except docker.errors.APIError as e:
        raise FileSystemError(f"Docker API error: {str(e)}") from e


def create_directory(path: str, container_name: str) -> None:
    """Create a new directory or ensure it exists in a Docker container."""
    if not path or not isinstance(path, str):
        raise FileSystemError("Invalid directory path")

    container = _get_container(container_name)
    command = f"mkdir -p {path}"
    try:
        exit_code, output = container.exec_run(command)
        if exit_code != 0:
            raise FileSystemError(f"Error creating directory: {output.decode('utf-8')}")
    except docker.errors.APIError as e:
        raise FileSystemError(f"Error executing command in container: {str(e)}") from e

    logger.info("Successfully created or ensured directory '%s' exists in container %s", path, container_name)


def list_directory(path: str, container_name: str) -> list:
    """List directory contents in a Docker container with [FILE] or [DIR] prefixes."""
    if not path or not isinstance(path, str):
        raise FileSystemError("Invalid directory path")

    container = _get_container(container_name)
    command = f"ls -la {path}"
    try:
        exit_code, output = container.exec_run(command)
        if exit_code != 0:
            raise FileSystemError(f"Error listing directory: {output.decode('utf-8')}")

        # Process the output
        contents = []
        lines = output.decode('utf-8').splitlines()
        # Skip the first line which shows total size
        for line in lines[1:]:
            if not line.strip():
                continue

            try:
                # Parse the ls output
                parts = line.split()
                if len(parts) < 9:
                    continue
                # The first character of the permissions indicates type
                file_type = parts[0][0]
                name = ' '.join(parts[8:])
                # Skip . and .. entries
                if name in ['.', '..']:
                    continue
                if file_type == 'd':
                    contents.append(f"[DIR] {name}")
                else:
                    contents.append(f"[FILE] {name}")
            except (IndexError, ValueError) as e:
                logger.error("Error parsing line '%s': %s", line, str(e))
                continue

        logger.info("Successfully listed directory contents for '%s' in container %s", path, container_name)
        return contents

    except docker.errors.APIError as e:
        raise FileSystemError(f"Error executing command in container: {str(e)}") from e


def move_file(source: str, destination: str, container_name: str) -> None:
    """Move or rename files and directories in a Docker container."""
    if not source or not isinstance(source, str):
        raise FileSystemError("Invalid source path")

    if not destination or not isinstance(destination, str):
        raise FileSystemError("Invalid destination path")

    container = _get_container(container_name)

    # Check if source exists
    command = f"[ -e '{source}' ]"
    exit_code, _ = container.exec_run(command)
    if exit_code != 0:
        raise FileSystemError(f"Source path '{source}' does not exist")

    # Check if destination exists
    command = f"[ -e '{destination}' ]"
    exit_code, _ = container.exec_run(command)
    if exit_code == 0:
        raise FileSystemError(f"Destination path '{destination}' already exists")

    # Move the file or directory
    command = f"mv '{source}' '{destination}'"
    try:
        exit_code, output = container.exec_run(command)
        if exit_code != 0:
            raise FileSystemError(f"Error moving file: {output.decode('utf-8')}")
    except docker.errors.APIError as e:
        raise FileSystemError(f"Error executing command in container: {str(e)}") from e


def read_file(path: str, container_name: str) -> str:
    """Read complete contents of a file from a Docker container.
    Returns the content as a string - either plain text or base64 encoded for binary files."""
    if not path or not isinstance(path, str):
        raise FileSystemError("Invalid file path")

    container = _get_container(container_name)

    # Get archive from container
    try:
        bits, stat = container.get_archive(path)
    except docker.errors.APIError as e:
        raise FileSystemError(f"Error reading file from container: {str(e)}") from e

    # Process the tar stream
    file_content = b""
    stream = io.BytesIO()
    for chunk in bits:
        stream.write(chunk)
    stream.seek(0)

    try:
        with tarfile.open(fileobj=stream) as tar:
            for member in tar.getmembers():
                f = tar.extractfile(member)
                if f:
                    file_content = f.read()
                    break
    except tarfile.TarError as e:
        raise FileSystemError(f"Error extracting tar: {str(e)}") from e

    # Try to decode as UTF-8, if it fails encode as base64
    try:
        return file_content.decode('utf-8')
    except UnicodeDecodeError:
        return base64.b64encode(file_content).decode('utf-8')


def file_exists(path: str, container_name: str) -> bool:
    """Check if a file or directory exists in a Docker container."""
    if not path or not isinstance(path, str):
        raise FileSystemError("Invalid path")

    container = _get_container(container_name)
    command = f"[ -e '{path}' ]"
    try:
        exit_code, _ = container.exec_run(command)
        return exit_code == 0
    except docker.errors.APIError as e:
        raise FileSystemError(f"Error checking file existence: {str(e)}") from e


def write_file(path: str, content: Union[str, bytes], container_name: str) -> None:
    """Create new file or overwrite existing file in a Docker container."""
    if not path or not isinstance(path, str):
        raise FileSystemError("Invalid file path")

    if not isinstance(content, (str, bytes)):
        raise FileSystemError("Content must be either string or bytes")

    # Handle base64 encoded content
    if isinstance(content, str):
        base64_pattern = r'^[A-Za-z0-9+/]+={0,2}$'
        if re.match(base64_pattern, content):
            try:
                content = base64.b64decode(content)
            except base64.binascii.Error:
                content = content.encode('utf-8')
        else:
            content = content.encode('utf-8')

    container = _get_container(container_name)

    # Create a tar archive in memory
    tar_stream = io.BytesIO()
    try:
        with tarfile.open(fileobj=tar_stream, mode='w') as tar:
            # Create a file-like object in memory
            file_data = io.BytesIO(content)
            # Create a TarInfo object
            tarinfo = tarfile.TarInfo(name=os.path.basename(path))
            tarinfo.size = len(file_data.getvalue())
            # Add the file to the tar archive
            tar.addfile(tarinfo, file_data)
        tar_stream.seek(0)

        # Copy the file into the container
        container.put_archive(os.path.dirname(path), tar_stream.read())
    except (tarfile.TarError, docker.errors.APIError) as e:
        raise FileSystemError(f"Error writing file to container: {str(e)}") from e
