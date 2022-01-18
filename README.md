# Elan-2-Refi
This project attempts to convert ELAN EAF files to the REFI-QDA QDPX format.  
  
## Usage
The refi.py file is the command-line script.  
You must provide the file path of the EAF file OR the folder it is contained in.  
  
USAGE:  
python refi.py -f {eaf file path} -o {qdpx archive name}  
  
ARGUMENTS:  
-f  path to EAF project file / folder  
-o  name of QDPX archive that will be created  
  
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