import requests

from config import Config

class AdguardInstance:

  def __init__(self, address=Config.ADGUARD_DNS, username=Config.ADGUARD_USER, password=Config.ADGUARD_PASS, scheme=Config.ADGUARD_SCHEME):
    self.__username = username
    self.__password = password
    self.__url = f"{scheme}://{address}"
    self.__records = self.__get_records()

  def __get_records(self):
    url = f"{self.__url}/control/rewrite/list"
    resp = requests.get(url=url, auth=(self.__username, self.__password))
    resp.raise_for_status()
    data = resp.json()
    return data

  def create_record(self, domain:str, ip:str):
    record = {
      "domain": domain,
      "answer": ip
    }
    url = f"{self.__url}/control/rewrite/add"
    resp = requests.post(url=url, json=record, auth=(self.__username, self.__password))
    resp.raise_for_status()
    self.__records = self.__get_records()
    return resp

  def delete_record(self, domain:str, ip:str):
    record = {
      "domain": domain,
      "answer": ip
    }
    url = f"{self.__url}/control/rewrite/delete"
    resp = requests.post(url=url, json=record, auth=(self.__username, self.__password))
    resp.raise_for_status()
    self.__records = self.__get_records()
    return resp


  @property
  def records(self):
    return self.__records