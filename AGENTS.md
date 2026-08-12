## 项目信息
name：networthlens后端
description：个人资产管理平台后端，面向个人用户的资产、负债、现金流、投资与目标管理工具，帮助用户“看清净资产、管好现金流、追踪财务目标
tech-stack：Python FastAPI + PostgreSQL + Redis + Celery + PydanticAI


## 项目结构

> 四层核心架构：
> - model
> - repo
> - router
> - service


```text
.
├── AGENTS.md
├── alembic             # 数据库迁移文件
├── alembic.ini
├── app
│   ├── agent           # agent核心
│   ├── common          # 公共方法/服务
│   ├── config          # 系统配置
│   ├── constant.py     # 常量/枚举
│   ├── core            # 核心配置（请求、异常、中间件等）
│   ├── database        # 数据库、redis client
│   ├── ext             # 插件
│   ├── __init__.py
│   ├── main.py         # 初始化入口
│   ├── middlewares     # 中间件
│   ├── models          # 数据模型层
│   ├── repo            # 仓储层
│   ├── routers         # 路由层
│   ├── schemas         # Pydantic schema参数验证及响应模型
│   ├── services        # 服务层
|   │   └── cache       # 缓存层
│   ├── tasks           # celery task
│   └── utils           # 工具类
├── deployment          # 部署
│   ├── deploy-docker.sh
│   ├── deploy-docker.test.sh
│   ├── DEPLOYMENT.md
│   ├── nginx.conf
├── docker-compose.dev.yml      # 测试compose
├── docker-compose.yml          # 生产compose
├── docker-entrypoint.sh
├── Dockerfile
├── docs                # 文档
├── gunicorn.conf.py        # 生产gunicorn
├── gunicorn.conf.test.py   # 测试gunicorn
├── load_env.py             # 环境变量统一加载器
├── make_celery.py          # celery 初始化
├── manage.py               # 系统启动全局入口
├── pyproject.toml
├── README.md
├── scripts                 # 脚本
├── tests
└── uv.lock

```


## 代码规范

- python version：3.12
- 类型注解：所有公共函数必须写
- 导入顺序：标准库 → 第三方 → 本地模块（每组空一行）
- 命名规范：遵守python命名规范，变量名或函数类名不宜过长，超长时适当缩写
- 文档字符串：所有公开函数使用 Google 风格 docstring


## 编码规范

- 路由函数命名：`get_users`、`create_order`（动词_名词）
- 数据库表名：单数
- 接口名：restful规范，名词
- Service 层方法命名：与路由函数对应
- 所有数据库操作通过 Repo 层，路由层和服务层不直接操作 ORM
- Repo层命名：新增-add、编辑-edit、删除-remove、查询-retrieve、查询列表-list、批量创建-batch_add
- 请求库使用`httpx`，不要使用`requests`
- 避免 hard coding
- 原则上函数行数不宜过长


## 错误处理

- 业务异常使用自定义 Exception 类，`errmsg` 将作为前端显示文本
- 不要使用 bare except



## 测试
- 框架：pytest + pytest-asyncio + httpx
- 覆盖率：不低于 80%
- 测试文件命名：test_*.py
- 每个 API 端点必须有集成测试


## 数据库
- ORM：SQLAlchemy 2.0（异步模式）
- 迁移：Alembic
- 查询优先用 select()，避免 query() 旧风格


## 环境管理

- 本地开发使用 .env 文件管理配置，通过 pydantic-settings 加载
- 不同环境的配置差异通过环境变量覆盖
- 绝不在代码中硬编码数据库连接字符串、密钥等
- 如果新增了环境变量，要写入`.env.example`、`.env`、`.env.test`
