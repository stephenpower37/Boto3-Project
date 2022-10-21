# Setup
import boto3, urllib.request, time
import subprocess as sp
import webbrowser as wb
import random as rm
from datetime import datetime, timedelta

ec2 = boto3.resource('ec2')
s3 = boto3.resource('s3')

def launch_bucket():
    try:
        print("Creating an S3 bucket...")

        # Generates a bucket name with 6 random figures
        bucket_name = "spower" + str(rm.randrange(100000, 999999))

        # S3 bucket setup
        s3.create_bucket(Bucket=bucket_name, ACL='public-read')
        print(f"S3 Bucket: {bucket_name} succesfully created...")

        website_configuration = {
            'ErrorDocument': {'Key': 'error.html'},
            'IndexDocument': {'Suffix': 'index.html'},
        }
        bucket_website = s3.BucketWebsite(bucket_name)
        bucket_website.put(WebsiteConfiguration=website_configuration)
        print("S3 bucket website configured...")
        insert_objects(name=bucket_name)

        # Reloads the s3 bucket's website and launches the website using the link
        print("Launching S3 bucket website...")
        bucket_website.reload()
        website_link = f"http://{bucket_name}.s3.us-east-1.amazonaws.com/index.html"
        wb.open_new_tab(website_link)
        print("S3 website launched...")

        # Creates a text file and copies the link of the s3 bucket website
        sp.run("touch spowerurls.txt", shell=True)
        sp.run(f"echo 'S3 Website: {website_link}' > spowerurls.txt", shell=True)

    except Exception as error:
        print("An error occured when creating an S3 bucket.")
        print(error)


def insert_objects(name):
    try:
        # Retrieves a url and saves to a jpeg file
        img_URL = 'http://devops.witdemo.net/logo.jpg'
        urllib.request.urlretrieve(img_URL, 'logo.jpg')

        # Creates a html file and inserts an image tag
        sp.run("touch index.html", shell=True)
        sp.run(f"echo '<img src='''https://{name}.s3.amazonaws.com/logo.jpg'>''' > index.html",
               shell=True)

        # Inserts a jpeg file to the s3 bucket
        image = 'logo.jpg'
        s3.Object(name, image).put(Body=open(image, 'rb'),
                                   ContentType='image/jpeg',
                                   ACL='public-read')

        # Inserts a html file to the s3 bucket
        index = 'index.html'
        s3.Object(name, index).put(Body=open(index, 'rb'),
                                   ContentType='text/html',
                                   ACL='public-read')
                                   
        print("HTML and JPEG objects added to the bucket...")

    except Exception as error:
        print("An error occured when inserting objects into an S3 bucket.")
        print(error)


def create_inst():
    try:
        print("Creating an EC2 instance...")

        # EC2 instance setup
        new_instances = ec2.create_instances(
            # Amazon Linux 2 AMI
            ImageId="ami-09d3b3274b6c5d4aa",
            MinCount=1,
            MaxCount=1,
            KeyName="devops",
            # Security group allows HTTP and SSH access
            SecurityGroupIds=['sg-0ebfe6fbded173a39', ],
            InstanceType='t2.nano',
            # Script used to display instance data in HTML format
            UserData="""#!/bin/bash 
                yum install httpd -y 
                systemctl enable httpd 
                systemctl start httpd
                echo '<html>' > index.html
                echo '<head>' >> index.html
                echo '<title> EC2 Webpage </title>' >> index.html
                echo '</head>' >> index.html
                echo '<body>' >> index.html
                echo '<h1> EC2 Webpage Details: </h1>' >> index.html
                echo '<br>Private IP Address: ' >> index.html
                curl -s http://169.254.169.254/latest/meta-data/local-ipv4 >> index.html
                echo '<br><br>Public IP Address: ' >> index.html
                curl -s http://169.254.169.254/latest/meta-data/public-ipv4 >> index.html
                echo '<br><br>Instance ID: ' >> index.html
                curl -s http://169.254.169.254/latest/meta-data/instance-id >> index.html
                echo '<br><br>Instance Type: ' >> index.html
                curl -s http://169.254.169.254/latest/meta-data/instance-type >> index.html
                echo '<br><br>AMI ID: ' >> index.html
                curl -s http://169.254.169.254/latest/meta-data/ami-id >> index.html
                echo '</body>' >> index.html
                echo '</html>' >> index.html
                cp index.html /var/www/html/index.html
                """)

        # Tagging the instance with a name
        name_tag = {'Key': 'Name', 'Value': 'EC2 Instance'}
        new_instances[0].create_tags(Tags=[name_tag])
        print("EC2 instance successfully created...")

        # Reloads the instance when it is successfully running
        new_instances[0].wait_until_running()
        new_instances[0].reload()
        print("EC2 instance is running...")

        # The program is set to sleep for 30 seconds to allow the web server to start
        public_ip = new_instances[0].public_ip_address
        print("Launching EC2 instance web server...")
        time.sleep(30)

        # The monitor.sh file is copied to the instance once the web server is running
        sp.run("chmod 400 devops.pem", shell=True)
        sp.run(f"ssh -o StrictHostKeyChecking=no -i devops.pem ec2-user@{public_ip} exit", shell=True)
        sp.run(f"scp -i devops.pem monitor.sh ec2-user@{public_ip}:.", shell=True)
        sp.run(f"ssh -i devops.pem ec2-user@{public_ip} 'chmod 700 monitor.sh'", shell=True)
        sp.run(f"ssh -i devops.pem ec2-user@{public_ip} './monitor.sh'", shell=True)

        # Launches the web page using the public ip address
        wb.open_new_tab(public_ip)
        print("EC2 web page launched...")

        # Copies the ec2 web page url to the text file
        sp.run(f"echo 'EC2 Web Page: http://{public_ip}' >> spowerurls.txt", shell=True)

        print("\n\nCLOUDWATCH\n")
        cloudwatch_setup(new_instances[0].id)

    except Exception as error:
        print("An error occured when creating an EC2 instance.")
        print(error)


def cloudwatch_setup(instId):
    try:
        cw_client = boto3.client('cloudwatch')
        cloudwatch = boto3.resource('cloudwatch')
        instance = ec2.Instance(instId)

        # Create alarm
        cw_client.put_metric_alarm(
            AlarmName='EC2_CPU_Utilization',
            ComparisonOperator='GreaterThanThreshold',
            EvaluationPeriods=3,
            MetricName='CPUUtilization',
            Namespace='AWS/EC2',
            # 60 seconds evaluation periods
            Period=60,
            Statistic='Average',
            Threshold=60.0,
            ActionsEnabled=True,
            # Terminate instance if threshold exceeded
            AlarmActions=[
                'arn:aws:automate:us-east-1:ec2:terminate'
            ],
            AlarmDescription='Alarm when server CPU exceeds 60%',
            Dimensions=[
                {
                    'Name': 'InstanceId',
                    'Value': instId
                },
            ],
            Unit='Seconds'
        )
        print("CloudWatch alarm successfully created...")

        # Alarm information
        a_name = f"Name: {cw_client.describe_alarms()['MetricAlarms'][0]['AlarmName']}\n"
        a_desc = f"Description: {cw_client.describe_alarms()['MetricAlarms'][0]['AlarmDescription']}\n"
        a_co = f"Comparison Operator: {cw_client.describe_alarms()['MetricAlarms'][0]['ComparisonOperator']}\n"
        a_ep = f"Evaluation Periods: {cw_client.describe_alarms()['MetricAlarms'][0]['EvaluationPeriods']}\n"
        a_mn = f"Metric Name: {cw_client.describe_alarms()['MetricAlarms'][0]['MetricName']}\n"
        a_ns = f"Namespace: {cw_client.describe_alarms()['MetricAlarms'][0]['Namespace']}\n"
        a_period = f"Period: {cw_client.describe_alarms()['MetricAlarms'][0]['Period']}\n"
        a_stat = f"Statistic: {cw_client.describe_alarms()['MetricAlarms'][0]['Statistic']}\n"
        a_thr = f"Threshold: {cw_client.describe_alarms()['MetricAlarms'][0]['Threshold']}\n"
        a_act = f"Actions: {cw_client.describe_alarms()['MetricAlarms'][0]['AlarmActions']}\n"
        a_dim = f"Dimensions: {cw_client.describe_alarms()['MetricAlarms'][0]['Dimensions']}\n"
        a_unit = f"Unit: {cw_client.describe_alarms()['MetricAlarms'][0]['Unit']}"

        alarm_info = f"{a_name}{a_desc}{a_co}{a_ep}{a_mn}{a_ns}{a_period}{a_stat}{a_thr}{a_act}{a_dim}{a_unit}"

        # Creates a text file and copies the cloudwatch alarm information
        sp.run("touch cloudwatch.txt", shell=True)
        sp.run(f"echo 'CloudWatch Alarm Information: \n\n{alarm_info}' > cloudwatch.txt", shell=True)
        print("CloudWatch alarm information successfully copied to 'cloudwatch.txt'...")

        # Enables monitoring on the instance
        instance.monitor()
        # Sleep the program for 3 minutes to allow monitoring
        time.sleep(180)

        metric_iterator = cloudwatch.metrics.filter(Namespace='AWS/EC2',
                                                    MetricName='CPUUtilization',
                                                    Dimensions=[{'Name': 'InstanceId', 'Value': instId}])

        metric = list(metric_iterator)[0]

        response = metric.get_statistics(StartTime=datetime.utcnow() - timedelta(minutes=3),
                                         EndTime=datetime.utcnow(),
                                         Period=60,
                                         Statistics=['Average'])

        # Print average CPU utilisation in periods of 60 seconds over 3 minutes
        print("Average CPU utilisation of EC2 instance:", response['Datapoints'][0]['Average'], response['Datapoints'][0]['Unit'])

    except Exception as error:
        print("An error occured when setting up CloudWatch monitoring.")
        print(error)


print("S3 BUCKET SETUP\n")
launch_bucket()

print("\n\nEC2 INSTANCE SETUP\n")
create_inst()
