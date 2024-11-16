import aws_cdk as core
import aws_cdk.assertions as assertions

from ingestion_app_cdk.ingestion_app_cdk_stack import IngestionAppCdkStack

# example tests. To run these tests, uncomment this file along with the example
# resource in ingestion_app_cdk/ingestion_app_cdk_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = IngestionAppCdkStack(app, "ingestion-app-cdk")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
