import os
from dotenv import load_dotenv

load_dotenv()

class Config(object):
  DOMAIN_NAME = os.environ.get("DOMAIN_NAME")
  ADGUARD_DNS = os.environ.get("ADGUARD_DNS")
  ADGUARD_USER = os.environ.get("ADGUARD_USER")
  ADGUARD_PASS = os.environ.get("ADGUARD_PASS")
  MODE = os.environ.get("MODE") or "PROD"
