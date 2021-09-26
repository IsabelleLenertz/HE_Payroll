from os import name
from constants import *
from pymongo import MongoClient, mongo_client, results
from pymongo.errors import _format_detailed_error
import json



mongo_client = "mongodb://127.0.0.1:27017"


client = MongoClient('mongodb://127.0.0.1:27017')
db = client["PayRoll"]
Collection = db["employees"]

def add_employee(file_name):
    with open(file_name) as file:
        file_data = json.load(file)
    result = Collection.insert_one(file_data)
    return file_data

def delete_employee(file_name):
    with open(file_name) as file:
        file_data = json.load(file)
    result = Collection.delete_one({fn: file_data[fn], ln: file_data[ln]})
    return file_data

class Mongo:
    def __init__(self,first_name, last_name, current_year):
        self.employee_identifiers = {
            ln: last_name,
            fn : first_name,
            year: current_year
        }
        self.ID = { "_id" : Collection.find_one(self.employee_identifiers)["_id"]}


    def get_employee(self):
        raw_dic = Collection.find_one(self.ID)
        return raw_dic

    def add_pto(self, pto_added):
        result = Collection.update_one(self.ID, {'$inc': {'PTO.received': pto_added}})
        return (result.modified_count == 1)

   
    def add_hours(self, hours):
        previous_state = Collection.find_one(self.ID)
        previous_sick = previous_state["sick"]
        print(previous_sick)
        sick_earned = (previous_state['total_hours']+hours)/hours_per_sick - previous_state['sick']['received']
        result = Collection.update_one(self.ID, {'$inc' : {'total_hours': hours, 'sick.received' : sick_earned}})
        return (result.modified_count == 1)
    
    def use_PTO(self, hours):
        result = Collection.update_one(self.ID, {'$inc' : {'PTO.used': hours}})
        return (result.modified_count == 1)

    def use_sick(self, hours):
        result = Collection.update_one(self.ID, {'$inc' : {'sick.used': hours}})
        return (result.modified_count == 1)

    # need to be replaced of private
    def create_paystub(self, hours_worked, pto_used, sickhours_used, gross, net, start, end, check):
        # Updates general state
        self.add_hours(hours_worked)
        self.use_PTO(pto_used)
        self.use_sick(sickhours_used)
        advance_balance = self.get_employee()['advance_balance']
        if advance_balance >= net:
                result = Collection.update_one(self.ID, {'$dec' : {'advance_balance': net}})
                net = 0
        elif advance_balance > 0:
                net = net - advance_balance
                result = Collection.update_one(self.ID, {'$set' : {'advance_balance': 0}})
        current_state = Collection.find_one(self.ID)
        paystub = {
            "payperiod_start" : start,
            "payperiod_end" : end,
            "check_number" : check,
            "pto_used" : pto_used,
            "sick_days_used" : sickhours_used,
            "hours_worked" : hours_worked,
            "balance" : {
                "pto" : current_state["PTO"]["received"] - current_state["PTO"]["used"],
                "sick_days" :  current_state["sick"]["received"] - current_state["sick"]["used"],
                "advance": current_state["advance_balance"],
                "gross_salary": net
                },
            "net_salary": gross
        }
        # Creates a paystub for the givent perioud
        result = Collection.update_one(self.ID, {'$push': {'paystubs' : paystub}})
        return (result.modified_count == 1)


print("employee removed: ", delete_employee("_private/steph.json"))
raw_data = add_employee("_private/steph.json")
print("employee added with state: ", raw_data)
employee = Mongo(raw_data[fn], raw_data[ln], raw_data[year])
print("found in db: ", employee.get_employee())
print("adding 6 PTO: ", employee.add_pto(6))
print("new state: ", employee.get_employee())
print("adding 62 hours: ", employee.add_hours(62))
print("new state: ", employee.get_employee())
print("using 1 sick hour: ", employee.use_sick(1))
print("new state: ", employee.get_employee())

