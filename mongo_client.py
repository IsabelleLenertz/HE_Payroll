from os import name
from constants import *
from pymongo import MongoClient, mongo_client
from pymongo.errors import _format_detailed_error
import json



mongo_client = "mongodb://127.0.0.1:27017"


client = MongoClient('mongodb://127.0.0.1:27017')
db = client["PayRoll"]
Collection = db["employees"]

def add_employee(file_name):
    with open("_private/steph.json") as file:
            file_data = json.load(file)
    Collection.insert_one(file_data)
    return file_data

class Mongo:
    def __init__(self,first_name, last_name):
        self.last_name = last_name
        self.first_name = first_name
    
    def get_employee_json(self):
        raw_dic = Collection.find_one({fn : self.first_name, ln : self.last_name})
        return raw_dic

    def add_pto(self, pto_added):
        return Collection.update_one({fn : self.first_name, ln : self.last_name}, {'$inc': {'PTO.balance': pto_added, 'PTO.received': pto_added}})
    
    def update_sick_days(self, new_total_value):
        used = Collection.find_one({fn : self.first_name, ln : self.last_name})
        used = used['sick']['used']
        result = Collection.update_one({fn : self.first_name, ln : self.last_name}, {'$set' : {'sick.received': new_total_value, 'sick.balance' : new_total_value-used}})
        print("modified count: ", result.modified_count)
        return (result.modified_count == 1)

#raw_data = add_employee("_private/steph.json")
#print("raw Data: ", raw_data)
employee = Mongo('vv', 'vv')
#print("found in db: ", employee.get_employee_json())
employee.add_pto(6)
print("found in db: ", employee.get_employee_json())
employee.update_sick_days(10)
print("found in db: ", employee.get_employee_json())

