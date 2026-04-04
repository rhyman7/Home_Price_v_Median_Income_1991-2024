# Home Price v Median Income 1991 - 2024

## Project Overview:
The purpose of this project is to determine whether or not median income has kept up with the cost of buying a home on a state by state basis. Data gathered from the Federal Housing Finance Agency (FHFA) and the United States Census Bureau will be used to make this determination. FHFA data will provide the change in the Housing Price Index (HPI), while the United States Census Bureau data will provide the median income data. 

## Data Sources
+ **Federal Housing Finance Agency**: Data provides change in Housign Price Index (HPI) 1991 - 2024 
+ **United States Census Bureau**: Data provides change in Median Income 1991 - 2024

## Project Setup Instructions:
### 1️⃣ Clone the Repository

```bash
git clone https://github.com/rhyman7/Home_Price_v_Median_Income_1991-2024.git
```

After you have cloned the repository to your machine, navigate to the project folder in GitBash/Terminal.

```bash
cd [your_project_folder]
```

### 2️⃣ Create Virtual Environment & Install Dependencies

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

### 3️⃣ Run the Jupyter Notebook

```bash
jupyter notebook
```

**Windows:** Access the jupyter server by copying and pasting one of the provided URLs in the output,
or CTRL + click the link in the output.

Open the file.  Execute each cell in order or select "Run All" at the top of the notebook.

### 4️⃣ Deactivate Virtual Environment

When finished working in the repo, deactivate the virtual environment.

```bash
# For Mac/Linux and Windows
deactivate
```

## Data Sources
Federal Housing Finance Agency: https://www.fhfa.gov/data/hpi/datasets?tab=master-hpi-data(historical

United States Census Bureau: https://www.census.gov/data/tables/time-series/demo/income-poverty/historical-income-households.html