# JAR Runner
Executing JARs on AWS EC2 through UI and Cognito based authentication.

## Architecture
### Basic flow
![Basic flow](./diagrams/sequenceMain.svg)

### Authentication flow
![Auth flow](./diagrams/sequenceAuth.svg)

### CloudFormation
The whole solution is wrapped in a single CloudFormation template.

#### Parameters
- `BuildsSourceBucket` - S3 bucket containing source for Lambda functions
- `BuildVersion` - Build version to use - i.e. directory name in `BuildsSourceBucket`
- `JarApiStage` - Name of the stage for REST API endpoint Deployment (e.g. *prod*)
- `ExecutorInstanceType` - EC2 instance type to use for executing jars
- `ExecutorInstanceLimit` - Maximum number of concurrently running executor instances
- `ExecutionParameterConfiguration` - configuration of what parameters can be passed to the jar being executed

#### Requirements
The stack can be deployed in any region, however it needs to be in the same region as `BuildsSourceBucket`. If you wish to deploy to a different region, first copy contents from `BuildsSourceBucket` to a bucket in your desired region and put that bucket name into `BuildsSourceBucket` parameter while deploying the stack.

#### Outputs
##### InputBucketName
Name of the S3 bucket which holds jars that can be executed. For jars to be visible, they all need to be put into `jars/` folder/prefix in the bucket. All files outside of that folde won't be visible by JAR Runner.
##### OutputBucketName
This is the S3 bucket name where the results of the execution will be stored. JAR Runner captures standard and diagnostic output from jars being executed and stores them in this bucket. The results will be in `tgz` format and will be named this way:
```
results_<jar_file_name>_<date>-<time>.tgz
```
where date is in the format `YYYY-mm-dd` and time in the format `HH-MM-SS`. The `jar_file_name` is the file name without the trailing `.jar` extension.
##### InputBucketGroup
Group that provides read-write access to `InputBucketName`. Add here all your IAM users who will be responsible for adding and managing jars for JAR Runner.
##### OutputBucketGroup
Group that provides read-only access to `OutputBucketName`. Add here all your IAM users who have need to access outputs from executions of jars.
##### WebsiteURL
This is the URL under which the web interface for JAR runner is present. Give this to all who will be using JAR Runner to execute jars.
##### NotifyTopic
This is the SNS topic that is being published to when jar execution finishes. Subscribe here all the users who want to receive notifications (e.g. emails) for completed executions. The notification will contain an S3 pre-signed URL of the results archive, which is stored in `OutputBucketName`. This topic send notofication of all executions to all the subscribers, regardless of who scheduled those executions. Subscriptions can be more than emails and therefore this can be linked to external systems for various purposes like automation.
##### UserPool
This Cognito user pool stores users (and their passwords) who will be allowed to schedule executions. This credentials are used to log in to the JAR Runner web interface and schedule jar executions from there.

### Manual configuration
After the stack deploys successfully, the following needs to be configured.

#### Cognito users
Users of the system, that will be able to schedule JAR executions through Web UI need to have their accounts created in Cognito in the `UserPool` mentioned in CloudFormation's stack outputs section.

#### SNS notifications
To be able to get nofitications on completed executions, subscriptions in SNS have to be created. The easiest is to create email subscription in the `NotifyTopic` SNS topic. See CloudFormation's stack outputs section.

#### Access to input bucket
This is the bucket the jars will be stored and read from. JAR Runner reads jars from the `jars/` directory of this bucket. Read-write access can be given to people who will be populating this bucket with jars possible to execute. This can be accomplished by creating an IAM user and adding that user to the `InputBucketGroup` group listed in CloudFormation's stack outputs section.

#### Access to output bucket
This bucket contains gzipped output of executions. People who need access to these outputs need read-only access to this bucket. This can be accomplished by creating an IAM user and adding that user to the `OutputBucketGroup` group listed in CloudFormation's stack outputs section.
