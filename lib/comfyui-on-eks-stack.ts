import * as cdk from 'aws-cdk-lib';
import * as ec2 from "aws-cdk-lib/aws-ec2";
import { CapacityType, KubernetesManifest, KubernetesVersion, NodegroupAmiType } from 'aws-cdk-lib/aws-eks';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as kms from 'aws-cdk-lib/aws-kms';
import { Construct } from "constructs";
import * as blueprints from '@aws-quickstart/eks-blueprints';


const stackName = 'Comfyui-Cluster';

export interface BlueprintConstructProps { id: string }

export default class BlueprintConstruct {
    constructor(scope: Construct, props: cdk.StackProps) {

        // Instance profiles of K8S node EC2
        const nodeRole = new blueprints.CreateRoleProvider("blueprint-node-role", new iam.ServicePrincipal("ec2.amazonaws.com"),
            [
                iam.ManagedPolicy.fromAwsManagedPolicyName("AmazonEKS_CNI_Policy"),
                iam.ManagedPolicy.fromAwsManagedPolicyName("AmazonEKSWorkerNodePolicy"),
                iam.ManagedPolicy.fromAwsManagedPolicyName("AmazonEC2ContainerRegistryReadOnly"),
                iam.ManagedPolicy.fromAwsManagedPolicyName("AmazonSSMManagedInstanceCore"),
                iam.ManagedPolicy.fromAwsManagedPolicyName("AmazonS3FullAccess")
            ]);

        const clusterProvider = new blueprints.GenericClusterProvider({
            version: KubernetesVersion.V1_30,
            tags: {
                "Name": "comfyui-eks-cluster",
                "Type": "generic-cluster"
            },
            mastersRole: blueprints.getResource(context => {
                return new iam.Role(context.scope, 'AdminRole', { assumedBy: new iam.AccountRootPrincipal() });
            }),
            managedNodeGroups: [
                addLightWeightNodeGroup()
            ]
        });

        const stack = blueprints.EksBlueprint.builder()
            .addOns(
                new blueprints.addons.AwsLoadBalancerControllerAddOn(),
                new blueprints.addons.SSMAgentAddOn(),
                new blueprints.addons.KedaAddOn({
                    namespace: 'keda',
                    version: '2.11.0',
                    values: {
                        podSecurityContextFsGroup: 1001,
                        securityContextRunAsGroup: 1001,
                        securityContextRunAsUser: 1001,
                        serviceAccount: {
                            create: false,
                            name: 'keda-operator',
                        },
                    }
                }),
                new blueprints.addons.KarpenterAddOn({
                    version: 'v0.34.5',
                    values: { replicas: 1 },
                }),
                new blueprints.GpuOperatorAddon({
                    values: {
                        driver: { enabled: true },
                        mig: { strategy: 'mixed' },
                        devicePlugin: { enabled: true, version: 'v0.13.0' },
                        migManager: { enabled: true, WITH_REBOOT: true },
                        toolkit: { version: 'v1.13.1-centos7' },
                        operator: { defaultRuntime: 'containerd' },
                        gfd: { version: 'v0.8.0' }
                    }
                }))
            .resourceProvider(
                blueprints.GlobalResources.Vpc,
                new blueprints.VpcProvider(undefined, {
                    primaryCidr: "10.2.0.0/16",
                    secondaryCidr: "100.64.0.0/16",
                    secondarySubnetCidrs: ["100.64.0.0/24", "100.64.1.0/24", "100.64.2.0/24"]
                }))
            .resourceProvider("node-role", nodeRole)
            .clusterProvider(clusterProvider)
            .teams()
            .build(scope, stackName, props);

        // Define IAM policy for SQS
        const sqsPolicy = new iam.PolicyStatement({
            effect: iam.Effect.ALLOW,
            actions: [
                "sqs:ReceiveMessage",
                "sqs:DeleteMessage",
                "sqs:GetQueueAttributes"
            ],
            resources: ["arn:aws:sqs:eu-west-2:339712991492:wedgwood-ai-staging-queue"],
        });

        const s3Policy = new iam.PolicyStatement({
            effect: iam.Effect.ALLOW,
            actions: [
                "s3:GetObject",
                "s3:PutObject",
                "s3:ListBucket"
            ],
            resources: [
                "arn:aws:s3:::comfyui-outputs-339712991492-eu-west-2",
                "arn:aws:s3:::comfyui-outputs-339712991492-eu-west-2/*",
                "arn:aws:s3:::comfyui-inputs-339712991492-eu-west-2",
                "arn:aws:s3:::comfyui-inputs-339712991492-eu-west-2/*"
            ],
        });

        // Create a ServiceAccount for KEDA with IRSA
        const kedaServiceAccount = stack.getClusterInfo().cluster.addServiceAccount('KedaOperatorServiceAccount', {
            name: 'keda-operator',
            namespace: 'keda',
        });

        const comfyuiServiceAccount = stack.getClusterInfo().cluster.addServiceAccount('ComfyuiServiceAccount', {
            name: 'comfyui-sa',
            namespace: 'default',
        });

        // Attach the SQS policy to the ServiceAccount's role
        comfyuiServiceAccount.addToPrincipalPolicy(sqsPolicy);
        comfyuiServiceAccount.addToPrincipalPolicy(s3Policy);
        // Modify the trust relationship to allow kedaServiceAccount to assume the comfyuiServiceAccount role
        (comfyuiServiceAccount.role as iam.Role).assumeRolePolicy?.addStatements(
            new iam.PolicyStatement({
                effect: iam.Effect.ALLOW,
                actions: ["sts:AssumeRole"],
                principals: [new iam.ArnPrincipal(kedaServiceAccount.role.roleArn)],
            })
        );

        // Add permissions to KEDA service account
        kedaServiceAccount.addToPrincipalPolicy(new iam.PolicyStatement({
            effect: iam.Effect.ALLOW,
            actions: ["sts:AssumeRole"],
            resources: [comfyuiServiceAccount.role.roleArn],
        }));
    }
}

// Node Group for lightweight workloads
function addLightWeightNodeGroup(): blueprints.ManagedNodeGroup {
    return {
        id: "AL2-MNG-LW",
        amiType: NodegroupAmiType.AL2_X86_64,
        instanceTypes: [new ec2.InstanceType('t3a.xlarge')],
        nodeRole: blueprints.getNamedResource("node-role") as iam.Role,
        minSize: 0,
        desiredSize: 1,
        maxSize: 3,
        nodeGroupSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
        launchTemplate: {
            tags: {
                "Name": "Comfyui-EKS-LW-Node",
            }
        }
    };
}
