'''
Script to process nbn coverage map csv files, transform and load into a MongoDB

Author: Rommel Poggenberg (29860571)
Date created: 19th April 2021 (TP2 2021)
'''

import csv
import pymongo
import pprint
import sys
import datetime

pp = pprint.PrettyPrinter(indent=4)

state_lookup={2:'New South Wales',3:'Victoria',4:'Queensland',5:'South Australia',6:'Western Australia',7:'Tasmania',8:'Northern Territory',9:'Australian Capital Territory'}
filter_tech={'Fibre to the Basement':'fttb', 'Fibre to the Curb':'fttc', 'Fibre to the Node':'fttn', 'Fibre to the Premises':'fttp', 'Fixed Wireless':'fixed_wireless', 'Hybrid Fibre Coaxial (HFC)':'hfc'}
filter_state={'Australian Capital Territory':'act', 'New South Wales':'nsw', 'Northern Territory':'nt', 'Queensland':'ql','South Australia':'sa', 'Tasmania':'tas', 'Victoria':'vic', 'Western Australia': 'wa'}
nbn_map_data={}

#Cut off date which nbn declared to be built 30th June 2020
nbn_build_deadline=datetime.datetime.strptime('30/06/2020 00:00:00', '%d/%m/%Y %H:%M:%S')

all_techs=['ALL_FixedWireless','ALL_FTTB','ALL_FTTC','ALL_FTTN','ALL_FTTP','ALL_HFC']

#Read CSV files
for tech in all_techs:
	with open('data\\'+tech+'.csv', newline='') as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:	
			#print(row)
			data={}
			data['Technology_Type']=row['Technology_Type']
			data['Ready_for_Service_Date']=row['Ready_for_Service_Date']
			try:
				if datetime.datetime.strptime(row['Ready_for_Service_Date']+' 00:00:00', '%d/%m/%Y %H:%M:%S') <= nbn_build_deadline:
					data['RFS_On_Schedule']=True
				else:
					data['RFS_On_Schedule']=False
			except:
				data['RFS_On_Schedule']=False
			data['Area_ID']=row['Area_ID']
			data['Service_Status']=row['Service_Status']
			data['state']=state_lookup[int(row['Area_ID'][0])]
			data['longitude']=row['longitude']
			data['latitude']=row['latitude']
			data['markerscale']=1
			
			if data['state'] in nbn_map_data.keys():
				if data['Technology_Type'] in nbn_map_data[data['state']].keys():
					map_records=nbn_map_data[data['state']][data['Technology_Type']]
					map_records.append(data)
					nbn_map_data[data['state']][data['Technology_Type']]=map_records
				else:
					nbn_map_data[data['state']][data['Technology_Type']]=[data]
			else:
				nbn_map_data[data['state']]={}
				nbn_map_data[data['state']][data['Technology_Type']]=[data]


#pp.pprint(nbn_map_data)
#sys.exit(0)

bar_chart_all={}
bar_chart_ontime={}
bar_chart_after={}

#Calculate areas within original build deadline
for state in nbn_map_data.keys():
	for tech in nbn_map_data[state].keys():
		for record in nbn_map_data[state][tech]:
			
			try:
				year=int(record['Ready_for_Service_Date'].split('/')[2])
			except:
				year=2024
				
			year=int(year)
			technology=record['Technology_Type']	
				
			#Schedule of all areas in all time
			if year in bar_chart_all.keys():
				if technology in bar_chart_all[year].keys():
					bar_chart_all[year][technology]=bar_chart_all[year][technology]+1
			else:
				bar_chart_all[year]=  {
				"Fibre to the Basement": 0,
				"Fibre to the Curb": 0,
				"Fibre to the Node": 0,
				"Fibre to the Premises": 0,
				"Fixed Wireless": 0,
				"Hybrid Fibre Coaxial (HFC)": 0,
				"year": str(year)
				}
				
				bar_chart_all[year][technology]=1
				
			#Find areas which were build on schedule	
			if record['RFS_On_Schedule']==True:
				if year in bar_chart_ontime.keys():
					if technology in bar_chart_ontime[year].keys():
						bar_chart_ontime[year][technology]=bar_chart_ontime[year][technology]+1
				else:
					bar_chart_ontime[year]=  {
					"Fibre to the Basement": 0,
					"Fibre to the Curb": 0,
					"Fibre to the Node": 0,
					"Fibre to the Premises": 0,
					"Fixed Wireless": 0,
					"Hybrid Fibre Coaxial (HFC)": 0,
					"year": str(year)
					}
					
					bar_chart_ontime[year][technology]=1	
					
			#Find areas which will be built after the deadline		
			if record['RFS_On_Schedule']==False:
				if year in bar_chart_after.keys():
					if technology in bar_chart_after[year].keys():
						bar_chart_after[year][technology]=bar_chart_after[year][technology]+1
				else:
					bar_chart_after[year]=  {
					"Fibre to the Basement": 0,
					"Fibre to the Curb": 0,
					"Fibre to the Node": 0,
					"Fibre to the Premises": 0,
					"Fixed Wireless": 0,
					"Hybrid Fibre Coaxial (HFC)": 0,
					"year": str(year)
					}
					
					bar_chart_after[year][technology]=1						
			
#Get all schedules in a dictionary
raw_values={'all':bar_chart_all,'ontime':bar_chart_ontime,'after':bar_chart_after}		
rollout_schedule={}
for key in raw_values:
	for year in sorted(raw_values[key].keys()):
		if key in rollout_schedule.keys():
			values=rollout_schedule[key]
			values.append(raw_values[key][year])
			rollout_schedule[key]=values
		else:
			rollout_schedule[key]=[raw_values[key][year]]
		
#Write dictionaries to mongodb
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["nbn"]
col = db["map"]
col2 = db["chart"]

for state in nbn_map_data.keys():
	for tech in nbn_map_data[state].keys():
		print(state, tech)
		col.insert_one({'technology_type':filter_tech[tech],'state':filter_state[state],'results':nbn_map_data[state][tech]})			
		
for timeline in rollout_schedule.keys():
	print(timeline)
	col2.insert_one({'schedule':timeline,'results':rollout_schedule[timeline]})
				
