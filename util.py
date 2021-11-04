import datetime
import csv
from mongo_client import delete_employee
import pandas as pd
import numpy as np
from datetime import datetime, date, time, timedelta
import json
from constants import *
from pymongo import MongoClient, mongo_client
from pymongo.errors import _format_detailed_error
import mongo_client

# get the hours worked for a week from start date to end date (str: MM-DD-YYY)
def calculate_time_worked(start, end, timesheet):
    reg_hours, overtime_hours, pto_hours, sick_hours = 0, 0, 0, 0
    df = pd.read_csv(timesheet, header=0, parse_dates= False, infer_datetime_format = True)
    FMT = '%H:%M'
    period = df.query('date >= @start and date <= @end')
    #get hours worked
    daily_hours = period.apply(lambda r : datetime.strptime(r[2], FMT)  - datetime.strptime(r[1], FMT), axis=1)
    daily_other = period.sum(numeric_only = True)
    pto_hours = daily_other[1]
    sick_hours = daily_other[0]
    reg_hours = daily_hours.aggregate(np.sum, 0)
    reg_hours = reg_hours.total_seconds()/3600
    if reg_hours > 40:
        overtime_hours = reg_hours - 40
        reg_hours = 40
    return (reg_hours, overtime_hours, pto_hours, sick_hours)

def update_db(start, end, timesheet, employee_file, check_num):
    # Get the hours per week (worked, over, pto, sick)
    reg_hours, overtime_hours, pto, sick = calculate_time_worked(start, end , timesheet)

    # Load tax info
    with open('taxes_2021.json') as f:
        taxrates = json.load(f)
    with open(employee_file) as f:
        employee = json.load(f)
    
    employee_connection = mongo_client.Mongo("Stephanie", "Langerveld", 2021)
        
    # Apply pay-rate and over-time rate
    hours_dic = { worked : reg_hours, sick_used : sick, pto_used: pto, over_worked : overtime_hours}
    wages = { gross : (reg_hours + pto + sick + overtime_hours*1.5)*employee['rate']}

    # Apply federal taxes
    federal_taxes = {
        ss_employer : taxrates[fed][ss_employer][0]*wages[gross]/100,
        ss_employee : taxrates[fed][ss_employee][0]*wages[gross]/100,
        medicare_employer : taxrates[fed][medicare_employer][0]*wages[gross]/100,
        medicare_employee : taxrates[fed][medicare_employer][0]*wages[gross]/100,
        futa : taxrates[fed][futa][0]*wages[gross]/100,
    }
    wages[w_notaxes], wages[w_taxes] = 0, 0
    for tax in federal_taxes:
        if taxrates[fed][tax][2]:
            wages[w_taxes] = wages[w_taxes] + federal_taxes[tax]
        else:
            wages[w_notaxes]  = wages[w_notaxes]  + federal_taxes[tax]
            
    # Apply California taxes
    california_taxes = {
        unemployment: taxrates[cal][unemployment][0]*wages[gross]/100,
        training:  taxrates[cal][training][0]*wages[gross]/100,
        disability:  taxrates[cal][disability][0]*wages[gross]/100
    }
    
    for tax in california_taxes:
        if taxrates[cal][tax][2]:
            wages[w_taxes] = wages[w_taxes] + california_taxes[tax]
        else:
            wages[w_notaxes] = wages[w_notaxes] + california_taxes[tax]


    wages[net] = wages[gross] - wages[w_taxes]
    
    return employee_connection.create_paystub(hours_dic[worked], hours_dic[pto_used], hours_dic[sick_used], wages, start, end, check_num, california_taxes, federal_taxes)

