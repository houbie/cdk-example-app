# cdk-example-app

A Python AWS lambda application that you can deploy with the [AWS CDK](https://docs.aws.amazon.com/cdk/latest/guide/home.html).

## Required tools

* Python: preferred installation via [pyenv](https://github.com/pyenv/pyenv#installation)
  * Main development language
* Nodejs/npm: preferred installation via [nvm](https://github.com/nvm-sh/nvm)
  * For deploying to AWS via the CDK
* Java: preferred installation via [sdkman](https://sdkman.io/)
    * Used for running DynamoDB on your dev machine

## Prepare project

We use [poetry](https://python-poetry.org/) for dependency management.  See the section about _Managing your Python setup_.

## Build and deploy the application
* activate your virtual environment (automatically done when using pyenv)

TODO

## Run locally

TODO

## Unit tests

Tests are defined in the `test` folder in this project.
Use [pytest](https://docs.pytest.org/en/latest/) to run unit tests.
Just run `pytest` in your virtualenv or run tests in your IDE (you have to configure the project to use pytest in Intellij/Pycharm)

TODO: The tests require _DynamoDBLocal_

## Cleanup

TODO

## Intellij / Pycharm

With the _AWS Toolkit_ plugin, you can view/update lambda's, S3 files, cloudwatch logs...

## Managing your Python setup
Note: still have to try out [PDM](https://pdm.fming.dev/), which works like npm. Maybe better then what's described below.

There are lots of ways to install Python and the required tools.
I had the best experience by installing _pyenv_ and _Poetry_ directly on my dev machine:
* Install _pyenv_ via the [installer](https://github.com/pyenv/pyenv-installer) (or the [Windows version](https://github.com/pyenv-win/pyenv-win))
* Install [Poetry](https://python-poetry.org/docs/#installation)

Install the Python version that you want to use for your lambdas (the version for this project is in _.python_version_, currently 3.8.8):
```shell
pyenv install 3.8.8
pyenv virtualenv 3.8.8 cdk-example-app
pyenv local cdk-example-app 3.8.8
```
