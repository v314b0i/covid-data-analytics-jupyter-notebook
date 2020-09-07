#!/usr/bin/env python
# coding: utf-8

# In[5]:


import csv
import json
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt


# In[3]:


###downloading data (from multiple sources)
import requests

#source 1 https://covid.ourworldindata.org/data/owid-covid-data.csv
r=requests.get('https://covid.ourworldindata.org/data/owid-covid-data.csv', allow_redirects=True)
if r.status_code<200 or r.status_code>210:
    print('Error downloading OWID data')
else:
    open('owid-covid-data_pydw.csv','wb').write(r.content)
print('downloading data 1/3')

#source 2 https://covid.ourworldindata.org/data/owid-covid-data.csv
r0=requests.get('https://api.covid19api.com/all', allow_redirects=True)
r1=requests.get('https://api.covid19api.com/total/country/australia', allow_redirects=True) #aus data in all is state wise only?? not like usa
if r0.status_code not in range(200,211) or r1.status_code not in range(200,211):
    print('Error downloading the John H. data from covid19api.com')
else:
    open('allJH_pydw.json','wb').write(r0.content)
    open('ausJH_pydw.json','wb').write(r1.content)
print('downloading data 2/3') 

#source 3 covid19india.org
r=requests.get('https://api.covid19india.org/data.json', allow_redirects=True)
if r.status_code<200 or r.status_code>210:
    print('Error downloading covid19india.org data')
else:
    open('dataIN_pydw.json', 'wb').write(r.content)
print('downloading data 2.5/3')


r=requests.get('https://api.covid19india.org/v3/data-all.json', allow_redirects=True)
if r.status_code<200 or r.status_code>210:
    print('Error downloading state-wise data from covid19india.org data')
else:
    open('dataINST_pydw.json', 'wb').write(r.content)
print('downloading data 2.5/3')


# In[14]:


print('Parsing Source 1')

with open('owid-covid-data_pydw.csv','r', encoding='utf-8') as f:
    globalListRAW=list(csv.reader(f))
    f.close()
#print(globalListRAW[0])

class area:
    def __init__(obj, iso, name):
        obj.iso = iso
        obj.name = name
        obj.records=[]
        
dataOWID=dict()
skipped=0
parsed=0
for row in globalListRAW[1:]:
    if '' in [row[i] for i in [0,3,4,5,6,7]]:
        skipped+=1
        #print('skipped for iso:'+row[0])
        continue
    if row[0] not in dataOWID.keys():
        dataOWID[row[0]]=area(row[0],row[2])
    dataDict={globalListRAW[0][i]: float(row[i])     for i in [4,5,6,7]}
    dataDict['date'] = row[3]
    dataOWID[row[0]].records.append(dataDict)
    parsed+=1
print('\nSkipped:'+str(skipped)) #empty
print('parsed:'+str(parsed))
#print('Fields:', [h for h in dataOWID['IND'].records[0]])
print('Num Countries:', len([a for a in dataOWID]))
#print('\nCountries:', [a for a in dataOWID])
#for c in dataOWID:
#    print(c+" : "+dataOWID[c].name)


# In[16]:


#Getting John Hopkins Data from file (downloaded via: 'curl https://api.covid19api.com/all -o "allJH.json"',
                                    # 'curl https://api.covid19api.com/total/country/united-states -o usaJH.json')
print('Parsing Source 2')


with open('allJH_pydw.json','r', encoding='utf-8') as f:
    dataJH_RAW=json.load(f)
    f.close()
#us and aus data is divided
#with open('usaJH.json','r', encoding='utf-8') as f: 
#    dataJH_RAW+=json.load(f)
#    f.close()
with open('ausJH_pydw.json','r', encoding='utf-8') as f:
    dataJH_RAW+=json.load(f)
    f.close()

print('converting country codes to iso3 using source 1 data')
country2iso=dict() #John H data uses non standard codes. can be taken from OWID data. rough one time work
for c in dataOWID:
    country2iso[dataOWID[c].name]=dataOWID[c].iso
notFound=set()
forceFound=set()
found=set()
for row in dataJH_RAW:
    if row['Country'] not in country2iso:
        for c in dataOWID:
            if row['Country'][0:4] == dataOWID[c].name[0:4]:
                country2iso[row['Country']]=dataOWID[c].iso
                forceFound.add(row['Country'])
                #print('adding forced match: '+row['Country']+" : "+dataOWID[c].iso+" : "+dataOWID[c].name)
                #break  #don't, bootleg code
        if row['Country'] not in forceFound:
            notFound.add(row['Country'])       
    else:
        found.add(row['Country'])   
country2iso['United States of America']='USA' #fixing wrong match.
country2iso['Congo (Kinshasa)']='COD' #fixing wrong match.
country2iso['Korea (South)']='KOR'
country2iso["Côte d'Ivoire"]='CIV'
country2iso['Lao PDR']='LAO'
country2iso['Republic of Kosovo']='OWID_KOS' #exception in OWID data
country2iso['Holy See (Vatican City State)']='VAT'

dataJH=dict()
for row in dataJH_RAW:
    if not (row['City']=='' and row['Province']==''):
        continue
    if country2iso[row['Country']] not in dataJH.keys():
        dataJH[country2iso[row['Country']]]=area(country2iso[row['Country']],row['Country'])
    day=len(dataJH[country2iso[row['Country']]].records)
    dataDict={'date' : row['Date'].split('T')[0],
              'total_cases': float(row['Confirmed']),
              'total_deaths': float(row['Deaths']),
              'total_recovered': float(row['Recovered']),
              'total_active': float(row['Active']),
              
              'new_cases' : (float(row['Confirmed']) - (0 if day<1 else dataJH[country2iso[row['Country']]].records[day-1]['total_cases'])),
              'new_deaths': (float(row['Deaths']) - (0 if day<1 else dataJH[country2iso[row['Country']]].records[day-1]['total_deaths'])),
              'new_recovered': (float(row['Recovered']) - (0 if day<1 else dataJH[country2iso[row['Country']]].records[day-1]['total_recovered'])),
              
              #'past_x_days_new_cases' : (float(row['Confirmed']) - (0 if day<WINSIZE else dataJH[country2iso[row['Country']]].records[day-WINSIZE]['new_cases'])),
              #'past_x_days_new_deaths': (float(row['Deaths']) - (0 if day<WINSIZE else dataJH[country2iso[row['Country']]].records[day-WINSIZE]['new_deaths'])),
              #'past_x_days_new_recovered': (float(row['Recovered']) - (0 if day<WINSIZE else dataJH[country2iso[row['Country']]].records[day-WINSIZE]['new_recovered']))
             }
    dataJH[country2iso[row['Country']]].records.append(dataDict)
print('Missing Countries in Source 2 (that were there in Source 1)')
for c in dataOWID:
    if c not in dataJH:
        print(c, dataOWID[c].name)
print("---")
print('Missing Countries in Source 1 (that are there in Source 2)')
for c in dataJH:
    if c not in dataOWID:
        print(c, dataJH[c].name)
print("---")  


# In[18]:


#Getting Indian Data from covid19india.org from file (downloaded via: 'curl https://api.covid19india.org/data.json -o "data.json"')

print('Parsing Source 3')
with open('dataIN_pydw.json','r', encoding='utf-8') as f:
    dataIN_RAW=json.load(f)
    dataIN_RAW=dataIN_RAW['cases_time_series']
    f.close()

dataIN=[]
for row in dataIN_RAW:
    day=len(dataIN)
    dataDict={'date' : row['date'],
              'total_cases': float(row['totalconfirmed']),
              'total_deaths': float(row['totaldeceased']),
              'total_recovered': float(row['totalrecovered']),
              'total_active': float(row['totalconfirmed'])-(float(row['totaldeceased'])+float(row['totalrecovered'])),
              
              'new_cases' : float(row['dailyconfirmed']),
              'new_deaths': float(row['dailydeceased']),
              'new_recovered': float(row['dailyrecovered']),
              
              #'past_x_days_new_cases' : (float(row['Confirmed']) - (0 if day<WINSIZE else dataJH[country2iso[row['Country']]].records[day-WINSIZE]['new_cases'])),
              #'past_x_days_new_deaths': (float(row['Deaths']) - (0 if day<WINSIZE else dataJH[country2iso[row['Country']]].records[day-WINSIZE]['new_deaths'])),
              #'past_x_days_new_recovered': (float(row['Recovered']) - (0 if day<WINSIZE else dataJH[country2iso[row['Country']]].records[day-WINSIZE]['new_recovered']))
             }
    dataIN.append(dataDict)

print('done!'+str(len(dataIN)))


# In[22]:


print('Calculating some constants.\n(offsets since different sources start at different dates and'+
      '\nwe are conviniently not looking at dates and relying on the data being in sorted order)\n')
def daysBeforeFeb(data):
    days=0
    for r in data['IND'].records:
        if r['date'].split('-')[1]=='02':
            break
        else:
            days+=1
    return days
def daysBefore50(data):
    days=dict()
    for c in data:
        days[c]=0  #assuming every one we'll look has crossd 50
        for r in data[c].records:
            if r['total_cases']>=50:
                break
            else:
                days[c]+=1
    return days
    
extraDaysJH=daysBeforeFeb(dataJH)
extraDaysOWID=daysBeforeFeb(dataOWID)
extraDaysIN=2        

print("JH data", dataJH['IND'].records[extraDaysJH:][0]['date']," to ",dataJH['IND'].records[-1]['date'])
print("OWID data", dataOWID['IND'].records[extraDaysOWID:][0]['date']," to ",dataOWID['IND'].records[-1]['date'])
print("IN data", dataIN[extraDaysIN:][0]['date']," to ",dataIN[-1]['date'])

print('\nCalculating some more constants.\n (offsets for each country since for the first few cases the r factor corelated'+
      'measures will be too high, so in some cases we ignore the data till first 50 cases)')

daysTill50JH=daysBefore50(dataJH)
daysTill50OWID=daysBefore50(dataOWID)
daysTill50IN=40


# In[25]:


print('preprocessing')
#very bootleg code here (and everywhere else in the notebook) lads, note to self: don't show to any recruiter.

INCUBATIONPERIOD=7
WINSIZE=7
new=dict()
act=dict()
new_by_active=dict()
for c in dataJH:
    new_by_active[c]=[]
    new[c]=[]
    act[c]=[]
    active=0
    for r in range(extraDaysJH, extraDaysJH + WINSIZE):
        active+= dataJH[c].records[r]['total_active']
    active/=WINSIZE
    for r in range(extraDaysJH+WINSIZE-1,len(dataJH[c].records)-INCUBATIONPERIOD):
        new_cases=dataJH[c].records[r+INCUBATIONPERIOD]['total_cases'] - dataJH[c].records[r + INCUBATIONPERIOD - WINSIZE]['total_cases']
        #new_cases=( dataJH[c].records[r+INCUBATIONPERIOD - int(WINSIZE/2) ]['new_cases'] +
        #            dataJH[c].records[r+INCUBATIONPERIOD - int(WINSIZE/2) -1]['new_cases'] +
        #            dataJH[c].records[r+INCUBATIONPERIOD - int(WINSIZE/2) +1]['new_cases'])
        new[c].append(new_cases)
        act[c].append(active)
        new_by_active[c].append(float(new_cases)/float(active) if active>0 else 0)
        
        active-=(dataJH[c].records[r+1 - WINSIZE]['total_active']/WINSIZE)
        active+=(dataJH[c].records[r+1]['total_active']/WINSIZE)

new_by_activeO=dict()
newO=dict()
for c in dataOWID:
    newO[c]=[]
    for r in range(extraDaysOWID+WINSIZE-1,len(dataOWID[c].records)-INCUBATIONPERIOD):
        #new_cases=( dataJH[c].records[r+INCUBATIONPERIOD - int(WINSIZE/2) ]['new_cases'] +
        #            dataJH[c].records[r+INCUBATIONPERIOD - int(WINSIZE/2) -1]['new_cases'] +
        #            dataJH[c].records[r+INCUBATIONPERIOD - int(WINSIZE/2) +1]['new_cases'])
        new_casesOWID=dataOWID[c].records[r+INCUBATIONPERIOD]['total_cases'] - dataOWID[c].records[r + INCUBATIONPERIOD - WINSIZE]['total_cases']
        newO[c].append(new_casesOWID) 
    if c not in dataJH:
        continue
    new_by_activeO[c]=[]
    for r in range(0,min([len(newO[c]),len(act[c])])):
        new_by_activeO[c].append(newO[c][r]/act[c][r] if act[c][r]!=0 else 0)
        
new_by_activeI=[]
newI=[]
actI=[]
active=0
for r in range(extraDaysIN, extraDaysIN + WINSIZE):
    active+= dataIN[r]['total_active']
active/=WINSIZE
for r in range(extraDaysIN+WINSIZE-1,len(dataIN)-INCUBATIONPERIOD):
    new_cases=dataIN[r+INCUBATIONPERIOD]['total_cases'] - dataIN[r + INCUBATIONPERIOD - WINSIZE]['total_cases']
    #new_cases=( dataJH[c].records[r+INCUBATIONPERIOD - int(WINSIZE/2) ]['new_cases'] +
    #            dataJH[c].records[r+INCUBATIONPERIOD - int(WINSIZE/2) -1]['new_cases'] +
    #            dataJH[c].records[r+INCUBATIONPERIOD - int(WINSIZE/2) +1]['new_cases'])
    newI.append(new_cases)
    actI.append(dataIN[r-3]['total_active'])
    new_by_activeI.append(float(new_cases)/float(active) if active>0 else 0)
    
    active-=(dataIN[r+1 - WINSIZE]['total_active']/WINSIZE)
    active+=(dataIN[r+1]['total_active']/WINSIZE)


# In[148]:


if WINSIZE!=7 or INCUBATIONPERIOD!=7:
    title=('"Avg. Active Cases in past '+str(WINSIZE)+'days & Total New Cases in the the *following* '+str(WINSIZE)+
           'days after\na gap of '+str(INCUBATIONPERIOD)+"-"+str(WINSIZE)+"="+str(INCUBATIONPERIOD-WINSIZE)+
           'days to adjust for the incubation (and delay) period of '+str(INCUBATIONPERIOD)+
           'days)"\nvs. "days passed since 1/Feb/2020"')
else:
    title=('"Avg. Active Cases in the past week" & "Total New Cases in the following week"\nvs. "days passed since 1/Feb/2020"'+
          '\n(new cases total is phase shifted back by 7 days to roughly account for the incubation period and delay in testing)')
    
print(title)
f, axes = plt.subplots(4, 2, figsize=(30, 30), sharex=True)
f.suptitle(title,
           fontsize=30, 
           fontweight=500,
           variant='small-caps'
           )
countries=[['BRA', 'RUS'], ['USA', 'IND'], ['DEU', 'AUS'], ['ITA', 'ESP']]
for i in range(0,4):
    for j in [0,1]:
        #print(countries[i][j])
        ax=axes[i,j]
        ax.set_title(countries[i][j])
        ax.set_ylabel("#")
        ax.set_xlabel("Days since 1/Feb/2020")
        #ax.set_yscale("log")
        #plt.grid(b=True,which='both',axis='both')
        ax.plot(
            #range(extraDaysJH+WINSIZE-1+INCUBATIONPERIOD,len(dataJH[c].records)),
            range(WINSIZE-1,len(dataJH[countries[i][j]].records)-INCUBATIONPERIOD-extraDaysJH),
            new[countries[i][j]],
            label=("New cases in the following period of "+str(WINSIZE)+"days after "+str(INCUBATIONPERIOD)+"-"+str(WINSIZE)+"="
                   +str(INCUBATIONPERIOD-WINSIZE)+" days (Source 1)"),
            color='yellow'
        )
        ax.plot(
            #range(extraDaysJH+WINSIZE-1+INCUBATIONPERIOD,len(dataJH[c].records)),
            range(WINSIZE-1,len(dataOWID[countries[i][j]].records)-INCUBATIONPERIOD-extraDaysOWID),
            newO[countries[i][j]],
            label=("New cases in the following period of "+str(WINSIZE)+"days after "+str(INCUBATIONPERIOD)+"-"+str(WINSIZE)+"="
                   +str(INCUBATIONPERIOD-WINSIZE)+" days (Source 2)"),
            color='red'
        )
        ax.plot(
            range(WINSIZE-1,len(dataJH[countries[i][j]].records)-INCUBATIONPERIOD-extraDaysJH),
            act[countries[i][j]],
            color='blue',
            label="Avg. Active Cases in preceding "+str(WINSIZE)+"days (Source 1)"
        )
        ax.legend()

axes[1][1].fill_between([53,73],[0,0],[max(act['IND']),max(act['IND'])],
                facecolor='yellow',
                alpha=0.25,
                label='Phase 1'
                )
axes[1][1].fill_between([74,92],[0,0],[max(act['IND']),max(act['IND'])],
                facecolor='orange',
                alpha=0.25,
                label='Phase 2'
                )
axes[1][1].fill_between([93,106],[0,0],[max(act['IND']),max(act['IND'])],
                facecolor='red',
                alpha=0.25,
                label='Phase 3'
                )
axes[1][1].fill_between([107,120],[0,0],[max(act['IND']),max(act['IND'])],
                facecolor='purple',
                alpha=0.25,
                label='Phase 4'
                )
axes[1][1].fill_between([121,150],[0,0],[max(act['IND']),max(act['IND'])],
                facecolor='pink',
                alpha=0.25,
                label='Phase 5'
                )
axes[1][1].plot(
    #range(extraDaysJH+WINSIZE-1+INCUBATIONPERIOD,len(dataJH[c].records)),
    range(WINSIZE-1,len(dataIN)-INCUBATIONPERIOD-extraDaysIN),
    newI,
    label="New cases in the following period of "+str(WINSIZE)+"days after "+str(INCUBATIONPERIOD)+"-"+str(WINSIZE)+"="+str(INCUBATIONPERIOD-WINSIZE)+" days (Source 3)",
    color='orange'
)
axes[1][1].plot(
    range(WINSIZE-1,len(dataIN)-INCUBATIONPERIOD-extraDaysIN),
    actI,
    color='green',
    label="Avg. Active Cases in preceding "+str(WINSIZE)+"days (Source 3)"
)
axes[1][1].legend()

f.savefig("Plot_1.png")

# In[149]:


if WINSIZE!=7 or INCUBATIONPERIOD!=7:
    title=('"Total New Cases in the the *following* '+str(WINSIZE)+
           'days after a gap of '+str(INCUBATIONPERIOD)+"-"+str(WINSIZE)+"="+str(INCUBATIONPERIOD-WINSIZE)+
           'days\n(to adjust for the incubation (and delay) period of '+str(INCUBATIONPERIOD)+
           'days)\n divided by Avg. Active Cases in past '+str(WINSIZE)+'days"\nvs. "days passed since 1/Feb/2020"')
else:
    title=('"Avg. New Cases in the *following* week\ndivided by Avg. Active Cases in the *past* week"\nvs. "days passed since 1/Feb/2020"'+
          '\n(new cases total is phase shifted back by 7 days to roughly account for the incubation period and delay in testing)')
print("plotting:\n"+title)
f, axes = plt.subplots(4, 2, figsize=(30, 30), sharex=True)
f.suptitle(title,
           fontsize=30, 
           fontweight=500#,
           #variant='small-caps'
          )
countries=[['BRA', 'RUS'], ['USA', 'IND'], ['DEU', 'AUS'], ['ITA', 'ESP']]
for i in range(0,4):
    for j in [0,1]:
        #print(countries[i][j])
        ax=axes[i,j]
        ax.set_title(countries[i][j])
        ax.set_xlabel("Days since 1/Feb/2020")
        ax.set_ylim(0,0.5)
        ax.set_xlim(0,len(dataJH['IND'].records)-extraDaysJH+10)
        #plt.grid(b=True,which='both',axis='both')
        ax.plot(
            #range(extraDaysJH+WINSIZE-1+INCUBATIONPERIOD,len(dataJH[c].records)),
            range(max(WINSIZE-1, daysTill50JH[countries[i][j]]),WINSIZE-1+len(new_by_active[countries[i][j]])),
            [p/WINSIZE for p in new_by_active[countries[i][j]][max(WINSIZE-1, daysTill50JH[countries[i][j]])-WINSIZE+1:]],
            label=("Avg. New cases in the following period of "+str(WINSIZE)+
                   "days after "+str(INCUBATIONPERIOD)+"-"+str(WINSIZE)+"="+str(INCUBATIONPERIOD-WINSIZE)+" days (Source 1)"+
                   "\ndevided by the average Active number of cases in the past week (Source 1)"),
                   color='yellow'
                  )
        ax.plot(
            #range(extraDaysJH+WINSIZE-1+INCUBATIONPERIOD,len(dataJH[c].records)),
            #range(max(WINSIZE-1, daysTill50OWID[countries[i][j]]),WINSIZE-1+len(new_by_active[countries[i][j]])),
            [p+max(WINSIZE-1, daysTill50OWID[countries[i][j]]) for p in range(0,len(new_by_activeO[countries[i][j]][max(WINSIZE-1, daysTill50OWID[countries[i][j]])-WINSIZE+1:]))],
            [p/WINSIZE for p in new_by_activeO[countries[i][j]][max(WINSIZE-1, daysTill50OWID[countries[i][j]])-WINSIZE+1:]],
            label=("Avg. New cases in the following period of "+str(WINSIZE)+
                   "days after "+str(INCUBATIONPERIOD)+"-"+str(WINSIZE)+"="+str(INCUBATIONPERIOD-WINSIZE)+" days (Source 2)"+
                   "\ndevided by the average Active number of cases in the past week (Source 1)"),
            color='red'
        )
        ax.legend()
axes[1][1].plot(
    #range(extraDaysJH+WINSIZE-1+INCUBATIONPERIOD,len(dataJH[c].records)),
    range(40,len(new_by_activeI[40-6+2:])+40),
    [p/WINSIZE for p in new_by_activeI[40-6+2:]],
    label=("Avg. New cases in the following period of "+str(WINSIZE)+
            "days after "+str(INCUBATIONPERIOD)+"-"+str(WINSIZE)+"="+str(INCUBATIONPERIOD-WINSIZE)+" days (Source 3)"+
            "\ndevided by the average Active number of cases in the past week (Source 3)"),
    color='black'
)

axes[1][1].legend()

axes[1][1].fill_between([53,73],[0,0],[max(act['IND']),max(act['IND'])],
                facecolor='yellow',
                alpha=0.4,
                label='Phase 1'
                )
axes[1][1].fill_between([74,92],[0,0],[max(act['IND']),max(act['IND'])],
                facecolor='orange',
                alpha=0.4,
                label='Phase 2'
                )
axes[1][1].fill_between([93,106],[0,0],[max(act['IND']),max(act['IND'])],
                facecolor='red',
                alpha=0.4,
                label='Phase 3'
                )
axes[1][1].fill_between([107,120],[0,0],[max(act['IND']),max(act['IND'])],
                facecolor='purple',
                alpha=0.4,
                label='Phase 4'
                )
axes[1][1].fill_between([121,150],[0,0],[max(act['IND']),max(act['IND'])],
                facecolor='pink',
                alpha=0.4,
                label='Phase 5'
                )


# In[150]:


if WINSIZE!=7 or INCUBATIONPERIOD!=7:
    title=('Δ(N/A)/ΔT vs. T\n'+
           'N="Avg. New Cases in the the *following* '+str(WINSIZE)+'days\n  after a gap of '+
           str(INCUBATIONPERIOD)+"-"+str(WINSIZE)+"="+str(INCUBATIONPERIOD-WINSIZE)+
           'days\n  (to adjust for the incubation (and delay) period of '+str(INCUBATIONPERIOD)+
           'days)\nA=Avg. Active Cases in past '+str(WINSIZE)+'days'+
           '\nT=days passed since 1/Feb/2020')
else:
    title=('Δ(N/A)/ΔT vs. T\n'+
           '\nN=Avg. New Cases in the the *following* week'+
           '\nA=Avg. Active Cases in *past* week'+
           '\nT=days passed since 1/Feb/2020')
print("plotting:\n"+title)
f, axes = plt.subplots(4, 2, figsize=(30, 30), sharex=False)
f.suptitle(title,
           fontsize=30, 
           fontweight=500#,
           #variant='small-caps'
          )
countries=[['BRA', 'RUS'], ['USA', 'IND'], ['DEU', 'AUS'], ['ITA', 'ESP']]
for i in range(0,4):
    for j in [0,1]:
        print(countries[i][j])
        y=[p/WINSIZE for p in new_by_active[countries[i][j]][max(WINSIZE-1, daysTill50JH[countries[i][j]])-WINSIZE+1:]]
        yJ=[0]+[y[i]-y[i-1] for i in range(1,len(y))]
        y=[p/WINSIZE for p in new_by_activeO[countries[i][j]][max(WINSIZE-1, daysTill50OWID[countries[i][j]])-WINSIZE+1:]]
        yO=[0]+[y[i]-y[i-1] for i in range(1,len(y))]
        ax=axes[i,j]
        ax.set_title(countries[i][j])
        ax.set_xlabel("Days since 1/Feb/2020")
        ax.set_ylim(-0.15,0.05)
        #ax.set_yscale("symlog")
        ax.set_xlim(0,len(dataJH['IND'].records)-extraDaysJH+10)
        #plt.grid(b=True,which='both',axis='both')
        ax.plot(
            #range(extraDaysJH+WINSIZE-1+INCUBATIONPERIOD,len(dataJH[c].records)),
            range(max(WINSIZE-1, daysTill50JH[countries[i][j]]),WINSIZE-1+len(new_by_active[countries[i][j]])),
            yJ,
            label=('Δ(N (source 1) / A (source 1))/ΔT vs. T'),
                   color='yellow'
                  )
        ax.fill_between(range(max(WINSIZE-1, daysTill50JH[countries[i][j]]),WINSIZE-1+len(new_by_active[countries[i][j]])),
                        yJ,
                        [0 for f in yJ],
                        where=[f<0 for f in yJ],
                        facecolor='green',
                        alpha=0.4,
                        interpolate=True
                        )
        ax.fill_between(range(max(WINSIZE-1, daysTill50JH[countries[i][j]]),WINSIZE-1+len(new_by_active[countries[i][j]])),
                        yJ,
                        [0 for f in yJ],
                        where=[f>0 for f in yJ],
                        facecolor='red',
                        alpha=0.4,
                        interpolate=True
                        )
        #ax.plot(
            #range(extraDaysJH+WINSIZE-1+INCUBATIONPERIOD,len(dataJH[c].records)),
            #range(max(WINSIZE-1, daysTill50OWID[countries[i][j]]),WINSIZE-1+len(new_by_active[countries[i][j]])),
        #    [p+max(WINSIZE-1, daysTill50OWID[countries[i][j]]) for p in range(0,len(yO))],
        #    yO,
        #    label=('Δ(N (source 2) / A (source 1))/ΔT vs. T'),
        #           color='red'
        #          )
        #ax.fill_between(range(max(WINSIZE-1, daysTill50JH[countries[i][j]]),WINSIZE-1+len(new_by_active[countries[i][j]])),
        #                yJ,
        #                [0 for f in yJ],
        #        facecolor='red',
        #        alpha=0.4
        #        )
        ax.plot(
            #range(extraDaysJH+WINSIZE-1+INCUBATIONPERIOD,len(dataJH[c].records)),
            #range(max(WINSIZE-1, daysTill50OWID[countries[i][j]]),WINSIZE-1+len(new_by_active[countries[i][j]])),
            [0,len(dataJH['IND'].records)-extraDaysJH+10],
            [0,0],
            label=('0'),
            color='grey'
            )
        ax.legend()
y=[p/WINSIZE for p in new_by_activeI[40-6+2:]]
yI=[0]+[y[i]-y[i-1] for i in range(1,len(y))]
axes[1][1].plot(
    #range(extraDaysJH+WINSIZE-1+INCUBATIONPERIOD,len(dataJH[c].records)),
    range(40,len(new_by_activeI[40-6+2:])+40),
    yI,
    label=('Δ(N (source 3) / A (source 3))/ΔT vs. T'),
    color='black')
axes[1][1].fill_between(range(40,len(new_by_activeI[40-6+2:])+40),
                        yI,
                        [0 for f in yI],
                        where=[f<=0 for f in yI],
                        facecolor='green',
                        alpha=0.4,
                        interpolate=True
                        )
axes[1][1].fill_between(range(40,len(new_by_activeI[40-6+2:])+40),
                        yI,
                        [0 for f in yI],
                        where=[f>0 for f in yI],
                        facecolor='red',
                        alpha=0.4,
                        interpolate=True
                        )
axes[1][1].legend()

axes[1][1].fill_between([53,73],[min(yI),min(yI)],[max(yI),max(yI)],
                facecolor='yellow',
                alpha=0.2,
                label='Phase 1'
                )
axes[1][1].fill_between([74,92],[min(yI),min(yI)],[max(yI),max(yI)],
                facecolor='orange',
                alpha=0.2,
                label='Phase 2'
                )
axes[1][1].fill_between([93,106],[min(yI),min(yI)],[max(yI),max(yI)],
                facecolor='red',
                alpha=0.2,
                label='Phase 3'
                )
axes[1][1].fill_between([107,120],[min(yI),min(yI)],[max(yI),max(yI)],
                facecolor='purple',
                alpha=0.2,
                label='Phase 4'
                )
axes[1][1].fill_between([121,150],[min(yI),min(yI)],[max(yI),max(yI)],
                facecolor='pink',
                alpha=0.2,
                label='Phase 5'
                )


# In[147]:


#what to do next? (ΔN/N)/(ΔA/A) ? 

if WINSIZE==7 or INCUBATIONPERIOD!=7:
    title=('Total New Cases in the the *following* '+str(WINSIZE)+
           'days\n(after a gap of '+str(INCUBATIONPERIOD)+"-"+str(WINSIZE)+"="+str(INCUBATIONPERIOD-WINSIZE)+
           'days to adjust for the incubation (and delay) period of '+str(INCUBATIONPERIOD)+
           'days)"\nvs. "Avg. Active Cases in past '+str(WINSIZE)+'days')
else:
    title=('"Avg. Active Cases in the past week" & "Total New Cases in the following week"\nvs. "days passed since 1/Feb/2020"'+
          '\n(new cases total is phase shifted back by 7 days to roughly account for the incubation period and delay in testing)')
    
print(title)
f, axes = plt.subplots(4, 2, figsize=(30, 30), sharex=False)
f.suptitle(title,
           fontsize=30, 
           fontweight=500,
           variant='small-caps'
           )
countries=[['BRA', 'RUS'], ['USA', 'IND'], ['DEU', 'AUS'], ['ITA', 'ESP']]
for i in range(0,4):
    for j in [0,1]:
        #print(countries[i][j])
        ax=axes[i,j]
        ax.set_title(countries[i][j])
        ax.set_yscale("log")
        ax.set_xscale("log")
        x1,x2=ax.get_xlim()
        y1,y2=ax.get_xlim()
        print(x1,x2,y1,y2)
        ax.set_xlim(1,10000000)
        ax.set_ylim(1,10000000)
        ax.set_ylabel("New cases in the following period of "+str(WINSIZE)+"days after "+str(INCUBATIONPERIOD)+"-"+str(WINSIZE)+"="
                   +str(INCUBATIONPERIOD-WINSIZE)+" days")
        ax.set_xlabel("Avg. Active Cases in preceding "+str(WINSIZE)+"days (Source 1)")
        #ax.set_yscale("log")
        #plt.grid(b=True,which='both',axis='both')
        ax.plot(
            #range(extraDaysJH+WINSIZE-1+INCUBATIONPERIOD,len(dataJH[c].records)),
            act[countries[i][j]],
            new[countries[i][j]],
            label=("New cases in the following period of "+str(WINSIZE)+"days after "+str(INCUBATIONPERIOD)+"-"+str(WINSIZE)+"="
                   +str(INCUBATIONPERIOD-WINSIZE)+" days (Source 1)"),
            color='yellow'
        )
        minl=min(len(act[countries[i][j]]),len(newO[countries[i][j]]))
        ax.plot(
            #range(extraDaysJH+WINSIZE-1+INCUBATIONPERIOD,len(dataJH[c].records)),
            act[countries[i][j]][7:minl],
            newO[countries[i][j]][7:minl],   
            label=("New cases in the following period of "+str(WINSIZE)+"days after "+str(INCUBATIONPERIOD)+"-"+str(WINSIZE)+"="
                   +str(INCUBATIONPERIOD-WINSIZE)+" days (Source 2)"),
            color='red'
        )
        ax.legend()


axes[1][1].plot(
    #range(extraDaysJH+WINSIZE-1+INCUBATIONPERIOD,len(dataJH[c].records)),
    actI[2:],
    newI[2:],
    label="New cases in the following period of "+str(WINSIZE)+"days after "+str(INCUBATIONPERIOD)+"-"+str(WINSIZE)+"="+str(INCUBATIONPERIOD-WINSIZE)+" days (Source 3)",
    color='orange'
)
axes[1][1].legend()


# In[151]:





# In[ ]:




