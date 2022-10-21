# Boto3-Project
Developer Operations assignment that uses Boto3 to interact with the EC2 and S3 AWS services. 

## EC2 Instance
An EC2 instance is launched that can be accessed with an SSH key and with a suitable security group that allows HTTP traffic. An Apache web server is installed on the instance where the instance metadata is displayed on the web server through a HTML file. 

## S3 Bucket
An S3 bucket is also programatically setup to store both a JPEG and HTML object. The S3 bucket is configured for static website hosting where it displays the JPEG object as an image through the HTML file. 

## Monitoring Script
The bash script 'monitor.sh' is copied to the EC2 instance and is excecuted on the instance through the use of SSH commands. This script is used to monitor the number of processes running on the instance and memory utilisation data. 

## CloudWatch
CloudWatch monitoring was setup for the EC2 instance. A CloudWatch alarm was created to monitor the instance and if the CPU usage exceeded 60%, the instance would be terminated. The alarm configurations were copied to 'cloudwatch.txt'.

## EC2 Web Page
![EC2 Web Page](https://github.com/stephenpower37/Boto3-Project/blob/main/ec2_website.jpg)

## S3 Website
![S3 Website](https://github.com/stephenpower37/Boto3-Project/blob/main/s3_website.jpg)
