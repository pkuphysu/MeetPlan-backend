# 北京大学物理学院本科生综合指导课后端
[![build][build-image]][build-url]
[![codecov][codecov-image]][codecov-url]

[build-image]: https://github.com/pkuphysu/MeetPlan-backend/actions/workflows/tests.yml/badge.svg
[build-url]: https://github.com/pkuphysu/MeetPlan-backend/actions
[codecov-image]: https://codecov.io/gh/pkuphysu/MeetPlan-backend/branch/master/graph/badge.svg?token=ihNGZISgFl
[codecov-url]: https://codecov.io/gh/pkuphysu/MeetPlan-backend


## 开发指南
见 [CONTRIBUTING](.github/CONTRIBUTING.md)

## 部署

### 安装 [poetry](https://github.com/python-poetry/poetry)

> 进阶用法，使用 pyenv + poetry 管理你的虚拟环境。

### 安装项目依赖

重启 shell 后，执行

```shell
poetry install --no-dev -E {mysql or pgsql}
```
> 上述命令中中括号内根据实际需要二选一即可

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
