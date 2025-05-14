#!/usr/bin/env python
from constructs import Construct
from cdktf import App, TerraformStack
from cdktf_cdktf_provider_aws.provider import AwsProvider
from cdktf_cdktf_provider_aws.default_vpc import DefaultVpc
from cdktf_cdktf_provider_aws.default_subnet import DefaultSubnet
from cdktf_cdktf_provider_aws.launch_template import LaunchTemplate
from cdktf_cdktf_provider_aws.lb import Lb
from cdktf_cdktf_provider_aws.lb_target_group import LbTargetGroup
from cdktf_cdktf_provider_aws.lb_listener import LbListener, LbListenerDefaultAction
from cdktf_cdktf_provider_aws.autoscaling_group import AutoscalingGroup
from cdktf_cdktf_provider_aws.security_group import SecurityGroup, SecurityGroupIngress, SecurityGroupEgress
from cdktf_cdktf_provider_aws.data_aws_caller_identity import DataAwsCallerIdentity
from main_serverless import ServerlessStack

import base64

# Mettez ici le nom du bucket S3 crée dans la partie serverless
bucket = ServerlessStack().bucket.bucket
# Mettez ici le nom de la table dynamoDB créée dans la partie serverless
dynamo_table="table"

# Mettez ici l'url de votre dépôt github. Votre dépôt doit être public !!!
your_repo="https://github.com/komodo-0/postagram_ensai#"

# Le user data pour lancer votre websservice. Il fonctionne tel quel
user_data= base64.b64encode(f"""#!/bin/bash
echo "userdata-start"        
apt update
apt install -y python3-pip python3.12-venv
git clone {your_repo} projet
cd projet/webservice
python3 -m venv venv
source venv/bin/activate
rm .env
echo 'BUCKET={bucket}' >> .env
echo 'DYNAMO_TABLE={dynamo_table}' >> .env
pip3 install -r requirements.txt
venv/bin/python app.py
echo "userdata-end""".encode("ascii")).decode("ascii")


class ServerStack(TerraformStack):
    
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

        account_id, security_group, subnets, default_vpc = self.infra_base()
        
        launch_template = LaunchTemplate(
            self, "launch template",
            image_id="ami-04b4f1a9cf54c11d0",
            instance_type="t2.micro",
            vpc_security_group_ids = [security_group.id],
            key_name="vockey",
            user_data=user_data,
            tags={"Name":"TP noté"},
            iam_instance_profile={"name":"LabInstanceProfile"}
            )
    

        lb = Lb(
            self, "lb",
            load_balancer_type= "application",
            security_groups= [security_group.id],
            subnets= subnets
        )

        target_group=LbTargetGroup(
            self, "tg_group",
            port= 8080,
            protocol= "HTTP", 
            vpc_id= default_vpc.id, 
            target_type="instance" 
        )

        lb_listener = LbListener(
            self, "lb_listener",
            load_balancer_arn= lb.arn, # l'arn (un identifiant amazon différent de l'id) du load balancer
            port= 80, #le port écouté par le LB
            protocol= "HTTP", #le protocole écouté par le LB
            default_action= [LbListenerDefaultAction(type="forward", 
                                                    target_group_arn=target_group.arn)
            ])

        asg = AutoscalingGroup(
            self, "asg",
            min_size=1, # taille minimum
            max_size=2, # taille maximum
            desired_capacity=1, # taille au debut
            launch_template={"id": launch_template.id}, # un dictionnaire avec la clé id et en valeur l'id du launch template
            vpc_zone_identifier= subnets,  # la liste des subnets
            target_group_arns= [target_group.arn]
        )

    def infra_base(self):
        """
        Permet de définir une infra de base, vous ne devez pas y toucher !
        """
        AwsProvider(self, "AWS", region="us-east-1")
        account_id = DataAwsCallerIdentity(self, "account_id").account_id

        default_vpc = DefaultVpc(
            self, "default_vpc"
        )
            
        # Les AZ de us-east-1 sont de la forme us-east-1x 
        # avec x une lettre dans abcdef. Ne permet pas de déployer
        # automatiquement ce code sur une autre région. Le code
        # pour y arriver est vraiment compliqué.
        az_ids = [f"us-east-1{i}" for i in "abcdef"]
        subnets= []
        for i,az_id in enumerate(az_ids):
            subnets.append(DefaultSubnet(
            self, f"default_sub{i}",
            availability_zone=az_id
        ).id)
            

        security_group = SecurityGroup(
            self, "sg-tp",
            ingress=[
                SecurityGroupIngress(
                    from_port=22,
                    to_port=22,
                    cidr_blocks=["0.0.0.0/0"],
                    protocol="TCP",
                ),
                SecurityGroupIngress(
                    from_port=80,
                    to_port=80,
                    cidr_blocks=["0.0.0.0/0"],
                    protocol="TCP"
                ),
                SecurityGroupIngress(
                    from_port=8080,
                    to_port=8080,
                    cidr_blocks=["0.0.0.0/0"],
                    protocol="TCP"
                )
            ],
            egress=[
                SecurityGroupEgress(
                    from_port=0,
                    to_port=0,
                    cidr_blocks=["0.0.0.0/0"],
                    protocol="-1"
                )
            ]
            )
        return account_id, security_group, subnets, default_vpc

app = App()
ServerStack(app, "cdktf_server")
app.synth()
