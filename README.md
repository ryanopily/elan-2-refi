# Elan-2-Refi
This project attempts to convert [ELAN](https://archive.mpi.nl/tla/elan) projects into [REFI-QDA](https://www.qdasoftware.org/wp-content/uploads/2019/09/REFI-QDA-1-5.pdf) compliant projects, so that data collected in ELAN can be used in other qualitative analysis software.  

## Usage
The refi.py file is the command-line script.  

**Arguments**  
-f  (EAF project file or directory path)  
-o  (output file path)  

**Example**  
python refi.py -f /PATH/project.eaf -o /PATH/output.qdpx  

## Dependencies
[pympi-ling](https://pypi.org/project/pympi-ling/)  

## Structure
refi.py  
This is the command-line script that invokes the conversion process.  

refi_common.py  
Defines utility functions used throughout the project  

elan_to_refi.py  
Converts EAF XML elements to the equivalent REFI-QDA QDPX XML elements.  

annotate.py  
Generates a linked transcript that syncs with a video file.  
