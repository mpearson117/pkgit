
**PKGit**
=======
[Hashicorp Packer](https://www.packer.io/) workflow wrapper for HCL2 code.

# Support

Currently PKGit supports the following OSes
- MacOS
- Linux
- Windows

# Installation

1. Git Based pip install

  ```sh
  $ git clone <Repo_URL> ~/<Local_PATH>
  $ cd ~/<Local_PATH>
  $ pip install -e .
  ```

2. Wheel file based pip install

  ```sh
  $ pip install <Wheel file location>
  ```

# Packer prerequisites

pkgit assumes that the deployment is executed from a git repository with the following setup:

## GIT Repository - Naming Conventions and Architecture
 
Repository Naming Standard:
- Start with: `Project_Shortname`
- Contain: `Cloud_ID` (aws, azr, vmw, gcp), `IAC_ID` (pkr)
Branch Naming Standard: `Environment` (dev, qa, stg, uat, prd)
 
## GIT Repository - Environment Specific branch layout

```sh
.
|____common
| |____environments                                     # Project variables folder
| | |____env_<environment>_common.pkrvars.hcl           # Environment specific Packer variables, global to all Images, referenced by PKGit
| | |____env_<environment>_<site>_common.pkrvars.hcl    # Environment and site specific Packer variables, global to all Images, referenced by PKGit
| | |
|____.gitignore                                         # Mandatory .gitignore file for repository maintenance
| | |
|____<resource>                                         # Image to be deployed
| |____environments                                     # OPTIONAL - Image environment specific folder (Overrides Project Variables)
| | |____env_<environment>_common.pkrvars.hcl           # OPTIONAL - Image specific Packer variables, referenced by PKGit
| | |____env_<environment>_<site>_common.pkrvars.hcl    # OPTIONAL - Image specific Environment and site variables, referenced by PKGit
| |____main.pkr.hcl                                     # Packer script
| |____variables.pkr.hcl                                # Packer variables
| |
|____<resource_groups>                                  # Group of Images to be deployed
| |____<sub_resource>                                   # Sub-Image to be deployed
| | |____environments                                   # OPTIONAL - Sub-Image environment specific folder (Overrides Project Variables)
| | | |____env_<environment>_common.pkrvars.hcl         # OPTIONAL - Sub-Image specific Packer variables, referenced by PKGit
| | | |____env_<environment>_<site>_common.pkrvars.hcl  # OPTIONAL - Sub-Image specific Environment and site variables, referenced by PKGit
| | |____main.pkr.hcl                                   # Sub-Image Packer script
| | |____variables.pkr.hcl                              # Sub-Image Packer variables
```
 
# Usage

```sh
Usage:
    pkgit <command>-<site> <image_date>

Commands:
    build          Build Packer image
    help           Display the help menu that shows available commands
    test           Test run showing all project variables
    validate       Packer build validation
    version        PKGit version

Optional Arguments:
    site
    image_date

Example:
    pkgit build
    pkgit build-dr
    pkgit build 2101
```

# Environment Variables Reference

Variables are sourced from:  
- The Git Deployment scripts repository naming conventions.  
Project Specific.
- The `<REPO_PATH>/common/environments/env_<Environment>_common.pkrvars.hcl` environment file, for unisite deployments.  
Environment specific, not changeable per resource.
- The `<REPO_PATH>/common/environments/env_<Environment>_<SITE_NAME>_common.pkrvars.hcl` environment file, for multi-site deployments.  
Environment and site specific, not changeable per resource.

Variables declared in the environment file are declared as runtime variables.  

A set of default Terraform Backend variables set using the environments file:  

| Variable | Description | Usage Target | Default | Required |
|----------|-------------|:------------:|:-------:|:--------:|
| AWS_ACCESS_KEY_ID | AWS Credential | AWS Backend | `` | yes for AWS |
| AWS_SECRET_ACCESS_KEY | AWS Credential | AWS Backend | `` | yes for AWS |
| AWS_SESSION_TOKEN | AWS Credential | AWS Backend | `` | yes for AWS |
| client_secret | AZR Principal Credential | AZR Backend | `` | yes for AZR |
| vsphere_password | VMware Vsphere credential | VMW Backend | `` | yes for VMware |

A set of default variables exposed to Packer in addition to the above variables:  

| Variable | Description | Usage Target | Default | Required |
|----------|-------------|:------------:|:-------:|:--------:|
| image_name_date | The image date stamp in `yymm` format | PKR | Current year and month | yes |
| env | Deployment environment, exposed to Packer, sourced from the Git repository branch name | PKR | - | yes |
| prefix | `Project_Shortname` | PKR | - | no |

