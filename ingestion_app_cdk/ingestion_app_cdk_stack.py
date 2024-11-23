from aws_cdk import Stack, RemovalPolicy
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3_notifications as s3n
from aws_cdk import aws_ec2 as ec2
from constructs import Construct

class IngestionAppCdkStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create the VPC once and reuse it
        vpc = self.create_vpc()

        # S3 Bucket for uploading HR files
        bucket = s3.Bucket(self, "HRDocumentsS3Bucket",
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # EC2 Instance Role
        ec2_role = iam.Role(self, "EC2S3AccessRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("CloudWatchFullAccess")
            ]
        )

        # EC2 Security Group with SSH ingress rule
        ec2_sg = ec2.SecurityGroup(self, "HREC2SecurityGroup",
            vpc=vpc,
            allow_all_outbound=True
        )
#         ec2_sg.add_ingress_rule(
#             ec2.Peer.any_ipv4(),
#             ec2.Port.tcp(22),
#             "Allow SSH access from anywhere"
#         )

        # EC2 Instance with SSM
        ec2_instance = ec2.Instance(
            self,
            "HRFileProcessingInstance",
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.T2,
                ec2.InstanceSize.MICRO
            ),
            machine_image=ec2.MachineImage.latest_amazon_linux2023(),
            vpc=vpc,
            key_name="AS-RAG",
            security_group=ec2_sg,
            role=iam.Role(
                self,
                "SSMRole",
                assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
                managed_policies=[
                    iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore")
                ]
            ),
        )
        # EC2 with ssh
#         ec2_instance = ec2.Instance(
#             self,
#             "HRFileProcessingInstance",
#             instance_type=ec2.InstanceType.of(
#                 ec2.InstanceClass.T2,
#                 ec2.InstanceSize.MICRO
#             ),
#             machine_image=ec2.MachineImage.latest_amazon_linux(),
#             vpc=vpc,
#             vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),  # Ensures public subnet
#             security_group=ec2_sg,
#             key_name="AS-RAG",  # Replace with your actual key pair name
#             role=ec2_role
#         )

        # Lambda function to process files
        process_files_lambda = _lambda.Function(
            self,
            "HRIngestionBatch",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="ingestion_batch.handler",  # Ensure this matches the correct function inside ingestion_batch.py
            code=_lambda.Code.from_asset("lambda/process_files"),
            environment={
                "BUCKET_NAME": bucket.bucket_name,
                "INSTANCE_ID": ec2_instance.instance_id,
                "TARGET_DIRECTORY": "/home/ec2-user/ingested_files"
            }
        )

        # Add IAM policy to the Lambda's role
        process_files_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["ssm:StartSession", "ssm:SendCommand"],
                resources=["*"]
            )
        )


        # Grant Lambda access to S3 bucket
        bucket.grant_read_write(process_files_lambda)

        # Notify Lambda on file upload to S3
        bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(process_files_lambda)
        )

        # Grant EC2 access to S3 bucket
        bucket.grant_read_write(ec2_instance.role)

    def create_vpc(self):
        return ec2.Vpc(self, "HR_VPC", max_azs=2)
