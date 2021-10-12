# cdk-example-app

An AWS lambda application written in Python that you can deploy with the [AWS CDK](https://docs.aws.amazon.com/cdk/latest/guide/home.html).

**I want to share my learnings by making this a public git repo. Please also share your thoughts, comments, improvements
by creating issues, pull requests ... !**

## Why CDK
Tools I used to manage AWS infrastructure:
* [Terraform by HashiCorp](https://www.terraform.io/)
  * Multi-cloud
  * Good for managing cloud infrastructure, but too verbose for managing the many pieces of a serverless application
  * YAML based
* [Serverless Framework](https://www.serverless.com/)
  * Multi-cloud
  * Built-in knowledge of API Gateway and Lambda
    * Manages a lot of components and wiring on your behalf
  * Lots of plugins
  * (partially) run your app on your local machine
  * YAML based (generates Cloudformation)
  * Implemented Nodejs/Javascript
* [AWS SAM](https://docs.aws.amazon.com/serverless-application-model/index.html)
  * AWS only
  * Built-in knowledge of API Gateway and Lambda
    * Manages a lot of components and wiring on your behalf
  * (partially) run your app on your local machine
  * YAML based (generates Cloudformation)
  * Not as mature and developer friendly as Serverless Framework
    * Will it be deprecated in favor of CDK?
* [AWS CDK](https://docs.aws.amazon.com/cdk/latest/guide/home.html)
  * AWS only
  * Written in Typescript with optional Python and Java wrappers
    * I started with the Python CDK, but switched to Typescript
      * Nodejs/Npm is required anyway because the Python code invokes the Nodejs implementation
      * Better typing / code completion in Typescript
      * Easier to troubleshoot / debug in Typescript
  * Ideal when you want to reuse architectural patterns, naming conventions, etc. across multiple projects
    * Everything inside [cdk/lib/common](cdk/lib/common) could be the basis for a reusable CDK library
  * Unit test your infrastructure code

## Used concepts
I created this repo to experiment with multiple concepts at the same time:
* Using CDK for Python AWS Lambda's
  * Small Lambda's with dependencies in a Lambda Layer
* Contract first development with [Connexion](https://connexion.readthedocs.io/en/latest/quickstart.html)
  * No need to repeat your REST API paths in your infrastructure code
  * The _operationId_ in [openApi.yaml](src/cdk_example_app/openApi.yaml) links to the implementation (f.e. [hello_operation](src/cdk_example_app/hello_operation.py))
* Async event handling via S3
  * Automatically store incoming data from API Gateway to S3
  * Create a reusable [wrapper](src/cdk_example_app/common/s3.py) for [S3 event handlers](src/cdk_example_app/s3_integration_event_lambda.py)
  * Keep track of all events in a [DynamoDB table/PynamoDB class](src/cdk_example_app/common/event_log.py)
* Distributed tracing with [OpenTelemetry](https://opentelemetry.io/)
  * Propagate trace context across S3 and SQS

## Required tools

* Python: preferred installation via [pyenv](https://github.com/pyenv/pyenv#installation)
  * Main development language
* Nodejs/npm: preferred installation via [nvm](https://github.com/nvm-sh/nvm)
  * For deploying to AWS via the CDK
* Java: preferred installation via [sdkman](https://sdkman.io/)
    * Used for running DynamoDB on your dev machine

## Build project

We use [poetry](https://python-poetry.org/) for dependency management
and [Python Wraptor](https://github.com/houbie/python-wraptor) scripts to bootstrap tool installations.

Python 3.8+ needs to be on your path.

```shell
./pw poetry install
./pw test
```

## Deploy to AWS

The _cdk_ folder contains the CDK typescript code and config.

```shell
cd cdk
npm i
npm run build
# when using an AWS profile, add '--profile your-profile' to the deploy command
npx cdk deploy --all
```

This will output the URL where you can access the API Gateway.
Try to invoke the app (replace _your-api-gw_ and _region):
* https://{your-api-gw}.execute-api.{region}.amazonaws.com/prod/hello
* `curl -X POST -H "Content-Type: application/json" -d '{"foo":"bar"}' https://{your-api-gw}.execute-api.{region}.amazonaws.com/prod/s3-integration-event`
  * the data is stored in S3
  * check the cloudwatch logs of the _s3-integration-event-fn_ for the result


All generated infrastructure is within the (almost) free tier.

## Run locally

The Flask/Connexion app can be started with `./src/cdk_example_app/api_lambda.py`.
Then you can navigate to http://localhost:8080/hello

## Unit tests

The `test` folder contains the pytest unit tests.
Just run `poetry run pytest` or run tests in your IDE (you have to configure the project to use pytest in Intellij/Pycharm)

**NOTE**: _DynamoDBLocal_ will be downloaded when running the tests for the first time.

There are also unit tests for the CDK code:

```shell
cd cdk
npm test
```

## Cleanup

```shell
# when using an AWS profile, add '--profile your-profile' to the destroy command
npx cdk destroy
```

## Intellij / Pycharm

With the _AWS Toolkit_ plugin, you can view/update lambda's, S3 files, cloudwatch logs...
