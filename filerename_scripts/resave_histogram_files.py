__author__ = 'Ahmad'
import os
from shutil import copy
# updates files with names in (pathname2) by searching (pathname) and copying the resultant files to (3athname3)
#pathname="/home/ahmad/Desktop/Link to waferprobe_ver2" #path of directory to search for updated files
pathname="/carbonics/owncloudsync/programs/python/waferprobe"
#pathname2= "/home/ahmad/Desktop/X.Selected_Measurements/Carbonics_measurement_modeling_software/software_installs/pythonforwindows/histogram_program_May27_2016"#path of the template folder that has all the histogram files= names that must be updated
#pathname3="/home/ahmad/Desktop/X.Selected_Measurements/Carbonics_measurement_modeling_software/software_installs/pythonforwindows/histogram_program_June13_2016" #pathname of destination folder
pathname2="/carbonics/owncloudsync/X.Selected_Measurements/Carbonics_measurement_modeling_software/software_installs/pythonforwindows/histogram_program_June7_2017"
#pathname3="/carbonics/owncloudsync/X.Selected_Measurements/Carbonics_measurement_modeling_software/software_installs/pythonforwindows/histogram_program_Sept9_2016"
def getsubdir(path):
	return [os.path.join(path,name) for name in os.listdir(path)
		if os.path.isdir(os.path.join(path,name))]
def getfile(path):
	return [os.path.join(path,name) for name in os.listdir(path)
	if not os.path.isdir(os.path.join(path,name))]
def getfilename(path):
	return [name for name in os.listdir(path)
	if not os.path.isdir(os.path.join(path,name))]


g=getsubdir(pathname)
names=getfilename(pathname2)
filenames=[]
for folder in g: # two levels down the folders
	gg=getsubdir(os.path.join(pathname, folder))
	pathnew=os.path.join(pathname, folder)
	for fldr in gg:
		filenames.extend(getfile(os.path.join(pathnew, fldr)))
	filenames.extend(getfile(os.path.join(pathname, folder)))

print("filenames length: ", len(filenames))

for file in filenames:
	for nm in names:
		if os.path.basename(file)==nm:
			copy(file, pathname3)