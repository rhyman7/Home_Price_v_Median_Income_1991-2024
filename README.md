# Home Price v Median Income 1991 - 2024

The purpose of this project is to compare the cost of purchasing a home to the median income on a state by state basis between the years of 1991 and 2024. Data gathered from the Federal Housing Finance Agency (FHFA) and the United States Census Bureau will be used to make this determination. FHFA data will provide the change in the Housing Price Index (HPI), while the United States Census Bureau data will provide the median income data. First question is whether or not any state's median income has kept up with the rise in HPI. After that explore what states are closest and which are furthest. Additionally, have there been any nationwide trends during this timeframe?

## Installation

1. Clone the repository
```bash
  git clone https://github.com/rhyman7/Home_Price_v_Median_Income_1991-2024.git
```
2. After you have cloned the repository to your machine, navigate to the project folder in GitBash/Terminal.
```bash
cd [your_project_folder]
```
3. Create Virtual Environment, Activate, and Install Dependencies.

Windows
```bash
python -m venv venv
```
```bash
source venv/Scripts/activate
```
```bash
pip install -r requirements.txt
```

Linux/Mac
```bash
python3 -m venv venv
```
```bash
source venv/bin/activate
```
```bash
pip install -r requirements.txt
```
4. Open ```dataset_cleaning_hpi_income.ipynb``` for understanding of how data was cleaned and median income dataset was reshaped.
5. Open ```sql_and_visuals.ipynb``` for all plots and SQL database.
6. When finished with repo deactivate virtual environment.
Windows
```bash
deactivate
```

Linux/Mac
```bash
deactivate
```

## Data Sources
Federal Housing Finance Agency: https://www.fhfa.gov/data/hpi/datasets?tab=master-hpi-data(historical

United States Census Bureau: https://www.census.gov/data/tables/time-series/demo/income-poverty/historical-income-households.html
## Code Structure
The project is organized into data preparation, SQL querying, and visualization layers. Cleaned datasets are joined using state and year, enabling calculation of affordability metrics such as the gap between housing prices and income growth. Modular plotting functions allow flexible analysis by state and year, while a choropleth map provides geographic insights.
## Technology Used

*Python* – core programming language for analysis and development\
*Python Libraries* - Pandas, Numpy, Matplotlib, Plotly\
*Jupyter Notebook* – used for exploratory analysis and workflow documentation\
*SQLite* – simple relational database for local data storage and retrieval\
*VS Code* – development environment for coding and file organization\
*Git & GitHub* – used for version control and collaborative project sharing\
*Markdown* – used for writing notes, documentation, and explanations\
*AI* - Chat GPT was used for the ai_assist_animations.ipynb notebook

## Data Dictionary
Variables from hpi_clean.csv:
- hpi_type       (str)           Type of housing transaction  
- hpi_flavor     (str)           Methodologies to measure price change
- frequency      (str)           How often the data is collected       
- level          (str)           Level of agency resposible for data      
- place_name     (str)           State, city, or division data was collected for   
- place_id       (str)           Unique identifier for each area data is collected on     
- yr             (int64)         Year data was collected
- period         (int64)         Can refer to a year or month depending on the frequency data was collected
- index_nsa      (float64)       Number representing the HPI index for the period data was collected. Not seasonally adjusted
- index_sa       (float64)       Number representing the seasonally adjusted HPI

Variables for median_income_clean_w_change.csv
- place_name     (str)           State data was collected on
- yr             (int64)         Year data was collected
- median_income  (str)           Median income for the reported year
- change         (float64)       Percent change from the baseline of 1991

## Findings
The data shows that by 2024 the Housing Price Index (HPI) is outpacing median income in all 50 states, indicating a widespread decline in housing affordability. While HPI had already begun to exceed income growth prior to 2020, the gap widened significantly during the COVID-19 period and reached a peak around 2022.

Through additional research I found that this acceleration appears to be driven by several macroeconomic factors, including historically low mortgage interest rates, limited housing supply, and elevated demand, all of which contributed to rapid increases in housing prices relative to income.

In 2021, median income growth exceeded HPI growth in only three states (Indiana, Mississippi, and Illinois). Since that time, no state has experienced income growth outpacing housing prices, reinforcing the persistence of the affordability gap. 

As of 2024 the four states with smallest gap between HPI and median income are: 
- Mississippi 
- West Virginia 
- Illinois 
- Connecticut 

While the four states with the highest gap are: 
- Utah
- Montana
- Colorado
- Oregon

This analysis highlights a significant shift in housing affordability across the United States over the period 1991–2024. Since 2021, no state's median income has outpaced HPI and we are currently living in the only period from the dataset where that is the case. The American Dream is becoming just that, a dream, for more and more people. 
