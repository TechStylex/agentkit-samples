# veadk-python Bug Report 提交指南

## Issue 已创建

Issue 文档位置: `.issues/veadk-nonetype-get-function-responses.md`
Patch 文件位置: `.issues/veadk-runner-fix.patch`

## 提交方式

### 方式一：GitHub Issue

1. 访问 veadk-python 仓库：**https://github.com/volcengine/veadk-python**

2. 点击 **Issues** → **New Issue**

3. 复制 `.issues/veadk-nonetype-get-function-responses.md` 的内容粘贴

4. 添加标签：`bug`, `runner`, `null-safety`

### 方式二：提交 Pull Request

1. Fork 仓库：https://github.com/volcengine/veadk-python

2. Clone 你的 fork：
   ```bash
   git clone https://github.com/YOUR_USERNAME/veadk-python.git
   cd veadk-python
   ```

3. 创建修复分支：
   ```bash
   git checkout -b fix/null-check-get-function-responses
   ```

4. 应用 patch 或手动修改 `veadk/runner.py`：
   
   在第 139 行后添加：
   ```python
   # Skip None events to prevent AttributeError
   if event is None:
       logger.warning("Received None event from generator, skipping...")
       continue
   ```

5. 提交并推送：
   ```bash
   git add veadk/runner.py
   git commit -m "fix: add null check before accessing event methods in runner.py
   
   - Prevents 'NoneType' object has no attribute 'get_function_responses' error
   - Occurs when using MCP tools or complex tool chains that may yield None events
   - Adds warning log for debugging purposes
   
   Fixes #XXX"
   
   git push origin fix/null-check-get-function-responses
   ```

6. 在 GitHub 上创建 Pull Request

## 临时本地修复

如果需要立即修复，可以直接修改本地安装的 veadk：

```bash
# 找到 veadk 安装位置
pip show veadk-python | grep Location

# 编辑 runner.py（以下路径根据实际情况调整）
code ~/.local/lib/python3.12/site-packages/veadk/runner.py
```

在第 139 行 `yield event` 后添加：

```python
if event is None:
    continue
```

## 相关信息

- **veadk-python 版本**: 0.2.29
- **GitHub 仓库**: https://github.com/volcengine/veadk-python
- **受影响用例**: `02-use-cases/video_gen` (使用 MCP 工具的视频生成案例)

## 联系方式

如有问题可联系 veadk-python 维护者：
- fangyozheng@gmail.com
- cu.eric.lee@gmail.com
- sliverydayday@gmail.com
- mengwangwm@gmail.com
