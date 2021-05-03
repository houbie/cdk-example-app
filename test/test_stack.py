from aws_cdk import core


def get_template():
    print('get_template')
    from stack import CdkStack
    app = core.App()
    CdkStack(app, "cdk-example-app")
    return app.synth().get_stack("cdk-example-app").template


def search_resource(key_prefix, type):
    resources = get_template()['Resources']
    result = [resources[key] for key in resources.keys() if
              key.startswith(key_prefix) and resources[key]['Type'] == type]
    return result[0] if result else None


def test_hello_lambda_created():
    assert search_resource('HelloHandler', 'AWS::Lambda::Function')


def test_api_gw_created():
    assert search_resource('CdkExampleApi', 'AWS::ApiGateway::RestApi')
