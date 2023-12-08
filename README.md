# aws-cdk-lb-fargate

Boilerplate repository to take a docker image and deploy it to the cloud with the AWS CDK. 

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
 * `rye sync`          install dependencies
 * `rye run fmt`       run code formatting 
 * `rye run typecheck` run type checking
 * `rye run lint`      run code linting
 * `rye run test`      run tests
 * `rye run quality`   run formatting, linting, and tests on the project

[rye](https://github.com/mitsuhiko/rye) is experimental, but I like it a lot, so I've been using it for all my personal projects, including this one.

You can still install things in standard pip fashion by `pip install -r requirements.lock` and `pip install -r requirements-dev.lock`.


