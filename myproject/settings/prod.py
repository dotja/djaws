from settings.shared import *
import boto3
from botocore.exceptions import ClientError
import json


DEBUG = False
ALLOWED_HOSTS = ['*']
AWS_REGION = 'eu-west-2'

ssm = boto3.client('ssm')
secret_key_param = ssm.get_parameter(Name='/Prod/DjangoSecret', WithDecryption=True)
SECRET_KEY = secret_key_param['Parameter']['Value']

def get_secret(my_secret_name, region=AWS_REGION):
    ##
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region
    )
    ##
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=my_secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            raise e
    else:
        if 'SecretString' in get_secret_value_response:
            return json.loads(get_secret_value_response['SecretString'])
        else:
            return base64.b64decode(get_secret_value_response['SecretBinary'])


db_creds = get_secret('ProdDBSecret')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': db_creds['assigned_name'],
        'USER': db_creds['username'],
        'PASSWORD': db_creds['password'],
        'HOST': db_creds['host'],
        'PORT': os.getenv('DB_PORT'),
    }
}


bucket_name_param = ssm.get_parameter(Name='/Prod/BucketName')
STATIC_URL = 'https://{0}.s3.{1}.amazonaws.com/'.format(bucket_name_param['Parameter']['Value'], AWS_REGION)


AWS_STORAGE_BUCKET_NAME = bucket_name_param['Parameter']['Value']
AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME
AWS_DEFAULT_ACL = 'public-read'


STATICFILES_DIRS = [ os.path.join(BASE_DIR, 'static') ]
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
