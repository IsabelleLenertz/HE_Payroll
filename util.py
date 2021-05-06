import datetime
import csv
import pandas as pd
import numpy as np
from datetime import datetime, date, time, timedelta
import json

fed = "federal_taxes"
ss_employer = "social_security_employer"
medicare_employer = "medicare_employer"
futa ="futa"
ss_employee = "social_security_employee"
medicare_employee = "medicare_employee"
ytd_ss_employer = "ytd_ss_employer"
ytd_medicare_employer = "ytd_medicare_employer"
ytd_futa = "ytd_futa"
ytd_ss_employee = "ytd_ss_employee"
ytd_medicare_employee = "ytd_medicare_employee"
gross = "gross"
net = "net"
cal = "california_taxes"
disability = "disability"
unemployment = "unemployment"
training = "training"
ytd_unemployment = "ytd_unemployment"
ytd_training = "ytd_training"
ytd_disability = "ytd_disability"


#classmethod date.fromisoformat(date_string)
#>>> from datetime import date
#>>> date.fromisoformat('2019-12-04')
# datetime.date(2019, 12, 4)
#tdelta = datetime.strptime(s2, FMT) - datetime.strptime(s1, FMT)
#    FMT = '%H:%M'


# get the hours worked for a week from start date (str: MM-DD-YYY)
def calculate_time_worked(start, end, timesheet):
    df = pd.read_csv(timesheet, header=0, parse_dates= False, infer_datetime_format = True)
    period = df.query('date >= @start and date <= @end')
    FMT = '%H:%M'
    #get hours worked
    daily_hours = period.apply(lambda r : datetime.strptime(r[2], FMT)  - datetime.strptime(r[1], FMT), axis=1)
    worked = daily_hours.aggregate(np.sum, 0)
    print(worked)
    #TODO get pto hours used
    #TODO get sick day hours used
    return (worked.total_seconds()/3600, 0, 0)


def create_json_stub(start, middle_sunday, middle_monday, end):
    # Get the hours per week (worked, over, pto, sick)
    reg_hours, overtime_hours, pto, sick = 0, 0, 0, 0
    hours, pto_temp, sick_temp = calculate_time_worked(start, middle_sunday , "timesheet_sample.csv")
    if(hours > 40):
        reg_hours += 40
        overtime_hours += (hours - 40)
    else:
        reg_hours += hours
    hours, pto_temp, sick_temp = calculate_time_worked(middle_monday, end , "timesheet_sample.csv")
    if(hours > 40):
        reg_hours += 40
        overtime_hours += (hours - 40)
    else:
        reg_hours += hours


    #Load tax info
    with open('taxes_2021.json') as f:
        taxrates = json.load(f)
    with open('david.json') as f:
        employee = json.load(f)
        
    # Apply pay-rate and over-time rate
    hours_dic = {"worked" : reg_hours, "sick" : sick, "pto": pto, "over": overtime_hours}
    wages = { gross : (reg_hours + pto + sick + overtime_hours*1.5)*employee['rate']}
    wages[net] = wages[gross]

    # Apply federal taxes
    federal_taxes = {
        ss_employer : taxrates[fed][ss_employer][0]*wages[gross]/100,
        ss_employee : taxrates[fed][ss_employee][0]*wages[gross]/100,
        medicare_employer : taxrates[fed][medicare_employer][0]*wages[gross]/100,
        medicare_employee : taxrates[fed][medicare_employer][0]*wages[gross]/100,
        futa : taxrates[fed][futa][0]*wages[gross]/100,
    }
    for tax in federal_taxes:
        if taxrates[fed][tax][2]:
            wages[net] = wages[net] - federal_taxes[tax]
            
    # Apply California taxes
    california_taxes = {
        unemployment: taxrates[cal][unemployment][0]*wages[gross]/100,
        training:  taxrates[cal][training][0]*wages[gross]/100,
        disability:  taxrates[cal][disability][0]*wages[gross]/100
    }
    
    for tax in california_taxes:
        if taxrates[cal][tax][2]:
            wages[net] = wages[net] - california_taxes[tax]

    print(wages)
    print(federal_taxes)
    print(california_taxes)


create_json_stub("04-26-2021", "04-28-2021", "04-29-2021", "04-30-2021")
        
    
    
    