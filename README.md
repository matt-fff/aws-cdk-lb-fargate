# nimbus-lib

Library for wrapping AWS CDK primitives in a useful way.

## FargateStack
Configurable CDK stack to take a docker image and deploy it to the cloud with the AWS CDK. 
Intended to be subclassed

* Support for both [ECR](https://aws.amazon.com/ecr/) images and Docker Hub images.
* Persistent container volumes using [EFS](https://aws.amazon.com/efs/).
* Passing environment variables to the containers.
* Allowlist of IP addresses (if you don't want the whole internet to have access).
* Updating arbitrary security groups to allow ingress from the containers (e.g. to allow your service access to an AWS database).


## Useful AWS/CDK commands
 * `aws sso login`   authenticate with AWS via sso
 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation
 
To authenticate docker with the AWS Elastic Container Registry:
 `aws ecr get-login-password | docker login --username AWS --password-stdin $AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com`


## Useful rye commands
[rye](https://github.com/mitsuhiko/rye) is experimental, but I like it a lot, so I've been using it for all my personal projects, including this one.

 * `rye sync`          install dependencies

You can still install things in standard pip fashion by `pip install -r requirements.lock` and `pip install -r requirements-dev.lock`.

### Scripts
These are custom scripts defined in `pyproject.toml` under `tool.rye.scripts`.
 * `rye run fmt`       run code formatting 
 * `rye run typecheck` run type checking
 * `rye run lint`      run code linting
 * `rye run test`      run tests
 * `rye run quality`   run formatting, linting, and tests on the project



