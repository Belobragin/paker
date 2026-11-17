# ML code to provide adversarial image attack

1. you can find a couple of articles about adversarial immages in the `./ref` folder. There are many other books and articles.
2. excellent popular words explanations are:
   - [Pyimagesearch-1](https://www.pyimagesearch.com/2020/10/19/adversarial-images-and-attacks-with-keras-and-tensorflow) and 
   - [Pyimagesearch-2](https://pyimagesearch.com/2024/01/08/adversarial-learning-with-keras-and-tensorflow-part-1-overview-of-adversarial-learning/)
   and 
   - [Pyimagesearch-3](https://www.pyimagesearch.com/2020/10/26/targeted-adversarial-attacks-with-keras-and-tensorflow/)


## Overview
1. This repository provides Python code to build and run docker container for building adversarial images (adversarial image attack). This is a part of integral `werewolf - aker - cr-resnet` project.
2. This project is for fun and personal use only and it is not a commercial product.
3. Code is served "as-is", with absolutely no gurantees or support, on the best effort basis. I will try to answer the questions, but can not promise that.
4. This code was prepared with the assistance of Claude Sonnet 5.5

  
## Aker code realization:
This project is served as a local and an aws cloud options. Details are below.


## License and terms of use
This repo is covered by the standard `BSD 3-Clause "New" or "Revised" License`. 
For citing use the next information:
```
Vladimir Belobragin
e-mail:   vblvbl133@gmail.com
linkedin: https://www.linkedin.com/in/belovl%D0%B0d/
```

## Security
 This projects container is NOT intended for public exposure. Run it locally behind the firewall and other security devices OR/AND, if run in the aws cloud, use a ssh tunnel:
```
ssh -i [local path to your aws key] -N \
  -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 \
  -L 8101:localhost:8101 ec2-user@[your ec2 instance public address]
```
The recommended aws cloud IAC decision is included. 
No responsibility for this product use consequences. Play with the code on your own risk.

## More verbose product description
1. Code allows to use biterate tarheted, biterate untargeted and FGSM attack algorythms.
2. for biterate targeted and biterate untargeted algorythms the code idea from
[Pyimagesearch](https://www.pyimagesearch.com)
3. for FGSM algorythm the code was taken from:
   [Google Tensorflow](https://www.tensorflow.org/tutorials/generative/adversarial_fgsm)   
4. Code modifications and refacture were introduced to follow project goals.


### local run
1. Prerequisites:
   - [docker-compose](https://docs.docker.com/compose/)
   - [nats server](https://nats.io/)
classification neural net    
2. `aker` does not write to any database. For the database use, adapt `wewrewolf`
3. before local use, create storage with `make lcreatestorage`.
4. create virtual environment with `make lvenv`
5. clone repo. Put your values to the file `.env.local.example` and remove `.example` suffix. Files with environment variables are used by makefile commands
6. rename "Makefile.example" -> "Makefile".  Type `makefile help`   - most of the commands are explained
7. To run in the container, build and upload container with `make lakerstart`. To stop the container, type `lakerstop`.
8. Recommendations are to use  control pannel application `werewolf` for api proliferation
9. Example of local message command:
```
source .env.local && nats pub $NATS_FOR_PROCESSING_CHAN  '{ "order_id":"5678234", "algorythm": "biterate_targeted", "input_image_name": "hog-test.jpg", "alter_goal": "tiger_shark", "save_filter": "1"}' --user $NATS_AKER_USER --password $NATS_AKER_PSW
```
10. Precautions: 
   - do not work with storage folders directly since that will deter consistency with the database. Use `upload` and `download` apis and "test-image" and "download" folders, either in the cloud or locally
   - use werewolf project control panel
   - build crresnet container for smooth post-diagnosing of the adversarial image(s), explanations are at [cr-resnet](https://github.com/Belobragin/cr-resnet) repo


### cloud run
!} Attention: cloud resources are NOT free and their cost may vary greatly. Set alarms to avoid cloud infrastructure costs above the desired minimum (such an alarm is not included to the templates in this repo).
1. Clone this repo to another repo to `main` branch and locally. Adjust git parameters to interact with your repo. Fill in value of the parameter "GithubFullRepositoryId" at `iac/awscloud/parameter/aker_resource_pipeline_parameter.json`
2. Put your values to the file `.env.awscloud.example` and remove `.example` suffix. It is  used by makefile commands.
3. Adjust input parameters in the template  `iac/awscloud/template/AkerEcrTemplate.yaml` and in the parameters file `iac/awscloud/parameter/aker-ecr-parameter.json` (for non-default paramters) and create AWS ECR repo with `make setrepo`
4. Create docker image and push it to the ECR repository with `make pushtoecr`
5. Create cloud resources - follow guidelines in the `werewolf` project
6. Create AWS CodePipeline with `make setpipeline`. Grant AWS CodePipeline access to your github repo.
7. Push to the `main` branch in your repo "GithubFullRepositoryId". Pipeline will start automatically. It will crete the container and ECS cluster and finally - task definintion for the ECS Fargate run of `aker` application
8. After pipeline finishes, your container can be reached with AWS SQS message. Reply will get back to another sqs queue and be looged in the AWS Cloudformation
9. example of sqs message:
```
aws sqs send-message --region us-east-2 --queue-url "[your sqs message queue url]" --message-body '{ "order_id":"5678234", "algorythm": "biterate_targeted", "input_image_name": "hog-test.jpg", "alter_goal": "tiger_shark", "save_filter": "1" }'
```
SQS queue url may be obtained with the command `make getsqsqueue`
10. Precautions: 
   - do not work with storage folders directly since that may avoid consistency with the `werewolf` database. Use `upload` and `download` werewolf apis and "test-image" and "download" folders.  s3 bucket folders are created automatically on file uploads.
   - use werewolf project swagger notation
   - build crresnet container for smooth post-diagnosing of the adversarial image(s), explanations are at [cr-resnet](https://github.com/Belobragin/cr-resnet) repo


## Example of the output
```
{
    "order_id": "d3215822-b28c-405a-8b2c-707635f1e2f6",
    "success_adversarial": true,
    "success_filter": "1",
    "adversarial_name": "storage/adversarial/saluki_adversarial_fgsm.jpeg",
    "filter_name": "storage/filter/saluki_filter_fgsm.jpeg",
    "timestamp": "2026-11-15T16:03:00.673616",
    "error": "",
    "algorythm": "fgsm",
    "alter_goal": "",
    "predictions": {
        "n0": [
            "n02109047",
            "Great_Dane",
            "246",
            "83.85"
        ],
        "n1": [
            "n02108089",
            "boxer",
            "242",
            "5.14"
        ],
        "n2": [
            "n02091134",
            "whippet",
            "172",
            "4.61"
        ]
    }
}
```
