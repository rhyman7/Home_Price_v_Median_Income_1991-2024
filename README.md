# Home Price v Median Income 1991 - 2024

## Project Overview:
The purpose of this project is to compare the cost of purchasing a home to the median income on a state by state basis between the years of 1991 and 2024. Data gathered from the Federal Housing Finance Agency (FHFA) and the United States Census Bureau will be used to make this determination. FHFA data will provide the change in the Housing Price Index (HPI), while the United States Census Bureau data will provide the median income data. 

## Project Setup Instructions:
1. Clone the repository
```bash
git clone https://github.com/rhyman7/Home_Price_v_Median_Income_1991-2024.git
```
2. After you have cloned the repository to your machine, navigate to the project folder in GitBash/Terminal.
```bash
cd [your_project_folder]
```
3. Create Virtual Environment & Install Dependencies.
```bash
# Windows
python -m venv venv
# Mac/Linux
python3 -m venv venv

# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate  

pip install -r requirements.txt
```
4. Open ```dataset_cleaning_hpi_income.ipynb``` for understanding of how data was cleaned and median income dataset was reshaped.
5. Open ```sql_and_visuals.ipynb``` for all plots and SQL database.
6. When finished with repo deactivate virtual environment, 
```bash
# For Mac/Linux and Windows
deactivate
```
## Data Dictionary
### Variables from hpi_clean.csv:
*hpi_type       (str)           Type of housing transaction  
*hpi_flavor     (str)           Methodologies to measure price change
*frequency      (str)           How often the data is collected       
*level          (str)                 
*place_name     (str)           State, city, or division data was collected for   
*place_id       (str)           Unique identifier for each area data is collected on     
*yr             (int64)         Year data was collected
*period         (int64)         Can refer to a year or month depending on the frequency data was collected
*index_nsa      (float64)       Number representing the HPI index for the period data was collected. Not seasonally adjusted
*index_sa       (float64)       Number representing the seasonally adjusted HPI

### Variables for median_income_clean_w_change.csv
*place_name     (str)           State data was collected on
*yr             (int64)         Year data was collected
*median_income  (str)           Median income for the reported year
*change         (float64)       Percent change from the baseline of 1991


## Technologies Used
*Python (Numpy, Matplotlib, Pandas, Plotly)
*Jupyter Notebook
*SQLite
*VS Code
*Git & GitHub

## Data Sources
Federal Housing Finance Agency: https://www.fhfa.gov/data/hpi/datasets?tab=master-hpi-data(historical

United States Census Bureau: https://www.census.gov/data/tables/time-series/demo/income-poverty/historical-income-households.html