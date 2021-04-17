# 北京大学物理学院本科生综合指导课

## 如何部署

### 安装 [poetry](https://github.com/python-poetry/poetry) 并安装项目依赖

> 进阶用法，使用 pyenv+poetry 管理你的虚拟环境。

### 安装项目依赖

重启 shell

```shell
poetry install
```

如果是生产环境：

```shell
poetry install --no-dev
```

### 设置部分

#### 生成 SECRET_KEY
```shell
poetry run python -c 'import django.core.management.utils;print(django.core.management.utils.get_random_secret_key())'
```

#### 准备配置文件

待补充

#### 准备数据表迁移
> 如已有原数据，无需执行本步骤，只需进行数据库的迁移即可
```shell
poetry run python manage.py makemigrations
poetry run python manage.py migrate
```

#### 准备翻译文件

```shell
poetry run python manage.py compilemessages
```

### 本地测试

```shell
# 单纯地跑测试
poetry run pytest
# 记录测试覆盖率
poetry run task test-cov
poetry run task cov-report
# 代码检查
poetry run task flake8 bookB116
```

#### 前端

待补充

#### Nginx

安装 Nginx 并参考如下配置

```nginx
    location / {
        proxy_pass http://127.0.0.1:10801;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header REMOTE-HOST $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static {
        alias /path/to/project/assets;
        expires      12h;
        error_log /dev/null;
        access_log off;
    }
    
    location /media {
        alias /path/to/project/media;
        expires      30d;
        error_log /dev/null;
        access_log off;
    }
```