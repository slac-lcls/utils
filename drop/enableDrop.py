import pickle
from epics import caget, caput, cainfo
import time
import datetime
import os
import sys
from pprint import pprint

major, minor, micro = (1, 0, 0)
date = time.strftime('%Y_%m')
logfilename = 'log/'+date
try:
    logfile = open(logfilename,'a')
except:
    sys.exit(f'failed to open "{logfilename}"')

sys.stderr = logfile
sys.stdout = logfile
print('---------------')

savefile = 'stopperstate.pkl'
minvalue = 10000

# soft xray PVs
soft_abtprd = 'IOC:IN20:EV01:BYKIKS_ABTPRD'
soft_abtact = 'IOC:IN20:EV01:BYKIKS_ABTACT'
 
# hard xray PVs
hard_abtprd = 'IOC:IN20:EV01:BYKIK_ABTPRD'
hard_abtact = 'IOC:IN20:EV01:BYKIK_ABTACT'

new_state = {
    'version': (major, minor, micro),
    'hutches': {
        'CXI' : {
            'stopper_pv' : 'STPR:XRT1:1:S5OUT_MPSC',
            'soft_xray' : False,
            'stopper_opens_on' : 1
        },
        'XCS' : {
            'stopper_pv' : 'PPS:FEH1:4:S4STPRSUM',
            'soft_xray' : False,
            'stopper_opens_on' : 0
        },
        'MEC' : {
            'stopper_pv' : 'PPS:FEH1:6:S6STPRSUM',
            'soft_xray' : False,
            'stopper_opens_on' : 0
        },
        'MFX' : {
            'stopper_pv' : 'STPR:XRT:1:S45IN_MPSC',
            'soft_xray' : False,
            'stopper_opens_on' : 1
        },
        'XPP' : {
            'stopper_pv' : 'PPS:NEH1:1:S3INSUM',
            'soft_xray' : False,
            'stopper_opens_on' : 0
        },
        'TMO' : {
            'stopper_pv' : 'PPS:NEH1:1:ST3K4OUTSUM',
            'soft_xray' : True,
            'stopper_opens_on' : 1
        },
        'RIX' : {
            'stopper_pv' : 'STPR:NEH1:2200:ST1K2OUT',
            'soft_xray' : True,
            'stopper_opens_on' : 1
        }
    }
}

# get the new stopper state by reading from EPICS
for value in new_state['hutches'].values():
    value['stopper_readout'] = caget(value['stopper_pv'])

# XXX pretend to open stoppers
#new_state['hutches']['RIX']['stopper_readout'] = new_state['hutches']['RIX']['stopper_opens_on']
#new_state['hutches']['XPP']['stopper_readout'] = new_state['hutches']['XPP']['stopper_opens_on']

print(f"Checked stoppers at: {datetime.datetime.now()}")

print('--- new stopper state ---')
pprint(new_state)

# get the old stopper state by reading from save file
if os.path.isfile(savefile):
    savedstateprimer = open(savefile, 'rb')
    old_state = pickle.load(savedstateprimer)
    print(f'Save file "{savefile}" read')
    savedstateprimer.close()
    print('--- old stopper state ---')
    pprint(old_state)

    if 'version' in old_state and old_state['version'][0] == major:
        # for each hutch, check if stopper newly opened
        for hutch in new_state['hutches'].keys():
            if (old_state['hutches'][hutch]['stopper_readout'] != old_state['hutches'][hutch]['stopper_opens_on']) and \
               (new_state['hutches'][hutch]['stopper_readout'] == new_state['hutches'][hutch]['stopper_opens_on']):
                print(f'hutch {hutch} opened')

                if new_state['hutches'][hutch]['soft_xray']:
                    if (caget(soft_abtact) == 0) or (caget(soft_abtprd) > minvalue):
                        caput(soft_abtprd, minvalue)
                        caput(soft_abtact, 1)
                        print(f"Soft xray drop shot period set to {minvalue} at {datetime.datetime.now()}")
                else:
                    if (caget(hard_abtact) == 0) or (caget(hard_abtprd) > minvalue):
                        caput(hard_abtprd, minvalue)
                        caput(hard_abtact, 1)
                        print(f"Hard xray drop shot period set to {minvalue} at {datetime.datetime.now()}")
    else:
        print(f'Save file "{savefile}" not compatible with version {major}.{minor}.{micro}')

else:
    print(f'Save file "{savefile}" not found')

# write the new stopper state to save file
newsavedstate = open(savefile, 'wb')
savedlist = pickle.dump(new_state, newsavedstate)
print(f'Save file "{savefile}" written')
newsavedstate.close()

#caget -d DBR_CTRL_ENUM (Stopper name) gets ya the descriptions of the states
#S5OUT_MPSC: 0=closed, 1=open
#S4STPRSUM: 0=open 4=closed
#S6STPRSUM: 0=open 4=closed
#S45IN_NPSC: 0: open, 1=closed
#S3INSUM: 0=open, 1=closed
#ST3K4OUTSUM: 0=closed, 1=open
#ST1K2OUT: 0=closed, 1=open
