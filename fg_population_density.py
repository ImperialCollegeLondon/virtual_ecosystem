""" 
Tool 1- Calculating population density for each functional group over time. 
Purpose: This tool is created to calculates the population density (indv/m2) for each functional group using the animal cohort data.  
Method: Sum individuals for each FG per timestep and then divide the total individuals by total simulation area. 
Input file: animal_cohort_data.csv
Output: Line graph showing population density over time and each functional group is plotted as a separate line. 
"""
import pandas as pd
import matplotlib.pyplot as plt
def fg_population_density(csv_path, cell_size, n_cells_x, n_cells_y):
    #read cohort data
    df= pd.read_csv(csv_path)
    #group the functional group per each timestep 
    d= df.groupby(["time_index", "functional_group"])["individuals"]. sum()
    d= d.reset_index()
    """Assumptions: The current simulation landscape area unit is in (m2) and need to be adjusted if grid size or cell size changes for each run. Current assumption is 50x50 grid cells with 100mx 100m per cell."""
    #calculate simulation landscape area
    cell_area= cell_size*cell_size
    total_area= cell_area* n_cells_x * n_cells_y
    #calculate population density 
    d["density"]= d["individuals"]/total_area 
    print(d.head())
    #loop through each functional group(fg) present in the data set
    for fg in d["functional_group"].unique():
        fg_data= d[d["functional_group"]== fg]
        plt.plot(fg_data["time_index"], fg_data["density"], label= fg)
    plt.xlabel("Time_index")
    plt.ylabel("Population density (indv/m²)")
    plt.title("Functional Group Population Density Over Time")
    plt.legend()
    plt.show()

fg_population_density("C:/Projects/ve_simulation_user/animal_cohort_data_example.csv",100,50,50)