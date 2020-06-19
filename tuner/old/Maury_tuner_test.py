import visa
import time
rm = visa.ResourceManager()                                                         # setup GPIB communications

######################################################################################################################################################
# WARNING! BC,DR1 must be executed as a setup OR this polling WILL NOT WORK
def poll(tuner):
    time.sleep(0.5)
    while True:
        try: sb=tuner.read_stb()
        except:
            print ("error in sb read retry")
            continue
        #print ("before break in loop",sb)
        if int(sb&32)==32: break
        print ("after break"), sb
        #time.sleep(settlingtime)
        time.sleep(0.4)
    time.sleep(2)                                      # minimum time here to prevent read errors is 2sec
    #print("waiting for service request")




tuner = rm.open_resource('GPIB0::11::INSTR')
#tuner_data.read_termination='\r'
tuner.write_termination='\r'
#PNA = rm.open_resource('GPIB0::3::INSTR')
#
# tuner_data.write("*IDN?")
#
# rt=tuner_data.read_raw()
#print(rt)
# tuner_data.write("V 0")
# time.sleep(1)
# rt=tuner_data.read_raw()

#tuner_data.write("M1")
# #tuner_data.write_raw("I\r")
# tuner_data.write("A 100")
# #tuner_data.write("P 0")
# #tuner_data.write("V 0")
# rt=tuner_data.read_raw()
#print(rt)
#rt=tuner_data.query("V0")
#tuner_data.write_raw("200")
tuner.write("M0")
tuner.write("I")
tuner.write("F 5")
tuner.write("S 225")
tuner.write("R 80")
tuner.write("Z 1")
tuner.write("P 7000")
poll(tuner)
tuner.write("M0")
tuner.write("I")
# tuner_data.write("V 0")
# rt=tuner_data.read()
rt=tuner.query("V 0")
print(rt)
sb=tuner.read_stb()
print(sb)
# PNA.write("*IDN?")
# print(PNA.read())

