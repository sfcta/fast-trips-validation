# fast-trips-validation

Tableau workbooks for analyzing Fast-Trips outputs, with comparison to on-board survey data.

Tableau workbooks depend on typical Fast-Trips output files, and files that can be generated
from Jupyter notebooks in this repository, including:
- path_comparison.csv
- chosenpath_links_with_observed.csv

To generate these files, run all cells in **prepare_fasttrips.ipynb**. At the top of this notebook, specify a directory 
of existing Fast-Trips results, in which to save the additional csv files. In the Tableau workbook, point to this location. 

## Inputs

Under data/obs, find the latest version of on-board survey records "obs_chosenpaths_links.csv". The "prepare_fasttrips" notebook depends on this input to generate comparison csv files. The notebook "prepare_obs_links.ipynb" was used to clean and prepare "obs_chosenpaths_links.csv".  
