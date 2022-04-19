#!/usr/bin/python3 -u

from .core import Core
from py_console import console
import pkg_resources
import sys
import jsonpickle
import json
import subprocess

class Action(Core):
    """
    Inherits the Core Class and its attributes.
    Adding in 3 child atts, action, image_name_date and target_environment.
    """
    def __init__(self, action, image_name_date, target_environment):
        self.action = action
        self.image_name_date = image_name_date
        self.target_environment = target_environment
        Core.__init__(self, action, image_name_date, target_environment)

    def __str__(self):
        return ' '.join((self.repo_name, self.location))

    def command(self, command):
        """
        Re-usable function to execute a shell command, 
        with error handling, and ability to execute quietly, 
        or display output.
        """
        output = subprocess.Popen(command, env=self.my_env)
        output.communicate()

    def build(self):
        console.success("  Running Packer Build:", showTime=False)
        self.command("packer build{} .".format(self.var_file_args).split())

    def validate(self):
        console.success("  Running Packer Validate:", showTime=False)
        self.command("packer validate{} .".format(self.var_file_args).split())

    def help(self):
        """
        Provide Application Help
        """
        help = """
        Usage:
            {0} <command>-<site> <image_date>
        
        Commands:
            build          Build Packer image
            help           Display the help menu that shows available commands
            test           Test run showing all project variables
            validate       Packer build validation
            version        {0} version

        Optional Arguments:
            site
            image_date
        
        Example:
            {0} build
            {0} build-dr
            {0} build 2101
        """
        print(help.format(self.app_name))

    def test(self):
        """
        Debug all of our class attributes through a single
        cli call.
        """
        console.warn("  Packer Prerequisites Check", showTime=False)
        console.warn("  ==========================", showTime=False)
        self.version_git()
        self.version_pkr()

        serialized = json.loads(jsonpickle.encode(self, max_depth=2))
        console.warn("\n  Current Deployment Details", showTime=False)
        console.warn("  ==========================", showTime=False)
        console.success("  Platform           = {platform}".format(**serialized), showTime=False)
        console.success("  AppDir             = {location}".format(**serialized), showTime=False)
        console.success("  Repo Name          = {repo_name}".format(**serialized), showTime=False)
        console.success("  Repo Root          = {repo_root}".format(**serialized), showTime=False)
        console.success("  Repo URL           = {repo_url}".format(**serialized), showTime=False)
        console.success("  Branch Name        = {branch_name}".format(**serialized), showTime=False)
        console.success("  Resource Name      = {resource}".format(**serialized), showTime=False)
        console.success("  Cloud              = {cloud}".format(**serialized), showTime=False)
        console.success("  Project            = {project}".format(**serialized), showTime=False)
        console.success("  Cloud Account      = {cloud_account}".format(**serialized), showTime=False)
        console.success("  Cloud Role         = {cloud_role}".format(**serialized), showTime=False)
        console.success("  Environment        = {environment}".format(**serialized), showTime=False)
        console.success("  Common Env File    = {common_env_file}".format(**serialized), showTime=False)
        console.success("  Local Env File     = {local_env_file}".format(**serialized), showTime=False)
        console.success("  Target Env (Site)  = {target_environment}".format(**serialized), showTime=False)
        console.success("  Command            = {action}".format(**serialized), showTime=False)
        console.success("  Prefix             = {project}".format(**serialized), showTime=False)
        console.success("  Backend Secret     = {secret_path}".format(**serialized), showTime=False)

        console.warn("\n  Packer Variables", showTime=False)
        console.warn("  ================", showTime=False)
        console.success("  PKR_VAR_image_name_date  = {image_name_date}".format(**serialized), showTime=False)
        console.success("  PKR_VAR_prefix           = {project}".format(**serialized), showTime=False)
        console.success("  PKR_VAR_env              = {environment}".format(**serialized), showTime=False)

    def version(self):
        """
        Get application version from VERSION with cli call.
        """
        version = pkg_resources.require(self.app_config)[0].version
        console.success("  " + self.app_config.upper() + " version: " + version, showTime=False)

    def version_git(self):
        """
        Get the version of Git used.
        """
        try:    
            show_cmd = subprocess.Popen(['git', '--version'],stdin=None,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            (stdout, stderr) = show_cmd.communicate()
            git_version = stdout.strip().decode().split(" ")[2]
            console.success("  Git version: " + git_version, showTime=False)
        except:
            console.error("  Git is not installed", showTime=False)
            sys.exit(2)  

        return git_version

    def version_pkr(self):
        """
        Get the version of Packer used.
        """

        try:
            show_cmd = subprocess.Popen(['packer', 'version'],stdin=None,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            (stdout, stderr) = show_cmd.communicate()
            output = stdout.decode().split(" ")[1]
            packer_version = output.split("\n")[0]
            console.success("  Packer version: " + packer_version, showTime=False)
        except:
            console.error("  Packer is not installed", showTime=False)
            sys.exit(2)  

        return packer_version
