#!/usr/bin/env python3

import boto3
import datetime

from os import environ


AWS_ACCESS_KEY = environ.get('AWS_ACCESS_KEY_ID', 'some access key')
AWS_SECRET_KEY = environ.get('AWS_SECRET_ACCESS_KEY', 'super secret')
AWS_REGION = environ.get('AWS_REGION', 'us-east-2')

# could be replaced to obtaining info
PRICE_OD = {
    't2.nano': 0.0058,
    't2.micro': 0.0116,
    't3.nano': 0.0108,
    't3.micro': 0.0104
}

START_DATE = datetime.datetime.today() - datetime.timedelta(days = 7)


def average(lst):
    if lst:
        return sum(lst) / len(lst)
    else:
        return 0

def average_spot_price(platform, instance_type, az):
    res = cli.describe_spot_price_history(
        StartTime = START_DATE, 
        Filters=[
            {'Name': 'product-description', 
             'Values': [platform,]}], 
        InstanceTypes = [instance_type], 
        AvailabilityZone = az, 
        # it might be replaced to iterations
        MaxResults=10000)

    return average([ float(_['SpotPrice']) for _ in res['SpotPriceHistory']])


def print_header():
    fields = ['Name',
            'InstanceType',
            'AZ',
            'PlatformDet',
            'PriceOD',
            'PriceSpot',
            'PriceDiff']

    print(' '.join(fields))
    print(' '.join(['-'*len(el) for el in fields]))


def print_table(instances, images):
    if not instances:
        return
    for i in instances:
       platform_os = images[i['ImageId']]
       avg_spot_price = average_spot_price(
           platform_os,
           i['InstanceType'],
           i['Placement']['AvailabilityZone'])
       price_delta = PRICE_OD[i['InstanceType']] - avg_spot_price

       instance_name = i['InstanceId']
       for tag in i['Tags']:
        if tag.get('Key') == 'Name':
          instance_name = tag['Value']

       print('%s '*7 % (
             instance_name,
             i['InstanceType'],
             i['Placement']['AvailabilityZone'],
             platform_os,
             PRICE_OD[i['InstanceType']],
             "{:10.4f}".format(avg_spot_price),
             "{:10.4f}".format(price_delta)
             ))

def get_images_info(conn, ami_ids):
    images = conn.describe_images(ImageIds=ami_ids)['Images']
    res = {}
    for _ in images:
        res[_['ImageId']] = _['PlatformDetails']
    return res



cli = boto3.client('ec2',
        region_name = AWS_REGION,
        aws_access_key_id = AWS_ACCESS_KEY,
        aws_secret_access_key = AWS_SECRET_KEY
    )

filters = [{'Name': 'instance-type',
            'Values': ['t2.nano',
                    't2.micro',
                    't3.nano',
                    't3.micro'],}]

reservations = cli.describe_instances(Filters = filters)['Reservations']

print_header()
for _ in reservations:
    ami_ids = [el['ImageId'] for el in _['Instances']]
    print_table(_['Instances'], get_images_info(cli, ami_ids))
