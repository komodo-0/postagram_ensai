
import pytest
from cdktf import Testing
from main import MyStack

class TestMain:

    def setup_method(self):
        self.app = Testing.app()
        self.stack = MyStack(self.app, "test")
        self.synthesized = Testing.synth(self.stack)

    def test_should_be_valid_terraform(self):
        assert Testing.to_be_valid_terraform(self.synthesized)

    def test_should_contain_s3_bucket(self):
        assert Testing.to_have_resource(self.synthesized, "aws_s3_bucket")

    def test_should_contain_dynamodb_table(self):
        assert Testing.to_have_resource(self.synthesized, "aws_dynamodb_table")

    def test_should_contain_launch_template(self):
        assert Testing.to_have_resource(self.synthesized, "aws_launch_template")

    def test_should_contain_load_balancer(self):
        assert Testing.to_have_resource(self.synthesized, "aws_lb")

