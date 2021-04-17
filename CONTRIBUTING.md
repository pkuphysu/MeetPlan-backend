# Contributing 贡献
  
Thanks for helping to make meet plan system great!

感谢您帮助使综合指导课系统变得更好！

We welcome all kinds of contributions:

我们欢迎各种贡献：

- Bug fixes Bug修复
- Documentation improvements 文档改进
- New features 新的功能
- Refactoring & tidying 重构和整理
- Fix some typo 修正了一些错字
- Write more tests 编写更多测试


## Getting started 入门

If you have a specific contribution in mind, be sure to check the [issues](https://github.com/pkuphysu/MeetPlan-backend/issues) and [projects](https://github.com/pkuphysu/MeetPlan-backend/projects) in progress - someone could already be working on something similar and you can help out.

如果您有特定的想法，请务必检查 [issues](https://github.com/pkuphysu/MeetPlan-backend/issues) 和进行中的 [projects](https://github.com/pkuphysu/MeetPlan-backend/projects) -某人可能已经在从事类似的工作，您可以提供帮助。

## Project setup 项目建立

After cloning this repo, first you should install [Poetry](https://python-poetry.org/docs/#installation), then ensure dependencies are installed by running:

克隆此存储库后，首先应安装 [Poetry](https://python-poetry.org/docs/#installation), 然后通过运行以下命令来确保已安装依赖项：

```sh
poetry install
```

## Running tests 运行测试

After developing, the full test suite can be evaluated by running:

开发完成后，可以通过运行以下命令评估完整的测试套件：

```sh
python manage.py test
```

## Opening Pull Requests 新建 PR

Please fork the project and open a pull request against the master branch.

请 Fork 本项目，并针对 master 分支新建一个PR。

This will trigger a series of test and lint checks.

这将触发一系列测试和格式检查。

We advise that you format and run lint locally before doing this to save time:

我们建议您在进行在本地进行格式化，以节省时间：

```sh
black -l 120 --exclude "/migrations/" apps MeetPlan
flake8 apps MeetPlan manage.py
```

## Documentation 文献资料 

The documentation is not available now. You can contribute it!

该文档现在不可用。 您可以贡献它！
