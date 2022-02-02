# Elan-2-Refi
This project attempts to convert ELAN EAF files to the REFI-QDA QDPX format,  
so that data collected using ELAN can be used in other qualitative analysis software.
  
## Usage
The refi.py file is the command-line script.  
  
USAGE:  
python refi.py -f {eaf file input path} -o {qdpx archive output path}  
  
ARGUMENTS:  
-f  path to EAF project file / folder that the project is contained in
-o  path of the QDPX archive that will be created  
  
EXAMPLE:  
python refi.py  -f C:\Users\ryanopily\ELAN-PROJECT\elan-project.eaf -o C:\Users\ryanopily\ELAN-PROJECT\elan-project.qdpx. 
  
## Dependencies
[pympi-ling](https://pypi.org/project/pympi-ling/)
  
## STRUCTURE
refi.py   
    This is the command-line script that invokes the entire conversion process.  
  
refi_common.py  
    Defines utility functions used throughout the project  
  
elan_to_refi.py  
    Converts EAF XML elements to the equivalent REFI-QDA QDPX XML elements.  
  
annotate.py  
    Creates a transcript from an EAF file that can be linked to a VideoSource in the QDPX archive.  
