import pulumi
import pulumi_aws as aws

import requests

template = """{
    "AWSTemplateFormatVersion": "2010-09-09",
    "Description": "Lacework AWS Config Security Audit Integration (Member Accounts)",
    "Parameters": {
        "ResourceNamePrefix": {
            "Default": "customerdemo",
            "Description": "Names of resources created by the stack will be prefixed with this value to ensure uniqueness.",
            "Type": "String",
            "MinLength": "1",
            "MaxLength": "45",
            "AllowedPattern": "^[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*$",
            "ConstraintDescription": "Invalid resource name prefix.  Must match pattern ^[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*$"
        },
        "ExternalID": {
            "Default": "4CEBE3B",
            "Description": "The cross-account access role created by the stack will use this value for its ExternalID.",
            "Type": "String",
            "MinLength": "2",
            "MaxLength": "1224"
        },
        "AccessToken": {
            "Default": "4CEBE3B",
            "Description": "Access token used by this stack template.",
            "Type": "String",
            "MinLength": "2",
            "MaxLength": "1224"
        },
        "ServiceToken": {
            "Default": "arn:aws:sns:us-west-2::434813966438:prodn-customer-cloudformation",
            "Description": "Access token used by this stack template.",
            "Type": "String",
            "MinLength": "2",
            "MaxLength": "1224"
        }
    },
    "Resources": {
        "LaceworkCrossAccountAccessRole": {
            "Type": "AWS::IAM::Role",
            "Properties": {
                "RoleName": {
                    "Fn::Join": [
                        "-",
                        [
                            {
                                "Ref": "ResourceNamePrefix"
                            },
                            "laceworkcwsrole-sa"
                        ]
                    ]
                },
                "AssumeRolePolicyDocument": {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Action": "sts:AssumeRole",
                            "Effect": "Allow",
                            "Principal": {
                                "AWS": {
                                    "Fn::Join": [
                                        "",
                                        [
                                            "arn:aws:iam::",
                                            "434813966438",
                                            ":root"
                                        ]
                                    ]
                                }
                            },
                            "Condition": {
                                "StringEquals": {
                                    "sts:ExternalId": {
                                        "Ref": "ExternalID"
                                    }
                                }
                            }
                        }
                    ]
                },
                "ManagedPolicyArns": [
                    "arn:aws:iam::aws:policy/SecurityAudit"
                ]
            }
        },
        "LaceworkSnsCustomResource": {
            "Type": "Custom::LaceworkSnsCustomResource",
            "DependsOn": [
                "LaceworkCrossAccountAccessRole"
            ],
            "Properties": {
                "Type": "AWS_CFG",
                "ServiceToken": {
                    "Ref": "ServiceToken"
                },
                "IntegrationName": {
                    "Ref": "AWS::StackName"
                },
                "RoleArn": {
                    "Fn::GetAtt": [
                        "LaceworkCrossAccountAccessRole",
                        "Arn"
                    ]
                },
                "ExternalId": {
                    "Ref": "ExternalID"
                },
                "ApiToken": {
                    "Ref": "AccessToken"
                },
                "Account": {
                    "Ref": "ResourceNamePrefix"
                },
                "TemplateVersion": "1.0",
                "AWSAccountId": {
                    "Ref": "AWS::AccountId"
                }
            }
        }
    },
    "Outputs": {
        "ExternalID": {
            "Description": "External ID to share with Lacework AWS Config Security Audit",
            "Value": {
                "Ref": "ExternalID"
            }
        },
        "RoleARN": {
            "Description": "Cross account Role ARN for Lacework AWS Config Security Audit",
            "Value": {
                "Fn::GetAtt": [
                    "LaceworkCrossAccountAccessRole",
                    "Arn"
                ]
            }
        },
        "TemplateVersion": {
            "Description": "Template version",
            "Value": "1.0"
        }
    }
}
"""

response = send_lacework_api_access_token_request('yourname.lacework.net','your_access_key','your_secret_id')
payload_response = response.json()
token = payload_response['token']

region_name = 'us-east-1'

lacework_config_stack = aws.cloudformation.Stack('lacework_config_stack',
    template_body=template,
    parameters={
        'ResourceNamePrefix': 'lacework-config',
        'ExternalID': '123456',
        'AccessToken': token,
        'ServiceToken': 'arn:aws:sns:' + region_name + ':434813966438:prodn-customer-cloudformation'

    },
)

def send_lacework_api_access_token_request(lacework_url, access_key_id, secret_key):
    request_payload = '''
        {{
            "keyId": "{}", 
            "expiryTime": 86400
        }}
        '''.format(access_key_id)

    try:
        return requests.post("https://" + lacework_url + "/api/v2/access/tokens",
                             headers={'X-LW-UAKS': secret_key, 'content-type': 'application/json'},
                             verify=True, data=request_payload)
    except Exception as api_request_exception:
        raise api_request_exception
        return None

pulumi.export('lacework_config_role_arn', lacework_config_stack.outputs["RoleARN"])