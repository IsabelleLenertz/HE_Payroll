from os import name
from constants import *
from pymongo import MongoClient, mongo_client, results
import json
from datetime import datetime, date, time, timedelta


client = MongoClient(mongo_adress)
db = client[payroll_db]
Collection = db[employee_collection]

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
        self.ID = { mongo_id : Collection.find_one(self.employee_identifiers)[mongo_id]}

    def get_employee(self):
        raw_dic = Collection.find_one(self.ID)
        return raw_dic

    def add_pto(self, pto_added):
        result = Collection.update_one(self.ID, {'$inc': {pto+"."+received: pto_added}})
        return (result.modified_count == 1)

    def add_hours(self, hours):
        previous_state = Collection.find_one(self.ID)
        previous_sick = previous_state[sick]
        print("PREVIOUS STATE: ", previous_state)
        sick_earned = int((previous_state[ytd_hours]+hours)/hours_per_sick - previous_state[sick][received])
        result = Collection.update_one(self.ID, {'$inc' : {ytd_hours: hours, sick+"."+received : sick_earned}})
        return (result.modified_count == 1)
    
    def use_PTO(self, hours):
        result = Collection.update_one(self.ID, {'$inc' : {pto+"."+used: hours}})
        return (result.modified_count == 1)

    def use_sick(self, hours):
        result = Collection.update_one(self.ID, {'$inc' : {sick+"."+used: hours}})
        return (result.modified_count == 1)

    # need to be replaced of private
    def create_paystub(self, hours_worked, ptohours_used, sickhours_used, wages_earned, start, end, check_used, califoria_taxes, federal_taxes):
        # Updates general state
        self.add_hours(hours_worked)
        self.use_PTO(ptohours_used)
        self.use_sick(sickhours_used)
        advance_balance = self.get_employee()[advance_b]
        if advance_balance >= wages_earned[net]:
                result_balance = Collection.update_one(self.ID, {'$inc' : {advance_b: - wages_earned[net]}})
                wages_earned[net] = 0
        elif advance_balance > 0:
                wages_earned[net] = wages_earned[net] - advance_balance
                result_balance = Collection.update_one(self.ID, {'$set' : {advance_b: 0}})
        current_state = Collection.find_one(self.ID)

        # Creates a paystub for the givent perioud
        paystub = {
            pp_start : start,
            pp_end : end,
            check : check_used,
            pto_used : ptohours_used,
            sick_used : sickhours_used,
            worked : hours_worked,
            balance : {
                pto : current_state[pto][received] - current_state[pto][used],
                sick :  current_state[sick][received] - current_state[sick][used],
                advance_b: current_state[advance_b],
            },
            wages: wages_earned,
            fed : federal_taxes,
            cal : califoria_taxes
        }

        result_stub = Collection.update_one(self.ID, {'$addToSet': { paystubs  : paystub},'$inc': { ytd_wages +"."+ytd_gross : wages_earned[gross], ytd_wages +"."+ytd_net : wages_earned[net]} })

        # update end of quarter totals
        end_date = date.fromisoformat(end)
        if end_date <= end_q1:
            result_quarter = Collection.update_one(self.ID, {'$inc': { 'quarters[0].hours' : hours_worked, 'quarters[0].gross': wages_earned[gross], 'quarters[0].net': wages_earned[net] }})
        elif end_date <= end_q2:
            result_quarter = Collection.update_one(self.ID, {'$inc': { 'quarters[1].hours' : hours_worked, 'quarters[1].gross': wages_earned[gross], 'quarters[1].net': wages_earned[net] }})
        elif end_date <= end_q3:
            result_quarter = Collection.update_one(self.ID, {'$inc': { 'quarters[2].hours' : hours_worked, 'quarters[2].gross': wages_earned[gross], 'quarters[2].net': wages_earned[net] }})
        else:
            result_quarter = Collection.update_one(self.ID, {'$inc': { 'quarters[3].hours' : hours_worked, 'quarters[3].gross': wages_earned[gross], 'quarters[3].net': wages_earned[net] }})
        return (result_stub.modified_count == 1 and result_quarter.modified_count == 1 and result_balance.modified_count == 1)
