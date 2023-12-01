import json
import os
def get_data(json_file_name):
   try:
       with open(json_file_name) as f:
           data = json.load(f)
           return data
   except Exception as e:
       print("Error: ", e)

DATABASES = get_data('mysite/env.json').get('DATABASES', 'key_not_found')
EMAIL_CONF= get_data('mysite/env.json').get('EMAIL_CONF', 'key_not_found')
