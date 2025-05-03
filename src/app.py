# Standard library imports
import logging
from typing import Union

import uvicorn
# Third-party imports
from fastapi import FastAPI, File, Form, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from command import execute_command
# Local imports
from filesystem import (FileSystemError, create_directory, file_exists,
                        list_directory, move_file, read_file, write_file)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="File Processor API",
    description="API for Docker container file operations",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Define response model
class APIResponse(BaseModel):
    code: int = 0
    message: str = "OK"
    data: Union[dict, list, str, None] = None

def create_response(data: Union[dict, list, str, None] = None, message: str = "OK", code: int = 0) -> APIResponse:
    return APIResponse(code=code, message=message, data=data)

def create_error_response(message: str, code: int = 10000) -> APIResponse:
    return APIResponse(code=code, message=message, data=None)

# Define request models
class WriteFileRequest(BaseModel):
    path: str
    content: Union[str, bytes]
    task_id: str

class MoveFileRequest(BaseModel):
    source: str
    destination: str
    task_id: str

class PathRequest(BaseModel):
    path: str
    task_id: str

class ExecuteCommandRequest(BaseModel):
    command: str
    timeout_ms: int
    task_id: str

class UploadFileRequest(BaseModel):
    file: UploadFile
    path: str
    task_id: str

# Endpoints
@app.get("/")
def read_root():
    return create_response(data={"status": "running"}, message="File Processor API is running")


@app.get("/file/exists")
def api_file_exists(path: str = Query(...), task_id: str = Query(...)):
    """Check if a file or directory exists in a Docker container."""
    container_name = "cabinet-sandbox"
    logger.info("Checking existence of path: %s for task_id: %s", path, task_id)

    try:
        exists = file_exists(path, container_name)
        return create_response(
            data={"exists": exists},
            message="File existence checked successfully"
        )
    except FileSystemError as e:
        logger.error("Failed to check file existence '%s': %s", path, str(e))
        return create_error_response(str(e), code=10000)
    except Exception as e:
        logger.error("Unexpected error while checking file existence '%s': %s", path, str(e))
        return create_error_response(f"Internal server error: {str(e)}", code=10000)


@app.get("/file/list_directory")
def api_list_directory(path: str = Query(...), task_id: str = Query(...)):
    """List contents of a directory in a Docker container."""
    container_name = "cabinet-sandbox"
    logger.info("Listing directory: %s for task_id: %s", path, task_id)

    try:
        if not path or not isinstance(path, str):
            return create_error_response("Invalid directory path", code=10000)

        result = list_directory(path, container_name)
        return create_response(data=result, message="Directory listed successfully")
    except FileSystemError as e:
        logger.error("Failed to list directory '%s': %s", path, str(e))
        return create_error_response(str(e), code=10000)
    except Exception as e:
        logger.error("Unexpected error while listing directory '%s': %s", path, str(e))
        return create_error_response(f"Internal server error: {str(e)}", code=10000)


@app.get("/file/read_file")
async def api_read_file(path: str = Query(...), task_id: str = Query(...)):
    """Read a file from a Docker container."""
    container_name = "cabinet-sandbox"
    logger.info("Reading file: %s for task_id: %s", path, task_id)

    try:
        content = read_file(path, container_name)
        return create_response(data=content, message="File read successfully")
    except FileSystemError as e:
        logger.error("Failed to read file '%s': %s", path, str(e))
        return create_error_response(str(e), code=10000)
    except Exception as e:
        logger.error("Unexpected error while reading file '%s': %s", path, str(e))
        return create_error_response(f"Internal server error: {str(e)}", code=10000)


@app.post("/file/write_file")
async def api_write_file(request: WriteFileRequest):
    """Write content to a file in a Docker container."""
    container_name = "cabinet-sandbox"
    logger.info("Writing file: %s for task_id: %s", request.path, request.task_id)

    try:
        write_file(request.path, request.content, container_name)
        return create_response(
            message=f"File written to {request.path} successfully"
        )
    except FileSystemError as e:
        logger.error("Failed to write file '%s': %s", request.path, str(e))
        return create_error_response(str(e), code=10000)
    except Exception as e:
        logger.error("Unexpected error while writing file '%s': %s", request.path, str(e))
        return create_error_response(f"Internal server error: {str(e)}", code=10000)


@app.post("/file/upload")
async def api_upload_file(
    file: UploadFile = File(...),
    path: str = Form(...),
    task_id: str = Form(...)
):
    """Upload a file to a Docker container."""
    container_name = "cabinet-sandbox"
    logger.info("Uploading file: %s to %s for task_id: %s", file.filename, path, task_id)

    try:
        content = await file.read()
        # Check if path ends with a slash or is empty (indicating it's just a directory)
        if path.endswith('/') or not path:
            # If it's just a directory, append the filename
            full_path = f"{path}{file.filename}"
        else:
            # If it's a full path, use it as is
            full_path = path

        write_file(full_path, content, container_name)
        return create_response(
            message=f"File {file.filename} uploaded to {full_path} successfully"
        )
    except FileSystemError as e:
        logger.error("Failed to upload file '%s': %s", path, str(e))
        return create_error_response(str(e), code=10000)
    except Exception as e:
        logger.error("Unexpected error while uploading file '%s': %s", path, str(e))
        return create_error_response(f"Internal server error: {str(e)}", code=10000)


@app.post("/file/create_directory")
def api_create_directory(request: PathRequest):
    """Create a directory in a Docker container."""
    container_name = "cabinet-sandbox"
    logger.info("Creating directory: %s for task_id: %s", request.path, request.task_id)

    try:
        create_directory(request.path, container_name)
        return create_response(
            message=f"Directory created at {request.path} successfully"
        )
    except FileSystemError as e:
        logger.error("Failed to create directory '%s': %s", request.path, str(e))
        return create_error_response(str(e), code=10000)
    except Exception as e:
        logger.error("Unexpected error while creating directory '%s': %s", request.path, str(e))
        return create_error_response(f"Internal server error: {str(e)}", code=10000)


@app.post("/file/move_file")
def api_move_file(request: MoveFileRequest):
    """Move or rename a file in a Docker container."""
    container_name = "cabinet-sandbox"
    logger.info("Moving file: %s to %s for task_id: %s",
                request.source, request.destination, request.task_id)
    try:
        move_file(request.source, request.destination, container_name)
        return create_response(
            message=f"File moved from {request.source} to {request.destination} successfully"
        )
    except FileSystemError as e:
        logger.error("Failed to move file from '%s' to '%s': %s",
                    request.source, request.destination, str(e))
        return create_error_response(str(e), code=10000)
    except Exception as e:
        logger.error("Unexpected error while moving file from '%s' to '%s': %s",
                    request.source, request.destination, str(e))
        return create_error_response(f"Internal server error: {str(e)}", code=10000)


@app.post("/command/execute")
def api_execute_command(request: ExecuteCommandRequest):
    """Execute a command in a Docker container with timeout."""
    try:
        logger.info("Executing command: '%s' with timeout: %dms, task_id: %s",
                    request.command, request.timeout_ms, request.task_id)
        container_name = "cabinet-sandbox"
        exit_code, output = execute_command(
            request.command,
            request.timeout_ms,
            container_name
        )

        if exit_code != 0:
            logger.error("Command execution failed: %s", output)
            return create_error_response(
                message=f"Command execution failed: {output}",
                code=10000
            )

        return create_response(
            data=output,
            message="Command executed successfully"
        )
    except Exception as e:
        logger.error("Unexpected error during command execution: %s", str(e))
        return create_error_response(
            message=f"Internal server error during command execution: {str(e)}",
            code=10000
        )


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=9100, reload=True)