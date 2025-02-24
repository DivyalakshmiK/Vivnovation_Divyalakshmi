# Project Documentation

[![Execution video](https://github.com/DivyalakshmiK/Vivnovation_Divyalakshmi/blob/main/_output_images/output1.jpg)](https://drive.google.com/file/d/1em5KLKXEY1U03rvqNW_HIBG2J4M5wD3P/view?usp=sharing)

[Drive link for the execution video](https://drive.google.com/file/d/1em5KLKXEY1U03rvqNW_HIBG2J4M5wD3P/view?usp=sharing)


## Files Explanation

### Data Files
- **cleaned_xl_files/**: Contains Excel files generated after processing JSON records. Unnecessary columns have been removed.
- **geocoded/**: Contains Excel files with additional latitude and longitude columns, derived using an open-source geocoding API.
- **output/**: Stores JSON files fetched from the NPI registry based on specified ZIP codes within a defined MSA.

### Scripts
- **app.py**: Main script for executing the complete workflow.
- **find_geocode.py**: Extracts latitude and longitude from the address column in Excel files and saves the updated files in the "geocoded" directory.
- **py_to_xl.py**: Converts JSON records into cleaned Excel files.
- **zip_to_msa**: Complete dataset mapping ZIP codes to counties and MSA (Metropolitan Statistical Areas).

## Running the Application

To execute the application in Google Colab:

1. Open Google Colab and create a new notebook.
2. Install required dependencies by running:
   ```sh
   !pip install pandas folium ipywidgets ipython
   ```
3. Create a folder named **"geocoded"**.
4. Upload all local files from the local "geocoded" directory (excel files) into the newly created folder in Colab.
5.  Copy the contents of `app.py` into a new cell.
6. Run the respective cell to complete the process.

## Output Images

![Plotting healthcare providers](https://github.com/DivyalakshmiK/Vivnovation_Divyalakshmi/blob/main/_output_images/output1.jpg)

![NP, Phone number filters](https://github.com/DivyalakshmiK/Vivnovation_Divyalakshmi/blob/main/_output_images/output5.jpg)

![Nearest provider lookup](https://github.com/DivyalakshmiK/Vivnovation_Divyalakshmi/blob/main/_output_images/output6.jpg)

![Filters for specializations](https://github.com/DivyalakshmiK/Vivnovation_Divyalakshmi/blob/main/_output_images/output3.jpg)

![Dropdown for selecting respective MSA](https://github.com/DivyalakshmiK/Vivnovation_Divyalakshmi/blob/main/_output_images/output2.jpg)



