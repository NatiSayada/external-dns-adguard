import sys
import os
import asyncio
#import multiprocessing
import logging

from threading import Thread

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from kubernetes import client, config, watch
import requests
import time
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

from config import Config
from adguard import AdguardInstance

load_dotenv()

session = requests.Session()
session.auth = (Config.ADGUARD_USER, Config.ADGUARD_PASS)

logger = logging.getLogger("external-dns-adguard")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def check_rewrite_exists(adguard: AdguardInstance, rule):
  for record in adguard.records:
    if rule == record.domain:
      return True
  return False


def ingress_event(netV1: client.NetworkingV1Api, adguard: AdguardInstance):
  watcher = watch.Watch()
  for event in watcher.stream(netV1.list_ingress_for_all_namespaces):

    record_exists == False
    for rule in event["object"].spec.rules:
      if Config.DOMAIN_NAME in rule.host:
        record_exists = check_rewrite_exists(rule.host)
      
      if not record_exists and (event["type"] == "ADDED" or event["type"] == "MODIFIED"):
        retry_count = 0
        lb_ip = ""
        while (retry_count < 6) and (lb_ip == ""):
          time.sleep(10)
          lb = event["object"].status.load_balancer.ingress[0]
          if "ip" in lb:
            logger.info(f'Found loadbalancer IP for ingress {rule.host}: {lb["ip"]}')
            lb_ip = lb["ip"]
          else:
            logger.warn(f'Failed to find an IP for ingress {rule.host}')
        if lb_ip == "":
          error = "Failed to get an IP address for ingress"
          logger.error(error)
          raise Exception(error)
        else:
          adguard.create_record(rule.host, lb_ip)
      
      elif record_exists and event["type"] == "DELETED":
        lb_ip = event["object"].status.load_balancer.ingress[0].ip
        adguard.delete_record(rule.host, lb_ip)

if __name__ == "__main__":
  for key,val in Config.__dict__.items():
    if not str(key).startswith("__"):
      if val == None or val == "":
        logger.error(f'Environment Variable {key} is not set. Exiting')
        sys.exit(0)

  force_deletion = False

  for flag in sys.argv[1:]:
    if "-f" == flag or "--force" == flag:
      force_deletion = True

  try:
    if Config.MODE == "DEV":
      config.load_kube_config()
    elif Config.MODE == "PROD":
      config.load_incluster_config()
    else:
      logger.error("Incorrect MODE type")
      sys.exit(0)

    logger.info("Starting application")

    netV1 = client.NetworkingV1Api()
    adguard = AdguardInstance()

    thread = Thread(target=ingress_event, args=[netV1, adguard])
    thread.run()
    thread.join(5)

  except (KeyboardInterrupt, SystemExit):
    pass
  finally:
    logger.info("Interrupt Received")