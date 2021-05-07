import hashlib
import inspect
import os
import subprocess
from pathlib import Path

from aws_cdk import core, aws_lambda


class PythonStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        self.project_dir = os.path.dirname(inspect.getfile(self.__class__))
        super().__init__(scope, construct_id, **kwargs)
        self.lambda_layers = [self.create_dependencies_layer()]

    def create_dependencies_layer(self) -> aws_lambda.LayerVersion:
        layers_dir = Path(self.project_dir, '.layers')
        layers_dir.mkdir(exist_ok=True)
        requirements = subprocess.check_output(
            f'poetry export --with-credentials --without-hashes'.split()
        ).decode("utf-8")
        requirements = '\n'.join([line for line in requirements.splitlines() if not line.startswith('boto')])

        requirements_hash = hashlib.sha256(requirements.encode('utf-8')).hexdigest()
        destination_dir = layers_dir.joinpath(requirements_hash)
        if not destination_dir.exists():
            destination_dir.mkdir()
            requirements_file = destination_dir.joinpath('requirements.txt')
            with requirements_file.open('w') as f:
                f.write(requirements)
            print('running pip install...')
            subprocess.check_call(
                f'pip install --no-deps -r {requirements_file} -t {destination_dir}/python'.split())

        layer_id = f'{self.stack_name}-dependencies'
        layer_code = aws_lambda.Code.from_asset(str(destination_dir))

        return aws_lambda.LayerVersion(self, layer_id, code=layer_code)

    def code_asset(self, relative_path):
        """Turn a path relative to the project dir into a lambda code asset.
        This makes it possible to test stack creation from within the test dir"""
        return aws_lambda.Code.from_asset(os.path.join(self.project_dir, relative_path))
