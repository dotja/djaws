# DJAWS (DJango on AWS)

### Description

Use **DJAWS** to deploy a Django container on AWS. This repo contains a small Django project called _myproject_ that needs access to a Postgres backend and an S3 bucket. The code in this repo will:

* deploy _myproject_ **locally** with Docker Compose using 4 containers (Gunicorn, Nginx, Postgres and a container to migrate the DB and collect the static files)
* deploy _myproject_ in **production** on AWS Elastic Container Service (ECS)

Deploying on ECS is done via Cloudformation YAML files in the _infra/_ directory. The Django app would be reached via the load balancer URL.


### Installing AWS CLI

It is advised that the root user of your AWS account not be used during deployment or most other activities. It is better to create a new group and a user belonging to that group. The user would have programmatic but limited access and you can store the user's credentials locally in `~/.aws/credentials`. 

> The group will probably exceed the limit of 10 policies, therfore a [new customer-managed policy should be created by consolidating permissions](https://stackoverflow.com/a/57875674/1037128).

```
## install aws cli
virtualenv venv -p python
source venv/bin/activate
python -m pip install awscli
aws --version
```

### Deployment to AWS

Deployment can be carried out from your local machine and it consists of the steps below:

#### Building the Container Images
1. Build the Docker image for _myproject_ that will carry out the DB migration and static collection. Push the image to the Elastic Container Registry (ECR)
2. Build the Docker image for _myproject_ that will launch the app. Push the image to the Elastic Container Registry (ECR)


#### Creating the Infrastructure on AWS
3. Create the VPC stack (includes public subnets, private subnets, internet gateway, elastic IPs, Nat gateways, route tables)
4. Create the execution role for the ECS task
5. Create the load balancer, security group and task definition
6. Create the Postgres RDS, S3 bucket and their secrets and parameters
7. Update the Django SECRET_KEY as a SecureString type on the parameter store and add its value

#### Launch
8. Run the ECS Service with the container image that will set up the DB and static files
9. Launch the ECS Service using the container image that will launch the Django app


### The AWS Services Used:

* Elastic Container Registry
* Elastic Container Service
* Fargate Cluster
* Application Load Balancer
* Elastic IP address
* Postgres RDS
* S3 bucket
* Secrets Manager
* SSM: Parameter Store
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

1. Build and push data container image to ECR
2. Build and push app container image to ECR

```
## build docker images
docker build -t myproject_data -f /path/to/Dockerfile_data .
docker build -t myproject_app -f /path/to/Dockerfile_app .

## create a repo on ECR
aws ecr create-repository --repository-name myproject

## authenticate your local Docker daemon against the ECR
$(aws ecr get-login --registry-ids <your registry ID> --no-include-email)

## tag the Docker images
docker tag myproject_data <your registry ID>.dkr.ecr.<your region>.amazonaws.com/myproject:data

docker tag myproject_app <your registry ID>.dkr.ecr.<your region>.amazonaws.com/myproject:app

## push to ECR
docker push <your registry ID>.dkr.ecr.<your region>.amazonaws.com/myproject:data

docker push <your registry ID>.dkr.ecr.<your region>.amazonaws.com/myproject:app

## list your container images on ECR
aws ecr list-images --repository-name myproject

## delete image on registry
aws ecr batch-delete-image --repository-name myproject --image-ids imageDigest=<the image digest>
```

3. The VPC stack

```
cd infra
aws cloudformation create-stack --stack-name vpc --template-body file://vpc.yaml --capabilities CAPABILITY_NAMED_IAM
```

4. The Execution role

```
aws cloudformation create-stack --stack-name roles --template-body file://roles.yaml --capabilities CAPABILITY_NAMED_IAM
```

5. The Load balancer, security group and task definition

```
## use the 'data' image
aws cloudformation create-stack --stack-name lb-sg-task --template-body file://lb_sg_task.yaml --capabilities CAPABILITY_NAMED_IAM --parameters ParameterKey=ImageUrl,ParameterValue='<your registry ID>.dkr.ecr.<your region>.amazonaws.com/myproject:data'
```

6. The Postgres DB, S3 bucket and Secrets

```
aws cloudformation create-stack --stack-name rds-s3 --template-body file://rds_s3.yaml --capabilities CAPABILITY_NAMED_IAM --parameters ParameterKey=BucketName,ParameterValue=$(head /dev/urandom | tr -dc a-z0-9 | head -c10)
```

7. Update SECRET_KEY in the Parameter Store:

```
aws ssm put-parameter --overwrite --name /Prod/DjangoSecret --type SecureString --value <SECRET_KEY value>
```

8. Run the ECS Service adding the data image that will migrate the DB and collect the static files

```
aws cloudformation create-stack --stack-name service --template-body file://service.yaml --capabilities CAPABILITY_NAMED_IAM
```

9. Run the ECS Service adding the app image that will launch the Django container

```
aws cloudformation delete-stack --stack-name service

## use the 'app' image this time
aws cloudformation update-stack --stack-name lb-sg-task --template-body file://lb_sg_task.yaml --capabilities CAPABILITY_NAMED_IAM --parameters ParameterKey=ImageUrl,ParameterValue='<your registry ID>.dkr.ecr.<your region>.amazonaws.com/myproject:app'

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
