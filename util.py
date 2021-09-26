import datetime
import csv
import pandas as pd
import numpy as np
from datetime import datetime, date, time, timedelta
import json
from constants import *
from pymongo import MongoClient, mongo_client
from pymongo.errors import _format_detailed_error



mongo_client = "mongodb://127.0.0.1:27017"

#importing jason basic data
""" with open("_private/steph.json") as file:
        file_data = json.load(file)
        print(file_data)
client = MongoClient('mongodb://127.0.0.1:27017')
db = client["PayRoll"]
Collection = db["emploees"]
Collection.insert_one(file_data) """
#classmethod date.fromisoformat(date_string)
#>>> from datetime import date
#>>> date.fromisoformat('2019-12-04')
# datetime.date(2019, 12, 4)
#tdelta = datetime.strptime(s2, FMT) - datetime.strptime(s1, FMT)
#    FMT = '%H:%M'


# get the hours worked for a week from start date (str: MM-DD-YYY)
def calculate_time_worked(start, num_weeks, timesheet):
    reg_hours, overtime_hours, pto_hours, sick_hours = 0, 0, 0, 0
    df = pd.read_csv(timesheet, header=0, parse_dates= False, infer_datetime_format = True)
    FMT = '%H:%M'
    for i in range(num_weeks):
        later = (date.fromisoformat(start) + timedelta(days=6)).isoformat()
        print(start)
        print(later)
        period = df.query('date >= @start and date <= @later')
        #get hours worked
        daily_hours = period.apply(lambda r : datetime.strptime(r[2], FMT)  - datetime.strptime(r[1], FMT), axis=1)
        daily_other = period.sum(numeric_only = True)
        pto_hours = pto_hours + daily_other[1]
        sick_hours = sick_hours + daily_other[0]
        worked = daily_hours.aggregate(np.sum, 0)
        worked = worked.total_seconds()/3600
        if worked > 40:
            reg_hours = reg_hours + 40
            overtime_hours = overtime_hours + worked - 40
        else:
            reg_hours = reg_hours + worked
        start = (date.fromisoformat(later) + timedelta(days=1)).isoformat()
    return (reg_hours, overtime_hours, pto_hours, sick_hours)

def calculate_PTO_sickdays_ballance(hiredate, end_of_period, employee):
    pass

def create_json_stub(start, num_weeks, timesheet):
    # Get the hours per week (worked, over, pto, sick)
    reg_hours, overtime_hours, pto, sick = calculate_time_worked(start, num_weeks , timesheet)

    #Load tax info
    with open('taxes_2021.json') as f:
        taxrates = json.load(f)
    with open('_private/steph.json') as f:
        employee = json.load(f)
        
    # Apply pay-rate and over-time rate
    hours_dic = {"worked" : reg_hours, "sick" : sick, "pto": pto, "over": overtime_hours}
    wages = { gross : (reg_hours + pto + sick + overtime_hours*1.5)*employee['rate']}

    # Apply federal taxes
    federal_taxes = {
        ss_employer : taxrates[fed][ss_employer][0]*wages[gross]/100,
        ss_employee : taxrates[fed][ss_employee][0]*wages[gross]/100,
        medicare_employer : taxrates[fed][medicare_employer][0]*wages[gross]/100,
        medicare_employee : taxrates[fed][medicare_employer][0]*wages[gross]/100,
        futa : taxrates[fed][futa][0]*wages[gross]/100,
    }
    wage_applicable_taxes = 0
    non_wage_taxes = 0
    for tax in federal_taxes:
        if taxrates[fed][tax][2]:
            wage_applicable_taxes = wage_applicable_taxes + federal_taxes[tax]
            print("subtracting", federal_taxes[tax])
        else:
            non_wage_taxes = non_wage_taxes + federal_taxes[tax]
            
    # Apply California taxes
    california_taxes = {
        unemployment: taxrates[cal][unemployment][0]*wages[gross]/100,
        training:  taxrates[cal][training][0]*wages[gross]/100,
        disability:  taxrates[cal][disability][0]*wages[gross]/100
    }
    
    for tax in california_taxes:
        if taxrates[cal][tax][2]:
            wage_applicable_taxes = wage_applicable_taxes + california_taxes[tax]
            print("subtracting", california_taxes[tax])
        else:
            non_wage_taxes = non_wage_taxes + california_taxes[tax]


    wages[net] = wages[gross] - wage_applicable_taxes

    print("Employee: ", employee)
    print("Hours: ", hours_dic)
    print("Wages: ", wages)
    print("Federal taxes: ", federal_taxes)
    print("California taxes: ", california_taxes)
    print("wages applicable taxes: ", wage_applicable_taxes)
    print("non wage taxes: ", non_wage_taxes )
    print("total taxes: ", non_wage_taxes + wage_applicable_taxes)
    return hours_dic, wages, federal_taxes, california_taxes, wage_applicable_taxes, non_wage_taxes

def print_paystub(info, employee):
    precision = "{:.2f}"
    "Paystub\nEmployee: \n\tName: %s\n\tDate of Birth: %s\n\t Social Security Number: %s\n\t"

#print(create_json_stub("2021-05-31", 15, "_private/steph_timesheet_2021.csv"))

print(create_json_stub("2021-09-25", 1, "_private/steph_timesheet_2021.csv"))


# hours_dic2, wages2, federal_taxes2, california_taxes2, wage_applicable_taxes2, non_wage_taxes2 = create_json_stub("2021-05-10",2, "_private/david_timesheet_2021.csv")
# hours_dic3, wages3, federal_taxes3, california_taxes3, wage_applicable_taxes3, non_wage_taxes3 = create_json_stub("2021-05-24",2, "_private/david_timesheet_2021.csv")

""" print("unemployment", california_taxes[unemployment] + california_taxes2[unemployment] + california_taxes3[unemployment])
print("training, ", california_taxes[training] + california_taxes2[training]+ california_taxes3[training])
print("disab, ", california_taxes[disability] + california_taxes2[disability] + california_taxes3[disability])
print("ss_er, ", federal_taxes[ss_employer] + federal_taxes2[ss_employer] + federal_taxes3[ss_employer])
print("medicare_ee, ", federal_taxes[medicare_employee] +  federal_taxes2[medicare_employee] +  federal_taxes3[medicare_employee])
print("ss_ee, ", federal_taxes[ss_employee] + federal_taxes2[ss_employee] + federal_taxes3[ss_employee])
print("medicare_er, ", federal_taxes[medicare_employer] +  federal_taxes2[medicare_employer] +  federal_taxes3[medicare_employer])
print("futa, ", federal_taxes[futa] + federal_taxes2[futa] + federal_taxes3[futa])
print("wages applicable taxes, ", wage_applicable_taxes + wage_applicable_taxes2  + wage_applicable_taxes3)
print("non wage taxes", non_wage_taxes + non_wage_taxes2 + non_wage_taxes3)
print("net: ", wages[net] + wages2[net] + wages3[net])
print("gross: ", wages[gross] + wages2[gross] + wages3[gross])
print("hours, ", hours_dic["worked"] + hours_dic2["worked"] + hours_dic3["worked"])
 """


        
    
    
    