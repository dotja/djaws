# DJAWS (DJango on AWS)

### Description

Use **DJAWS** to deploy a Django container on AWS. This repo contains a small Django project called _myproject_ that needs access to a Postgres backend and an S3 bucket. The code in this repo will:

* deploy _myproject_ **locally** with Docker Compose using 3 containers (Gunicorn, Nginx and Postgres)
* deploy _myproject_ in **production** on AWS Elastic Container Service (ECS)

Deploying on ECS is done via Cloudformation YAML files in the _infra/_ directory. The Django app would be reached via the load balancer URL.


### Installing AWS CLI

It is advised that the root user of your AWS account not to be used during deployment or most other activities. It is better to create a new group and a user belonging to that group. The user would have programmatic but limited access and you can store the user's credentials locally in `~/.aws/credentials`.

```
## install aws cli
virtualenv venv -p python
source venv/bin/activate
python -m pip install awscli
aws --version
```

### Deployment to AWS

Deployment can be carried out from your local machine and it consists of 7 steps:

1. Build the Docker image for _myproject_ and push it to the Elastic Container Registry (ECR)
2. Create the VPC stack (includes public subnets, private subnets, internet gateway, elastic IPs, Nat gateways, route tables)
3. Create the execution role for the ECS task
4. Create the load balancer, security group and task definition
5. Create the Postgres RDS, S3 bucket and their secrets and parameters
6. Update the Django SECRET_KEY as a SecureString type on the parameter store and add its value
7. Launch the ECS Service.


### The AWS Services Used:

* Elastic Container Registry
* Elastic Container Service
* Fargate Cluster
* Application Load Balancer
* Elastic IP address
* Postgres RDS
* S3 bucket
* Secrets Manager
* Parameter Store
* CloudWatch


## Local Deployment

Docker Compose is used to locally spin up a Django container with Gunicorn, Nginx container and a Postgres container.
Enviroment variables are found in the **.env** file.

The Docker image for the Django project _myproject_ will be built locally.

#### Start

```docker-compose up -d```

#### Stop

```docker-compose down```


## Deployment in Production with AWS

1. Build and push Docker image to ECR

```
## build docker image
docker build -t myproject .

## create a repo on ECR
aws ecr create-repository --repository-name myproject

## authenticate your local Docker daemon against the ECR
$(aws ecr get-login --registry-ids <your registry ID> --no-include-email)

## tag the Docker image
docker tag myproject <your registry ID>.dkr.ecr.<your region>.amazonaws.com/myproject:0.0.1

## push to ECR
docker push <your registry ID>.dkr.ecr.<your region>.amazonaws.com/myproject:0.0.1

## list your container images on ECR
aws ecr list-images --repository-name myproject

## delete image on registry
aws ecr batch-delete-image --repository-name myproject --image-ids imageDigest=<the image digest>
```

After the initial image is built (which does the DB migration), you will be able to change the `db_init.sh` script into an init.sh script that lacks the DB migration part and that will be used by the Task later on.

2. The VPC stack

```
cd infra
aws cloudformation create-stack --stack-name vpc --template-body file://vpc.yaml --capabilities CAPABILITY_NAMED_IAM
```

3. The Execution role

```
aws cloudformation create-stack --stack-name roles --template-body file://roles.yaml --capabilities CAPABILITY_NAMED_IAM
```

4. The Load balancer, security group and task definition

```
aws cloudformation create-stack --stack-name lb-sg-task --template-body file://lb_sg_task.yaml --capabilities CAPABILITY_NAMED_IAM --parameters ParameterKey=ImageUrl,ParameterValue='<your registry ID>.dkr.ecr.<your region>.amazonaws.com/myproject:0.0.1'
```

5. The Postgres DB, S3 bucket and Secrets

```
aws cloudformation create-stack --stack-name rds-s3 --template-body file://rds_s3.yaml --capabilities CAPABILITY_NAMED_IAM --parameters ParameterKey=BucketName,ParameterValue=$(head /dev/urandom | tr -dc a-z0-9 | head -c10)
```

6. Update SECRET_KEY in the Parameter Store:

```
aws ssm put-parameter --overwrite --name /Prod/DjangoSecret --type SecureString --value <SECRET_KEY value>
```

7. Launching the ECS Service

```
aws cloudformation create-stack --stack-name service --template-body file://service.yaml --capabilities CAPABILITY_NAMED_IAM
```

### Teardown

Teardown in reverse order:

service stack -> rds-s3 stack -> lb-sg-task stack -> roles stack -> vpc stack

```
## deleting a stack
aws cloudformation delete-stack --stack-name <stack name>

## updating a stack
aws cloudformation update-stack --stack-name <stack name> --template-body file://<stack yaml>
```
