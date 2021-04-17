# Contributing

Thanks for helping to make meet plan system great!

We welcome all kinds of contributions:

- Bug fixes
- Documentation improvements
- New features
- Refactoring & tidying
- Fix some typo
- Write more tests


## Getting started

If you have a specific contribution in mind, be sure to check the [issues](https://github.com/pkuphysu/MeetPlan-backend/issues) and [projects](https://github.com/pkuphysu/MeetPlan-backend/projects) in progress - someone could already be working on something similar and you can help out.


## Project setup

After cloning this repo, first you should install [Poetry](https://python-poetry.org/docs/#installation), then ensure dependencies are installed by running:

```sh
poetry install
```

## Running tests

After developing, the full test suite can be evaluated by running:

```sh
python manage.py test
```

## Opening Pull Requests

Please fork the project and open a pull request against the master branch.

This will trigger a series of test and lint checks.

We advise that you format and run lint locally before doing this to save time:

```sh
black -l 120 --exclude "/migrations/" apps MeetPlan
flake8 apps MeetPlan manage.py
```

## Documentation

The documentation is not available now. You can contribute it!

