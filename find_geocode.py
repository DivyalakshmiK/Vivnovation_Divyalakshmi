import asyncio
import json
import urllib.parse
from pathlib import Path

import aiohttp
import pandas as pd


async def geocode_address_census(session, address):
    """
    Asynchronously geocode a single address using the Census Geocoding API.
    """
    try:
        encoded_address = urllib.parse.quote(address)
        base_url = (
            "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
        )
        url = f"{base_url}?address={encoded_address}&benchmark=Public_AR_Current&format=json"

        async with session.get(url) as response:
            data = await response.json()

        if data.get("result", {}).get("addressMatches"):
            match = data["result"]["addressMatches"][0]
            return {
                "latitude": match["coordinates"]["y"],
                "longitude": match["coordinates"]["x"],
                "status": "matched",
            }
        return {"latitude": None, "longitude": None, "status": "no_match"}
    except Exception:
        return {"latitude": None, "longitude": None, "status": "error"}


async def process_address(index, address, df, session, semaphore, total_rows):
    """
    Process a single address using a semaphore to limit concurrent API calls.
    """
    async with semaphore:
        result = await geocode_address_census(session, address)
    df.at[index, "latitude"] = result["latitude"]
    df.at[index, "longitude"] = result["longitude"]
    df.at[index, "geocode_status"] = result["status"]
    symbol = "✓" if result["status"] == "matched" else "x"
    print(f"{index+1}/{total_rows} {symbol}", end=" ")


async def process_excel_file_async(
    input_file, output_dir, address_column, max_concurrent_requests=10
):
    """
    Asynchronously process a single Excel file:
      - Reads the Excel file.
      - Geocodes addresses concurrently (limited by a semaphore).
      - Writes the results to a new Excel file.
    """
    print(f"\nProcessing: {input_file.name}")
    df = pd.read_excel(input_file)
    total_rows = len(df)

    # Initialize new columns for geocoding results.
    df["latitude"] = None
    df["longitude"] = None
    df["geocode_status"] = None

    # Semaphore to limit concurrent API calls within this file.
    request_semaphore = asyncio.Semaphore(max_concurrent_requests)

    async with aiohttp.ClientSession() as session:
        tasks = []
        for index, row in df.iterrows():
            address = str(row[address_column])
            if pd.isna(address) or address.strip() == "":
                df.at[index, "geocode_status"] = "empty"
                print(f"{index+1}/{total_rows} -", end=" ")
                continue
            tasks.append(
                process_address(
                    index, address, df, session, request_semaphore, total_rows
                )
            )
        await asyncio.gather(*tasks)

    # Remove rows where geocoding was unsuccessful.
    df = df.dropna(subset=["latitude", "longitude"])

    output_file = output_dir / f"{input_file.stem}_geocoded_async.xlsx"
    # Use a context manager to ensure the file handle is closed promptly.
    with pd.ExcelWriter(output_file) as writer:
        df.to_excel(writer, index=False)
    print(f"\nCompleted processing {input_file.name}")


async def process_excel_file_with_semaphore(
    input_file,
    output_dir,
    address_column,
    file_semaphore,
    max_concurrent_requests,
):
    """
    Wrapper function to process an Excel file while ensuring that only a limited number
    of files are processed concurrently.
    """
    async with file_semaphore:
        await process_excel_file_async(
            input_file, output_dir, address_column, max_concurrent_requests
        )


def process_directory_async(
    input_dir,
    output_dir,
    address_column,
    max_concurrent_files=5,
    max_concurrent_requests=10,
):
    """
    Process all Excel files in the input directory asynchronously.
      - Limits the number of concurrently processed files.
      - For each file, limits the number of concurrent API calls.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    excel_files = list(input_path.glob("*.xlsx"))
    if not excel_files:
        print("No Excel files found in the input directory.")
        return

    print(f"Found {len(excel_files)} Excel files to process")

    async def main():
        # Semaphore to limit how many files are processed at once.
        file_semaphore = asyncio.Semaphore(max_concurrent_files)
        tasks = [
            process_excel_file_with_semaphore(
                file,
                output_path,
                address_column,
                file_semaphore,
                max_concurrent_requests,
            )
            for file in excel_files
        ]
        await asyncio.gather(*tasks)
        print(f"\nAll done! Check results in: {output_path.absolute()}")

    asyncio.run(main())


if __name__ == "__main__":
    input_dir = "copied"  # Directory containing your Excel files.
    output_dir = "geocoded"  # Directory where results will be saved.
    address_column = "Address"
    process_directory_async(input_dir, output_dir, address_column)
