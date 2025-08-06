import boto3
from flask import current_app
from werkzeug.utils import secure_filename

s3 = boto3.client('s3')
BUCKET = current_app.config.get('S3_BUCKET', 'chamalink-uploads')

def upload_file_to_s3(file, filename=None):
    if not filename:
        filename = secure_filename(file.filename)
    s3.upload_fileobj(file, BUCKET, filename)
    return f'https://{BUCKET}.s3.amazonaws.com/{filename}'

def download_file_from_s3(filename):
    fileobj = s3.get_object(Bucket=BUCKET, Key=filename)
    return fileobj['Body'].read()
