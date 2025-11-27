# Customer Support Agent - 智能客服系统

## 项目概述

这是一个基于火山引擎AgentKit构建的智能客服系统，专门用于处理客户咨询和商品售后服务需求。系统集成了CRM系统、知识库、长期记忆和多种通知工具，能够提供专业、高效的客户服务体验。

## 功能特性

### 🔧 核心功能
- **智能客服对话**：基于AI的智能客服，能够理解客户需求并提供准确回答
- **CRM系统集成**：集成客户关系管理系统，支持客户信息查询、商品保修查询等
- **知识库检索**：内置售后相关知识和故障排除指南
- **长期记忆**：支持会话记忆和客户历史记录存储
- **观测能力**：集成OpenTelemetry追踪和APMPlus监控

## 项目结构

```
customer-support/
├── customer_support_agent.py    # 主智能体应用
├── crm_tools.py                 # CRM系统工具函数
├── requirements.txt             # Python依赖包
├── README.md                    # 项目说明文档
└── pre_build/                   # 预构建资源
    ├── crm_demo/                # CRM系统演示
    │   ├── crm_sample.py        # CRM系统示例代码
    │   └── swagger.json         # API文档
    └── knowledge/               # 知识库文件
        ├── policies.md          # 退换货和保修策略
        └── troubleshooting_for_phone.md  # 手机故障排除指南
```

## 详细配置指南

### 1. 前置准备

#### 获取AK/SK
1. 登录火山引擎控制台 (https://console.volcengine.com)
2. 进入"访问控制" → "密钥管理"
3. 点击"创建密钥"，生成新的Access Key和Secret Key
4. 为AK/SK配置AgentKit产品权限：
   - 进入"访问控制" → "策略管理"
   - 添加AgentKit相关权限、添加 TOS 读写权限
   - 将策略绑定到AK/SK

#### 创建知识库和记忆库、MCP工具 (可选)
> 当前应用广场可以一键完成初始化，这些步骤可以在应用广场中一键部署完成。

##### 创建知识库
1. 登录火山引擎AgentKit控制台
2. 进入"知识库" → "导入知识库" → "去创建"
3. 填写知识库名称， 例如： customer-support-knowledge， 知识库描述： 客户支持知识库； 点击创建
4. 导入 `pre_build/knowledge/` 目录下的文件， 完成知识库的创建。
5. 知识库创建完成后，需要导入到 agentkit 中， 此时可以在"知识库" → "知识库列表"中查看， 可以查看代码集成示例。

##### 创建记忆库
1. 登录火山引擎AgentKit控制台
2. 进入"记忆库" → "创建Memory"
3. 填写记忆库名称， 例如： customer-support-memory
4. 点击"创建"， 即可创建一个新的记忆库。

##### 创建 MCP 工具
1. 登录火山引擎AgentKit控制台
2. 进入"工具管理" → "工具列表" → "创建MCP 服务"
3. 创建新的MCP 服务， 选择HTTP 转MCP， 输入如下信息：
   - 工具名称：customer-support-mcp
   - 访问方式：HTTP 转 MCP
   - 接口文档： `pre_build/crm_demo/swagger.json`
   - 后端服务： 可以通过 函数服务 部署一个简单的 CRM系统 函数工具， 用于查询客户信息、商品保修状态等。
4. 查看 MCP 工具的接入地址， 用于后续配置。

### 2. 部署到云上（从本地部署到AgentKit）

#### 配置agentkit.yaml
1. 重命名 `example-agentkit.yaml` 为 `agentkit.yaml`
2. 编辑 `agentkit.yaml`，完善 runtime_envs 配置：
```
    runtime_envs:
      # 系统环境变量
      # 模型名称
      MODEL_AGENT_NAME: deepseek-v3-1-terminus
      # 火山引擎访问密钥
      VOLCENGINE_ACCESS_KEY: 
      VOLCENGINE_SECRET_KEY: 
      # TOS的配置
      DATABASE_TOS_BUCKET: agentkit-cli-{{account_id}}
      DATABASE_TOS_REGION: cn-beijing
      DATABASE_TOS_ENDPOINT: tos-cn-beijing.volces.com
```

#### 安装agentkit cli
1. 确保已安装 Python 3.12 或以上版本
2. 安装 agentkit cli：
```bash
pip3 install -U agentkit-sdk-python  --index-url https://artifacts-cn-beijing.volces.com/repository/agentkit/simple/ --extra-index-url https://mirrors.volces.com/pypi/simple/
```

#### 部署到AgentKit & 验证
1. 配置环境变量
```
export VOLCENGINE_ACCESS_KEY=your_actual_access_key
export VOLCENGINE_SECRET_KEY=your_actual_secret_key
```
2. 在项目根目录执行部署命令：
```bash
agentkit launch
```
3. 部署完成后，执行验证

> 默认使用 CUST001 作为用户ID，验证客户邮箱为 zhang.ming@example.com
```bash
agentkit invoke --payload '{"prompt": "你好，我之前买的一个电视坏了"}' --headers '{"user_id": "CUST001", "session_id": "session4"}'

agentkit invoke --payload '{"prompt": "我的邮箱为 zhang.ming@example.com"}' --headers '{"user_id": "CUST001", "session_id": "session4"}'
```

### 3. 部署到云上（直接从镜像部署，无需本地代码）

#### 创建 Runtime
1. 去火山引擎 AgentKit 控制台，新建 Runtime
2. 填写 Runtime的基础信息： 名称、描述等
3. 填写 Runtime的镜像地址， 可以使用以下镜像地址
```
agentkit-toolkit-cli-m0fi-cn-beijing.cr.volces.com/agentkit/customer_support_agent:20251124144605
```
4. 填写 Runtime的环境变量， 参考 1. 前置准备 中的配置
```
# 模型名称
MODEL_AGENT_NAME: deepseek-v3-1-terminus
# 火山引擎访问密钥
VOLCENGINE_ACCESS_KEY: 
VOLCENGINE_SECRET_KEY: 
# TOS的配置
DATABASE_TOS_BUCKET: agentkit-cli-{{account_id}}
DATABASE_TOS_REGION: cn-beijing
DATABASE_TOS_ENDPOINT: tos-cn-beijing.volces.com
```
5. 部署发布 Runtime

#### 测试 Runtime
1. 去火山引擎 AgentKit 控制台，查询 Runtime 列表， 找到刚创建的 Runtime
2. 点击"调试"按钮，完善请求信息
    - 填写header： user_id: CUST001, session_id: session1
    - 填写测试 payload：
    ```json
    {
        "prompt": "你好，我之前买的一个电视坏了"
    }
    ```
3. 点击"执行"，查看返回结果


## 许可证

本项目基于Apache License 2.0许可证开源。
