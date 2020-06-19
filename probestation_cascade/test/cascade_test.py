# control Cascade via GPIB
import visa
import time
from cascade import CascadeProbeStation
rm = visa.ResourceManager()

pr = CascadeProbeStation(rm)
print pr.subsiteindex()
print pr.dieindex()
print pr.dieXindex()
print pr.dieYindex()
print pr.numberofsubsites()
print pr.numberofdie()
pr.move_contact()
# step through all sites on wafer

for idie in range(1,pr.numberofdie()+1):
    for isub in range(0,pr.numberofsubsites()-1):
        print "probing subsite ", pr.subsiteindex(),"in die number ",pr.dieindex()," die X index = ",pr.dieXindex()," die Y index = ",pr.dieYindex(),"xpos = ",pr.x(),"ypos =",pr.y()
        time.sleep(1)
        pr.move_nextsub()
        print "probing subsite ", pr.subsiteindex(),"in die number ",pr.dieindex()," die X index = ",pr.dieXindex()," die Y index = ",pr.dieYindex(),"xpos = ",pr.x(),"ypos =",pr.y()
        time.sleep(1)
    pr.move_nextdie()
pr.move_firstdie()
print("done probing")