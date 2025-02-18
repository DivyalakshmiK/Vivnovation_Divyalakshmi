# Project Documentation

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
3. Copy the contents of `app.py` into a new cell and execute it.
4. Create a folder named **"geocoded"**.
5. Upload all local files from the "geocoded" directory into the newly created folder in Colab.
6. Run the respective cells to complete the process.


