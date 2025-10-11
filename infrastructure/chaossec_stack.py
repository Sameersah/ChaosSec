"""AWS CDK stack definition for ChaosSec infrastructure."""

from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_logs as logs,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    aws_events as events,
    aws_events_targets as targets,
    aws_fis as fis,
)
from constructs import Construct


class ChaosSecStack(Stack):
    """CDK Stack for ChaosSec autonomous chaos and security agent."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ============================================================
        # Storage Resources
        # ============================================================
        
        # S3 Bucket for logs and evidence
        self.logs_bucket = s3.Bucket(
            self,
            "ChaosSecLogsBucket",
            bucket_name=f"chaossec-logs-{self.account}-{self.region}",
            encryption=s3.BucketEncryption.S3_MANAGED,
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN,
            lifecycle_rules=[
                s3.LifecycleRule(
                    expiration=Duration.days(90),
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INTELLIGENT_TIERING,
                            transition_after=Duration.days(30)
                        )
                    ]
                )
            ]
        )
        
        # DynamoDB Table for execution history
        self.history_table = dynamodb.Table(
            self,
            "ChaosSecHistoryTable",
            table_name="chaossec-execution-history",
            partition_key=dynamodb.Attribute(
                name="correlation_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True
        )
        
        # DynamoDB Table for compliance evidence
        self.evidence_table = dynamodb.Table(
            self,
            "ChaosSecEvidenceTable",
            table_name="chaossec-compliance-evidence",
            partition_key=dynamodb.Attribute(
                name="evidence_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="control_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN
        )
        
        # ============================================================
        # IAM Roles
        # ============================================================
        
        # Lambda execution role
        self.lambda_role = iam.Role(
            self,
            "ChaosSecLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )
        
        # Add permissions to Lambda role
        self.lambda_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "fis:StartExperiment",
                "fis:GetExperiment",
                "fis:ListExperiments",
                "fis:StopExperiment"
            ],
            resources=["*"]
        ))
        
        self.lambda_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "cloudwatch:GetMetricStatistics",
                "cloudwatch:ListMetrics",
                "cloudwatch:PutMetricData"
            ],
            resources=["*"]
        ))
        
        self.lambda_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "config:DescribeComplianceByResource",
                "config:GetComplianceDetailsByResource"
            ],
            resources=["*"]
        ))
        
        self.lambda_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "cloudtrail:LookupEvents"
            ],
            resources=["*"]
        ))
        
        self.lambda_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "bedrock:InvokeModel",
                "bedrock-runtime:InvokeModel"
            ],
            resources=["*"]
        ))
        
        self.lambda_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "s3:GetObject",
                "s3:PutObject",
                "s3:GetBucketAcl",
                "s3:PutBucketAcl",
                "s3:GetPublicAccessBlock",
                "s3:PutPublicAccessBlock",
                "s3:DeletePublicAccessBlock"
            ],
            resources=[
                self.logs_bucket.bucket_arn,
                f"{self.logs_bucket.bucket_arn}/*"
            ]
        ))
        
        # Grant DynamoDB access
        self.history_table.grant_read_write_data(self.lambda_role)
        self.evidence_table.grant_read_write_data(self.lambda_role)
        
        # FIS service role
        self.fis_role = iam.Role(
            self,
            "ChaosSecFISRole",
            assumed_by=iam.ServicePrincipal("fis.amazonaws.com"),
        )
        
        self.fis_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "s3:*",
                "ec2:*",
                "rds:*"
            ],
            resources=["*"]
        ))
        
        # ============================================================
        # Lambda Functions
        # ============================================================
        
        # Lambda Layer with dependencies
        self.chaossec_layer = lambda_.LayerVersion(
            self,
            "ChaosSecLayer",
            code=lambda_.Code.from_asset("../src"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_11],
            description="ChaosSec core modules"
        )
        
        # Orchestrator Lambda
        self.orchestrator_lambda = lambda_.Function(
            self,
            "OrchestratorLambda",
            function_name="chaossec-orchestrator",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="lambda_handlers.orchestrator_handler.handler",
            code=lambda_.Code.from_asset("../src"),
            role=self.lambda_role,
            timeout=Duration.minutes(15),
            memory_size=512,
            environment={
                "HISTORY_TABLE": self.history_table.table_name,
                "EVIDENCE_TABLE": self.evidence_table.table_name,
                "LOGS_BUCKET": self.logs_bucket.bucket_name,
                "CHAOSSEC_SAFETY_MODE": "true"
            },
            layers=[self.chaossec_layer]
        )
        
        # Chaos Executor Lambda
        self.chaos_executor_lambda = lambda_.Function(
            self,
            "ChaosExecutorLambda",
            function_name="chaossec-chaos-executor",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="lambda_handlers.chaos_executor_handler.handler",
            code=lambda_.Code.from_asset("../src"),
            role=self.lambda_role,
            timeout=Duration.minutes(10),
            memory_size=256,
            environment={
                "LOGS_BUCKET": self.logs_bucket.bucket_name
            }
        )
        
        # Scanner Lambda
        self.scanner_lambda = lambda_.Function(
            self,
            "ScannerLambda",
            function_name="chaossec-scanner",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="lambda_handlers.scanner_handler.handler",
            code=lambda_.Code.from_asset("../src"),
            role=self.lambda_role,
            timeout=Duration.minutes(10),
            memory_size=1024,
            environment={
                "LOGS_BUCKET": self.logs_bucket.bucket_name
            }
        )
        
        # Reporter Lambda
        self.reporter_lambda = lambda_.Function(
            self,
            "ReporterLambda",
            function_name="chaossec-reporter",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="lambda_handlers.reporter_handler.handler",
            code=lambda_.Code.from_asset("../src"),
            role=self.lambda_role,
            timeout=Duration.minutes(5),
            memory_size=256,
            environment={
                "EVIDENCE_TABLE": self.evidence_table.table_name,
                "LOGS_BUCKET": self.logs_bucket.bucket_name
            }
        )
        
        # ============================================================
        # Step Functions State Machine
        # ============================================================
        
        # Define tasks
        simulate_task = tasks.LambdaInvoke(
            self,
            "SimulateTask",
            lambda_function=self.orchestrator_lambda,
            payload=sfn.TaskInput.from_object({"step": "simulate"}),
            result_path="$.simulate_result"
        )
        
        scan_task = tasks.LambdaInvoke(
            self,
            "ScanTask",
            lambda_function=self.scanner_lambda,
            payload=sfn.TaskInput.from_object({"step": "scan"}),
            result_path="$.scan_result"
        )
        
        reason_task = tasks.LambdaInvoke(
            self,
            "ReasonTask",
            lambda_function=self.orchestrator_lambda,
            payload=sfn.TaskInput.from_object({"step": "reason"}),
            result_path="$.reason_result"
        )
        
        chaos_task = tasks.LambdaInvoke(
            self,
            "ChaosTask",
            lambda_function=self.chaos_executor_lambda,
            result_path="$.chaos_result"
        )
        
        monitor_task = tasks.LambdaInvoke(
            self,
            "MonitorTask",
            lambda_function=self.orchestrator_lambda,
            payload=sfn.TaskInput.from_object({"step": "monitor"}),
            result_path="$.monitor_result"
        )
        
        validate_task = tasks.LambdaInvoke(
            self,
            "ValidateTask",
            lambda_function=self.orchestrator_lambda,
            payload=sfn.TaskInput.from_object({"step": "validate"}),
            result_path="$.validate_result"
        )
        
        report_task = tasks.LambdaInvoke(
            self,
            "ReportTask",
            lambda_function=self.reporter_lambda,
            result_path="$.report_result"
        )
        
        learn_task = tasks.LambdaInvoke(
            self,
            "LearnTask",
            lambda_function=self.orchestrator_lambda,
            payload=sfn.TaskInput.from_object({"step": "learn"}),
            result_path="$.learn_result"
        )
        
        # Define workflow
        definition = simulate_task \
            .next(scan_task) \
            .next(reason_task) \
            .next(chaos_task) \
            .next(monitor_task) \
            .next(validate_task) \
            .next(report_task) \
            .next(learn_task)
        
        # Create state machine
        self.state_machine = sfn.StateMachine(
            self,
            "ChaosSecStateMachine",
            state_machine_name="chaossec-workflow",
            definition=definition,
            timeout=Duration.hours(1)
        )
        
        # ============================================================
        # EventBridge Rules
        # ============================================================
        
        # Scheduled execution (daily)
        events.Rule(
            self,
            "ChaosSecScheduleRule",
            schedule=events.Schedule.rate(Duration.days(1)),
            targets=[targets.SfnStateMachine(self.state_machine)]
        )
        
        # ============================================================
        # FIS Experiment Templates
        # ============================================================
        
        # S3 Public Access Experiment Template
        cfn_experiment_template = fis.CfnExperimentTemplate(
            self,
            "S3PublicAccessTemplate",
            description="ChaosSec: Test S3 public access detection",
            role_arn=self.fis_role.role_arn,
            stop_conditions=[
                fis.CfnExperimentTemplate.ExperimentTemplateStopConditionProperty(
                    source="none"
                )
            ],
            targets={
                "s3-buckets": fis.CfnExperimentTemplate.ExperimentTemplateTargetProperty(
                    resource_type="aws:s3:bucket",
                    selection_mode="ALL",
                    resource_tags={"chaossec": "test"}
                )
            },
            actions={
                "modify-bucket-acl": fis.CfnExperimentTemplate.ExperimentTemplateActionProperty(
                    action_id="aws:s3:bucket-pause-replication",
                    description="Test S3 security controls"
                )
            },
            tags={"Name": "chaossec-s3-public-test", "ManagedBy": "ChaosSec"}
        )

