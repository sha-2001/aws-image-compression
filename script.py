import boto3
import os
from urllib.parse import urlparse
# AWS credentials
aws_access_key_id = 'AKIATH57ANBYLRJVBWN5'
aws_secret_access_key = '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'
region_name = 'ap-south-1'
# S3 bucket information
src_bucket_name = 'frikly-images1'
dst_bucket_name = 'frikly-images-thumbnail'
# CloudFront information
cf_distribution_id = 'arn:aws:cloudfront::223202011248:distribution/EBSCE5MJE1OJY'
cf_domain_name = 'https://d17iset1k7k80v.cloudfront.net'
# Connect to S3 and CloudFront
s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name=region_name)
cf = boto3.client('cloudfront', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name=region_name)
# Connect to MySQL
db_host = 'localhost'
db_port = '3306'
db_name = 'frikly'
db_user = 'root'
db_password = 'ubuntu'
import mysql.connector
cnx = mysql.connector.connect(user=db_user, password=db_password, host=db_host, database=db_name)
cursor = cnx.cursor()
# Get the image URLs from the 'Image1' column of the 'frikly' table
query = "SELECT Image1 FROM product"
cursor.execute(query)
rows = cursor.fetchall()
# Iterate over the image URLs and compress each image
for row in rows:
    # Get the image URL and file name
    image_url = row[0]
    file_name = os.path.basename(urlparse(image_url).path)
    # Compress the image using Pillow library
    from PIL import Image
    # Download the image from S3
    obj = s3.get_object(Bucket=src_bucket_name, Key=file_name)
    image = Image.open(obj['Body'])
    # Compress the image
    max_size = (256, 256)
    image.thumbnail(max_size)
    # Upload the compressed image to S3
    thumbnail_key = f'{os.path.splitext(file_name)[0]}-thumbnail.jpg'
    with open(thumbnail_key, 'wb') as f:
        image.save(f, "JPEG", optimize=True)
    s3.upload_file(thumbnail_key, dst_bucket_name, thumbnail_key)
    
    # Generate a CloudFront URL for the compressed image
    thumbnail_url = f'https://{cf_domain_name}/{thumbnail_key}'
    dist_info = cf.get_distribution(Id=cf_distribution_id)
    cf_url = dist_info['Distribution']['DomainName']
    thumbnail_url = thumbnail_url.replace(cf_domain_name, cf_url)
    # Update the 'Image_thumbnail' column in the 'frikly' table with the CloudFront URL
    update_query = f"UPDATE frikly SET Image_thumbnail = '{thumbnail_url}' WHERE Image1 = '{image_url}'"
    cursor.execute(update_query)
    cnx.commit()
    # Print the CloudFront URL of the compressed image
    print("Thumbnail created: s3://{}/{} -> {}".format(dst_bucket_name, thumbnail_key, thumbnail_url))
    # Close the MySQL connection
    cursor.close()
    cnx.close()