#####Converts On-Board Survey file (OBS) to FT [passenger links](https://github.com/lmz/dyno-path/blob/patch-1/files/links.md) output.

---
#### Notes:
This conversion was done for the purpose of validation, and the output file does not necessarily contain all the required attributes designed for [passenger links](https://github.com/lmz/dyno-path/blob/patch-1/files/links.md) output. 

---
#### Prerequisites:
* Find stop_id's for boarding/alighting locations in OBS file by running [add\_StopID\_OBS.py](https://github.com/psrc/FastTrips_PathChoice_Validation/blob/master/OBS_to_FToutput/Add_StopID_OBS/add_StopID_OBS.py) .