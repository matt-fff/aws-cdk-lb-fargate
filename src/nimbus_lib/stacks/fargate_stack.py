# pylint: disable=unused-argument
from typing import Any, Generic, TypeVar
from constructs import Construct
from aws_cdk import (
    Fn,
    CfnOutput,
    Duration,
    Stack,
    aws_certificatemanager as acm,
    aws_route53 as route53,
    aws_route53_targets as route53_targets,
    aws_efs as efs,
    aws_ec2 as ec2,
    aws_ecr as ecr,
    aws_ecs as ecs,
    aws_iam as iam,
    aws_elasticloadbalancingv2 as elbv2,
)
from nimbus_lib import configs as conf

# pylint: disable=invalid-name
TConfig = TypeVar("TConfig", bound=conf.FargateConfig)


class FargateStack(Stack, Generic[TConfig]):
    @property
    def _base_name(self) -> str:
        return self.construct_id

    def _name(self, suffix: str = "", prefix: str = "") -> str:
        return "".join(
            [
                part[0].upper() + part[1:]
                for part in f"{prefix} {self._base_name} {suffix}".split()
            ]
        )

    def __init__(
        self,
        scope: Construct,
        config: TConfig,
        **kwargs,
    ) -> None:
        self.construct_id = config.construct_id
        super().__init__(scope, self.construct_id, **kwargs)

        vpc = self.vpc(config.vpc_id)
        fargate = self.fargate(config, vpc)
        self.setup_scaling(config, fargate)

        load_balancer = self.load_balancer(config, vpc)
        certs = self.setup_domains(load_balancer, config.domains, vpc)
        self.setup_listeners(
            config,
            load_balancer,
            certs,
            fargate,
        )

        CfnOutput(
            self,
            self._name("LoadBalancerDNS"),
            value=load_balancer.load_balancer_dns_name,
        )

    def vpc(self, vpc_id: str | None) -> ec2.IVpc:
        if vpc_id is not None:
            return ec2.Vpc.from_lookup(
                self,
                self._name("VPC"),
                vpc_id=vpc_id,
            )

        azs = Fn.get_azs()
        return ec2.Vpc(self, self._name("VPC"), availability_zones=azs)

    def setup_container(
        self,
        config: TConfig,
        taskdef: ecs.FargateTaskDefinition,
    ) -> ecs.ContainerDefinition:
        command = None
        if config.container.command:
            command = config.container.command.split(" ")

        container = taskdef.add_container(
            self._name("TaskContainer"),
            image=self.container_image(config.container),
            environment=self.image_environment(config),
            secrets=self.image_secrets(config),
            command=command,
        )
        container.add_port_mappings(
            ecs.PortMapping(container_port=config.container.port)
        )

        return container

    def efs_filesystem(
        self,
        vpc: ec2.IVpc,
        fargate_sg: ec2.SecurityGroup,
    ) -> efs.FileSystem:
        filesys_sg = ec2.SecurityGroup(
            self,
            self._name("FileSystemSecGrp"),
            vpc=vpc,
        )
        filesys_sg.add_ingress_rule(
            fargate_sg,
            ec2.Port.tcp(2049),
        )

        # Create an EFS file system
        file_system = efs.FileSystem(
            self,
            self._name("FileSystem"),
            vpc=vpc,
            performance_mode=efs.PerformanceMode.GENERAL_PURPOSE,
            security_group=filesys_sg,
        )

        return file_system

    def setup_container_volumes(
        self,
        config: TConfig,
        taskdef: ecs.FargateTaskDefinition,
        container: ecs.ContainerDefinition,
        file_system: efs.FileSystem,
    ) -> None:
        # Create all volumes and corresponding mount points
        for idx, container_path in enumerate(config.container.volumes):
            volume_name = f"vol-{idx}"
            taskdef.add_volume(
                name=volume_name,
                efs_volume_configuration=ecs.EfsVolumeConfiguration(
                    file_system_id=file_system.file_system_id,
                    transit_encryption="ENABLED",
                ),
            )
            container.add_mount_points(
                ecs.MountPoint(
                    source_volume=volume_name,
                    read_only=False,
                    container_path=container_path,
                )
            )

    def task_definition(
        self, config: TConfig, vpc: ec2.IVpc, fargate_sg: ec2.SecurityGroup
    ) -> ecs.FargateTaskDefinition:
        taskdef = ecs.FargateTaskDefinition(
            self,
            self._name("FargateTaskDef"),
            # Pyright ignore is necessary due to inconsistencies in
            # parameter naming ("grantee" vs "identity"), not types.
            task_role=self.task_role(config),  # pyright: ignore
            execution_role=self.task_execution_role(config),  # pyright: ignore
        )

        container = self.setup_container(config, taskdef)
        if config.use_efs:
            file_system = self.efs_filesystem(vpc, fargate_sg)
            self.setup_container_volumes(
                config, taskdef, container, file_system
            )

        return taskdef

    def container_image(
        self, config: conf.ContainerConfig
    ) -> ecs.ContainerImage:
        if config.source == conf.ContainerImageSource.ECR:
            container_repo = ecr.Repository.from_repository_name(
                self, self._name("Repo"), config.image
            )

            return ecs.ContainerImage.from_ecr_repository(
                container_repo, tag=config.tag
            )
        if config.source == conf.ContainerImageSource.REGISTRY:
            return ecs.ContainerImage.from_registry(
                f"{config.image}:{config.tag}"
            )

        raise NotImplementedError(
            f"Unimplemented image source: {config.source}"
        )

    def image_environment(self, config: TConfig) -> dict[str, Any]:
        return {}

    def image_secrets(self, config: TConfig) -> dict[str, Any]:
        return {}

    def task_role(self, config: TConfig) -> iam.Role:
        # Setup role permissions
        return iam.Role(
            self,
            self._name("TaskRole"),
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )

    def task_execution_role(self, config: TConfig) -> iam.Role:
        # Setup role permissions
        role = iam.Role(
            self,
            self._name("TaskExecutionRole"),
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )

        # Add necessary permissions to the IAM role
        role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "service-role/AmazonECSTaskExecutionRolePolicy"
            )
        )

        if config.use_efs:
            role.add_to_policy(
                iam.PolicyStatement(
                    actions=[
                        "elasticfilesystem:CreateMountTarget",
                    ],
                    resources=["*"],  # TODO get more specific
                )
            )

        return role

    def fargate(self, config: TConfig, vpc: ec2.IVpc) -> ecs.FargateService:
        #
        # SETUP THE FARGATE SERVICE
        #

        cluster = ecs.Cluster(self, self._name("Cluster"), vpc=vpc)

        # Create Fargate Service

        fargate_ingress_sg, fargate_egress_sg = self.fargate_security_groups(
            config, vpc
        )
        fargate = ecs.FargateService(
            self,
            self._name("FargateService"),
            cluster=cluster,
            task_definition=self.task_definition(
                config, vpc, fargate_egress_sg
            ),
            security_groups=[fargate_ingress_sg, fargate_egress_sg],
        )

        return fargate

    def setup_domains(
        self,
        load_balancer: elbv2.ApplicationLoadBalancer,
        domains: list[conf.DomainConfig],
        vpc: ec2.IVpc,
    ) -> list[acm.ICertificate]:
        certs = []
        # Setup certificates and zones
        for domain in domains:
            # Retrieve Route53 Alias Record to point to the Load Balancer
            zone_name = self._name(f"{domain.name}HostedZone")

            if domain.zone_exists:
                hosted_zone = route53.HostedZone.from_lookup(
                    self,
                    zone_name,
                    domain_name=domain.domain,
                    private_zone=domain.private_zone,
                    vpc_id=vpc.vpc_id if domain.private_zone else None,
                )
            else:
                hosted_zone = route53.HostedZone(
                    self,
                    zone_name,
                    zone_name=domain.domain,
                    vpcs=[vpc] if domain.private_zone else [],
                )

            cert_name = self._name(f"{domain.name}Cert")
            certificate = acm.Certificate(
                self,
                cert_name,
                domain_name=domain.name,
                validation=acm.CertificateValidation.from_dns(hosted_zone),
            )
            certs.append(certificate)

            route53.ARecord(
                self,
                self._name(f"{domain.name}ARecord"),
                zone=hosted_zone,
                record_name=domain.name,
                target=route53.RecordTarget.from_alias(
                    route53_targets.LoadBalancerTarget(load_balancer)
                ),
            )

        return certs

    def setup_scaling(
        self, config: TConfig, fargate: ecs.FargateService
    ) -> None:
        # Setup AutoScaling policy
        scaling = fargate.auto_scale_task_count(
            max_capacity=config.scaling.max_task_count
        )
        scaling.scale_on_cpu_utilization(
            self._name("CpuScaling"),
            target_utilization_percent=config.scaling.target_cpu_util_pct,
            scale_in_cooldown=Duration.seconds(60),
            scale_out_cooldown=Duration.seconds(60),
        )

    def setup_listeners(
        self,
        config: TConfig,
        load_balancer: elbv2.ApplicationLoadBalancer,
        certs: list[acm.ICertificate],
        fargate: ecs.FargateService,
    ):
        for port in config.external_ports:
            listener_name = f"Listener{port}"
            listener = load_balancer.add_listener(
                self._name(listener_name), port=port
            )
            listener.add_targets(
                f"{listener_name}Target",
                port=config.container.port,  # HTTPS terminates at the balancer
                targets=[fargate],
            )

            if port == config.external_https_port:
                listener.add_certificates(
                    self._name(f"{listener_name}Certs"), certs
                )
            # TODO healthcheck

    def load_balancer(
        self, config: TConfig, vpc: ec2.IVpc
    ) -> elbv2.ApplicationLoadBalancer:
        # Create a Security Group for the Load Balancer
        lb_security_group = ec2.SecurityGroup(
            self, self._name("LBSecGrp"), vpc=vpc
        )

        for port in config.external_ports:
            lb_security_group.add_ingress_rule(
                ec2.Peer.ipv4(vpc.vpc_cidr_block),
                ec2.Port.tcp(port),
                "Allow http inbound from VPC",
            )

            # If specified, allow access from this IP.
            for ip_address in config.ip_allowlist:
                lb_security_group.add_ingress_rule(
                    ec2.Peer.ipv4(ip_address),
                    ec2.Port.tcp(port),
                    "developer access",
                )
            # If specified, allow access from the entire internet
            if config.public_access:
                lb_security_group.add_ingress_rule(
                    ec2.Peer.any_ipv4(),
                    ec2.Port.tcp(port),
                    "unrestricted internet access",
                )

        # Create a Application Load Balancer
        load_balancer = elbv2.ApplicationLoadBalancer(
            self,
            self._name("LoadBalancer"),
            vpc=vpc,
            internet_facing=True,
            security_group=lb_security_group,
        )

        return load_balancer

    def fargate_security_groups(
        self, config: TConfig, vpc: ec2.IVpc
    ) -> tuple[ec2.SecurityGroup, ec2.SecurityGroup]:
        #
        # SECURITY GROUPS AND NETWORKING
        #

        # Setup incoming access
        ingress_sec_group = ec2.SecurityGroup(
            self,
            self._name("FargateIngressSecGrp"),
            vpc=vpc,
            description=(
                "Security group to link to other AWS resource security groups"
            ),
        )
        ingress_sec_group.add_ingress_rule(
            ec2.Peer.ipv4(vpc.vpc_cidr_block),
            ec2.Port.tcp(config.container.port),
            "Allow http inbound from VPC",
        )

        # Setup access to AWS resources
        egress_sec_group = ec2.SecurityGroup(
            self,
            self._name("FargateEgressSecGrp"),
            vpc=vpc,
            description=(
                "Security group to link to other AWS resource security groups"
            ),
        )

        # Give fargate access to all of the ingress configurations
        for idx, ingress in enumerate(config.ingress_confs):
            conf_security_group = ec2.SecurityGroup.from_security_group_id(
                self,
                self._name(f"IngressSecGrp{idx}"),
                security_group_id=ingress.security_group_id,
            )
            conf_security_group.add_ingress_rule(
                egress_sec_group,
                ec2.Port.tcp(ingress.port),
            )

        return ingress_sec_group, egress_sec_group
