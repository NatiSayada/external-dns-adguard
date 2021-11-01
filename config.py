import os
from dotenv import load_dotenv

load_dotenv()

class Config(object):
  DOMAIN_NAME = os.environ.get("DOMAIN_NAME")
  ADGURED_DNS = os.environ.get("ADGURED_DNS")
  ADGURED_USER = os.environ.get("ADGURED_USER")
  ADGURED_PASS = os.environ.get("ADGURED_PASS")
  MODE = os.environ.get("MODE") or "PROD"