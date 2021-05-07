from aws_cdk import core


def get_template():
    from app import ApplicationStack
    app = core.App()
    ApplicationStack(app, "cdk-example-app")
    return app.synth().get_stack("cdk-example-app").template


def search_resource(resources, key_prefix, type):
    result = [resources[key] for key in resources.keys() if
              key.startswith(key_prefix) and resources[key]['Type'] == type]
    return result[0] if result else None


def test_hello_lambda_created():
    resources = get_template()['Resources']
    assert search_resource(resources, 'HelloHandler', 'AWS::Lambda::Function')
    assert search_resource(resources, 'CdkExampleApi', 'AWS::ApiGateway::RestApi')
