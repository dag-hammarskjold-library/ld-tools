import os
from dlx import DB
from dlx.marc import Bib, Auth
import boto3

class DevelopmentConfig(object):
    client = boto3.client('ssm')
    secret_key = client.get_parameter(Name='metadata_cache_key')['Parameter']['Value']
    connect_string = client.get_parameter(Name='dev-dlx-connect-string')['Parameter']['Value']
    dbname = 'dev_undlFiles'

class ProductionConfig(object):
    client = boto3.client('ssm')
    secret_key = client.get_parameter(Name='metadata_cache_key')['Parameter']['Value']
    connect_string = client.get_parameter(Name='connect-string')['Parameter']['Value']
    dbname = 'undlFiles'

def get_config():
    flask_env = os.environ.setdefault('FLASK_ENV', 'development')
    
    if flask_env == 'production':
        return ProductionConfig
    elif flask_env == 'development':
        return DevelopmentConfig
    else:
        raise Exception('Environment variable "FLASK_ENV" set to invalid value "{}"'.format(flask_env))

Config = get_config()