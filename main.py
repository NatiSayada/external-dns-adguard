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
  return [ record for record in adguard.records if rule == record["domain"] ]


def handle_event(adguard: AdguardInstance, event : client.EventsV1Event):
  logger.info(f"Got an event of type {event['type']}")
  for rule in event["object"].spec.rules :
    if Config.DOMAIN_NAME in rule.host:
      logger.info(f"Checking if {rule.host} exists...")
      # Var records should contain currently existing records which match the IP of the ingress
      records = check_rewrite_exists(adguard, rule.host)
    
      if not (len(records) == len(event["object"].status.loadbalancer.ingress)) and (event["type"] == "ADDED"):
        try:
          lb_ip = event["object"].status.load_balancer.ingress[0].ip
        except TypeError:
          logger.info("No IP is set yet. Waiting for the MODIFIED event")
          continue
      elif not (len(records) == len(event["object"].status.loadbalancer.ingress)) and (event["type"] == "MODIFIED"):
        for ip in records:
          logger.info(f"Creating record {rule.host} with IP {ip}")
          resp: requests.Reponse = adguard.create_record(rule.host, ip)
          logger.info(f"Received response {resp.status_code}")
      
      elif (len(records) == len(event["object"].status.loadbalancer.ingress)) and (event["type"] == "DELETED"):
        for ip in records:
          logger.info(f"Deleting record {rule.host} with IP {ip}")
          resp : requests.Response = adguard.delete_record(rule.host, ip)
          logger.info(f"Received response {resp}")
      
      else:
          logger.info(f"Record {rule.host} exists. Skipping...")

    else:
      logger.info(f"Record {rule.host} does not match domain {Config.DOMAIN_NAME}. Skipping.")



def ingress_event(netV1: client.NetworkingV1Api, adguard: AdguardInstance):
  watcher = watch.Watch()
  while True:
    try:
      for event in watcher.stream(netV1.list_ingress_for_all_namespaces):
        Thread(target=handle_event, args=[adguard, event]).run()
    except client.exceptions.ApiException:
      logger.info("Watcher expired. Restarting")
      continue
    

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