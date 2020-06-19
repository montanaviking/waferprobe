__author__ = 'viking'
# test of histograms
from wafer_analysis import *
from IVplot import *
path = "/home/viking/documents_2/MicrocraftX_LLC/customers/Carbonics/projects/documents/wafer_tests/H31ba"
wafername = "H31ba"

Vgs=-20

waf = WaferData(path,wafername,fractVdsfit_Ronfoc=0.1,Y_Ids_fitorder=8)     # get wafer data
Ron=waf.Ron_Gon_histogram(minRon=0,binsizeRondev=.05,maxRon=1E99,maxRonstddev=3,includes='TLM0.4 MO',fractVdsfit_Ronfoc=0.25,recalc='yes',RG='R')['R']
Vgsarray=waf.DCd[0].Ron_foc()['Vgs']
iVgs=min(range(len(Vgsarray)), key=lambda i: abs(Vgsarray[i]-Vgs))	# find the Vgs closest to the selected value
print ("Average is",waf.Ron_Gon_histogram()['average'][iVgs])
for ib in range(0,len(waf.Ron_Gon_histogram()['R'][iVgs])):
    for idev in range(0,len(waf.Ron_Gon_histogram()['R'][iVgs][ib])):
        print(waf.Ron_Gon_histogram()['D'][iVgs][ib][idev],waf.Ron_Gon_histogram()['R'][iVgs][ib][idev])

plothistRon(waf.Ron_Gon_histogram()['Vgs'],waf.Ron_Gon_histogram()['binmin'],waf.Ron_Gon_histogram()['binmax'],waf.Ron_Gon_histogram()['R'],Vgs=-20.)

