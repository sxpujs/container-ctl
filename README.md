# container-ctl
Docker容器管理, 一个基于FastAPI的文件处理和命令执行服务，主要用于Docker容器中的文件操作和命令执行。

## 主要功能

- 文件系统操作（创建、读取、写入、移动文件等）
- 命令执行
- 文件上传
- 容器管理

## 环境要求

- Python 3.x
- Docker
- 虚拟环境（推荐）

## 安装和启动

执行下列命令启动服务
```bash
# 安装 Python 3.12 并创建虚拟环境
uv python install 3.12
uv venv --python 3.12

# 激活虚拟环境
source .venv/bin/activate

# 安装项目依赖
uv sync

# 启动服务
sh start.sh
```

## API文档

### 基础信息
- 基础URL: `http://localhost:9100`
- 所有接口都需要提供 `task_id` 参数用于任务追踪

### 文件操作接口

#### 检查文件是否存在
- **URL**: `/file/exists`
- **方法**: GET
- **参数**:
  - `path`: 文件路径
  - `task_id`: 任务ID
- **返回**: 
  - `exists`: 布尔值，表示文件是否存在

#### 列出目录内容
- **URL**: `/file/list_directory`
- **方法**: GET
- **参数**:
  - `path`: 目录路径
  - `task_id`: 任务ID
- **返回**: 目录内容列表

#### 读取文件
- **URL**: `/file/read_file`
- **方法**: GET
- **参数**:
  - `path`: 文件路径
  - `task_id`: 任务ID
- **返回**: 文件内容

#### 写入文件
- **URL**: `/file/write_file`
- **方法**: POST
- **参数**:
  - `path`: 文件路径
  - `content`: 文件内容
  - `task_id`: 任务ID

#### 上传文件
- **URL**: `/file/upload`
- **方法**: POST
- **参数**:
  - `file`: 文件对象
  - `path`: 目标路径
  - `task_id`: 任务ID

#### 创建目录
- **URL**: `/file/create_directory`
- **方法**: POST
- **参数**:
  - `path`: 目录路径
  - `task_id`: 任务ID

#### 移动文件
- **URL**: `/file/move_file`
- **方法**: POST
- **参数**:
  - `source`: 源文件路径
  - `destination`: 目标路径
  - `task_id`: 任务ID

### 命令执行接口

#### 执行命令
- **URL**: `/command/execute`
- **方法**: POST
- **参数**:
  - `command`: 要执行的命令
  - `timeout_ms`: 超时时间（毫秒）
  - `task_id`: 任务ID
- **返回**: 命令执行结果

## 错误处理

所有接口在发生错误时会返回统一的错误格式：
```json
{
    "code": 10000,
    "message": "错误信息",
    "data": null
}
```

## 注意事项

1. 所有文件操作都在名为 "cabinet-sandbox" 的Docker容器中执行
2. 建议使用虚拟环境来管理Python依赖
3. 确保Docker服务正在运行
4. 所有接口都需要提供有效的 `task_id` 参数

