#!/usr/bin/python3 -u

import os
import sys
import hcl
import boto3
import getpass
from git import Repo
from py_console import console
from datetime import datetime

class Error(Exception):
    """Core class for other exceptions"""
    pass
class Core():
    def __init__(self, action, image_name_date=None, target_environment=None):
        self.app_name = os.path.basename(sys.argv[0])
        self.app_config = os.path.basename(os.path.dirname(__file__))
        self.get_platform()
        self.action = action
        self.build_id = os.getenv('BUILD_ID')
        self.target_site = target_environment
        self.image_name_date_arg = image_name_date
        self.location = os.path.realpath(os.getcwd())
        self.repo_url = Repo(self.repo_root).remotes[0].config_reader.get("url")
        self.repo_name = str(os.path.splitext(os.path.basename(self.repo_url))[0])
        self.branch_name = str(Repo(self.repo_root).active_branch)
        self.clouds_list = ['aws', 'azr', 'vmw', 'gcp']
        self.iac = 'pkr'
        self.vsphere_password_environ = 'GOVC_PASSWORD'
        self.azure_password_environ = 'AZURE_PASSWORD'
        self.cloud = self.list_intersect(self.repo_name.split("-"), self.clouds_list)[0]
        self.resource = os.path.relpath(self.location, self.repo_root).replace('\\', '/')
        self.get_default_variables()
        self.data_set = dict(location=self.location,repo=self.repo_root,
                             env=self.environment,target_site=self.target_site,cloud=self.cloud)
        self.secret_path = os.path.join("{repo}".format(**self.data_set), "secret_{cloud}_backend.pkrvars.hcl".format(**self.data_set))
        self.get_image_name_date()
        self.get_env_files()
        self.sanity_check()
        self.get_backend_configuration()
        self.export_environment()

    def get_time(self, time_format):
        now = datetime.now()
        if time_format == "long":
            time_stanp = now.strftime("%y%m%d-%H%M%S")
        elif time_format == "short":
            time_stanp = now.strftime("%y%m")

        return time_stanp

    def get_aws_sts_credentials(self, account_number, role='inf_packer_cross_account_role', region='us-east-1', source_creds={}):
        self.sts_client = boto3.client('sts', **source_creds, region_name=region)
        self.arn = f"arn:aws:iam::{account_number}:role/{role}"
        self.session = self.sts_client.assume_role(
            RoleArn=self.arn, 
            RoleSessionName="packer-role-{}-{}".format(self.cloud_account, self.get_time("long")),
            )
        credentials = dict(
                aws_access_key_id = self.session['Credentials']['AccessKeyId'],
                aws_secret_access_key = self.session['Credentials']['SecretAccessKey'],
                aws_session_token = self.session['Credentials']['SessionToken'],
                region_name=region
        )

        return credentials

    def get_image_name_date(self):
        if self.image_name_date_arg == None:
            self.image_name_date = self.get_time("short")
        else:
            self.image_name_date = self.image_name_date_arg


    def get_platform(self):
        try:
            repo_root = Repo(search_parent_directories=True).git.rev_parse("--show-toplevel")
        except:
            console.error("  You are not executing " + self.app_config.upper() + " from a git repository !\n  Please ensure execution from a resurce directory inside a git repository !\n", showTime=False)
            sys.exit(2)

        if sys.platform.startswith("win"):
            self.platform = "windows"
            self.repo_root = repo_root.replace('/', '\\')
        else:
            self.platform = "linux"
            self.repo_root = repo_root

    def list_intersect(self, list1, list2):
        out = [item for item in list1 if item in list2]
        return out
    
    def get_default_variables(self):
        """
        Get repo dependent Project, Environment variables.
        """
        self.project = self.repo_name.split("-")[0]
        self.environment = self.branch_name

    def get_env_files(self):
        """
        Return Appropriate Env File Based on whether there is
        a target deployment defined in the init attributes.
        """
        if self.target_site:
            file_preffix = "{env}_{target_site}".format(**self.data_set)
        else:
            file_preffix = "{env}".format(**self.data_set)
        
        self.common_env_file = os.path.join(
            self.repo_root, "common", "environments","env_{}_common.pkrvars.hcl".format(
                file_preffix))
        self.local_env_file = os.path.join(
            self.location, "environments", "env_{}.pkrvars.hcl".format(
            file_preffix))

    def sanity_check(self):
        """
        Series of sanity Checks performed to ensure what we
        are working with.
        """
        self.var_file_args_list = []
        self.var_file_args = ''
        
        if os.path.isfile(self.secret_path):
            self.var_file_args_list.append(self.secret_path)

        if self.iac not in self.repo_name.split("-"):
            console.error("  This is not a Packer deployment repository !\n  use PKGit from a repository that contains " + self.iac + " in the name !\n", showTime=False)
            sys.exit(2)

        if self.location == self.repo_root:
            console.error("  You are executing PKGit from the repository root !\n  Please ensure execution from a resurce directory !\n", showTime=False)
            sys.exit(2)
        
        if not any(File.endswith(".pkr.hcl") for File in os.listdir(self.location)):
            console.error("  You are executing PKGit from an improper location,\n  Please ensure execution from a resurce directory !\n", showTime=False)
            sys.exit(2)

        if not os.path.isfile(self.common_env_file):
            console.error("  Please ensure the below file exists:\n    " + self.common_env_file + "\n    and add configuration content if necessary !\n", showTime=False)
            sys.exit(2)
        else:
            self.var_file_args_list.append(self.common_env_file)

        if not os.path.isfile(self.local_env_file):
            console.info("  No Local Environment Files at this location ! \n  Please  add configuration content here if necessary !:", showTime=False)
            console.warn("  " + self.local_env_file + "\n", showTime=False)
            #sys.exit(2)
        else:
            self.var_file_args_list.append(self.local_env_file)
                
        for env_file in self.var_file_args_list:
            self.var_file_args += ' -var-file ' + env_file

    def get_backend_configuration(self):
        """
        Parse Data returned by get_deployment_attributes and
        return bucket, backend_region for deployment.
        """
        if self.cloud in ['aws', 'azr', 'gcp']:
            try:    
                with open(self.common_env_file, 'r') as fp:
                    obj = hcl.load(fp)
                    self.cloud_account = obj['cloud_account']
            except KeyError:
                console.error("  Please ensure the " + self.common_env_file + "\n  contains the deployment 'cloud_account' variable !\n", showTime=False)
                sys.exit(2)
        else:
            self.cloud_account = ''

        if self.cloud == 'aws':
            if os.environ.get("AWS_ACCESS_KEY_ID") is not None and os.environ.get("AWS_SECRET_ACCESS_KEY") is not None:
                self.aws_access_key_id = os.environ.get("AWS_ACCESS_KEY_ID")
                self.aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
                self.aws_session_token = os.environ.get("AWS_SESSION_TOKEN")
            else:
                try:    
                    with open(self.common_env_file, 'r') as fp:
                        obj = hcl.load(fp)
                        self.cloud_role = obj['cloud_role']
                        creds = self.get_aws_sts_credentials(self.cloud_account, self.cloud_role)
                except KeyError:
                    console.info("  Role not speciffied in " + self.common_env_file + "\n  Using default role !\n", showTime=False)
                    creds = self.get_aws_sts_credentials(self.cloud_account)
                
                self.aws_access_key_id = creds['aws_access_key_id']
                self.aws_secret_key = creds['aws_secret_access_key']
                self.aws_session_token = creds['aws_session_token']

        elif self.cloud == 'vmw':
            self.cloud_role = ''
            if os.environ.get(self.vsphere_password_environ) is not None:
                self.vsphere_password = os.environ[self.vsphere_password_environ]
            elif os.path.exists(self.secret_path):
                try:    
                    with open(self.secret_path, 'r') as fp:
                        obj = hcl.load(fp)
                        self.vsphere_password = obj['vsphere_password']
                except KeyError:
                    console.error("  Secrets confg file " + self.secret_path + "\n  existsts, but does not contain 'vsphere_password' variable !\n", showTime=False)
                    sys.exit(2)
            else:
                self.vsphere_password = getpass.getpass()
        
        elif self.cloud == 'azr':
            self.cloud_role = ''
            if os.environ.get(self.azure_password_environ) is not None:
                self.azure_password = os.environ[self.azure_password_environ]
            elif os.path.exists(self.secret_path):
                try:    
                    with open(self.secret_path, 'r') as fp:
                        obj = hcl.load(fp)
                        self.azure_password = obj['client_secret']
                except KeyError:
                    console.error("  Secrets confg file " + self.secret_path + "\n  existsts, but does not contain 'vsphere_password' variable !\n")
                    sys.exit(2)
            else:
                self.azure_password = getpass.getpass()

    def export_environment(self):
        """
        Export the environemt Variables to be used by
        Terraform.
        """
        if self.cloud == 'aws':
            self.my_env = dict(os.environ, 
                **{"AWS_ACCESS_KEY_ID": self.aws_access_key_id},
                **{"AWS_SECRET_ACCESS_KEY": self.aws_secret_key},
                **{"AWS_SESSION_TOKEN": self.aws_session_token},
                **{"PKR_VAR_account_number": self.cloud_account},
                **{"PKR_VAR_image_name_date": self.image_name_date},
                **{"PKR_VAR_env": self.environment},
                **{"PKR_VAR_prefix": self.project},
                )
        elif self.cloud == 'vmw':
            self.my_env = dict(os.environ, 
                **{"PKR_VAR_vsphere_password": self.vsphere_password},
                **{"PKR_VAR_image_name_date": self.image_name_date},
                **{"PKR_VAR_env": self.environment},
                **{"PKR_VAR_prefix": self.project},
                )
        elif self.cloud == 'azr':
            self.my_env = dict(os.environ, 
                **{"PKR_VAR_client_secret": self.azure_password},
                **{"PKR_VAR_image_name_date": self.image_name_date},
                **{"PKR_VAR_env": self.environment},
                **{"PKR_VAR_prefix": self.project},
                )

