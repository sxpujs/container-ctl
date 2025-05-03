# container-ctl
Docker容器管理

### 安装步骤

```bash
# 1. 安装 Python 3.12 并创建虚拟环境
uv python install 3.12
uv venv --python 3.12

# 2. 激活虚拟环境
# Unix/macOS:
source .venv/bin/activate
# Windows:
# .venv\Scripts\activate

# 3. 安装项目依赖
uv sync
