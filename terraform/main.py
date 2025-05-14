#!/usr/bin/env python
from constructs import Construct
from cdktf import App, TerraformStack
from main_server import ServerStack
from main_serverless import ServerlessStack


class MyStack(TerraformStack):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

        ServerlessStack(scope, f"{id}-serverless")
        ServerStack(scope, f"{id}-server")


app = App()
MyStack(app, "terraform")

app.synth()
