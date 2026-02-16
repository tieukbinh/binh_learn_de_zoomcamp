import os
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from google.cloud import storage
from google.api_core.exceptions import NotFound, Forbidden
import time


# Change this to your bucket name
BUCKET_NAME = "dezoomcamp-ny-taxi-0119"

client = storage.Client(project='de-zoomcamp-2026-486710')
bucket = client.bucket(BUCKET_NAME)


BASE_URL = "https://github.com/DataTalksClub/nyc-tlc-data/releases/download"
DATASETS = ["yellow", "green"]
MONTHS = [f"{i:02d}" for i in range(1, 13)]
YEARS = [2019, 2020]
DOWNLOAD_DIR = "/Users/tieukbinh/Desktop/Data Engineering/de_zoomcamp/04_analytics_engineering/stage_taxi_download"

CHUNK_SIZE = 8 * 1024 * 1024

os.makedirs(DOWNLOAD_DIR, exist_ok=True)




def download_file(params):
    dataset, year, month = params
    url = f"{BASE_URL}/{dataset}/{dataset}_tripdata_{year}-{month}.csv.gz"
    file_path = os.path.join(DOWNLOAD_DIR, f"{dataset}_tripdata_{year}-{month}.csv.gz")

    try:
        print(f"Downloading {url}...")
        urllib.request.urlretrieve(url, file_path)
        print(f"Downloaded: {file_path}")
        return file_path
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return None


def create_bucket(bucket_name):
    try:
        # Get bucket details
        bucket = client.get_bucket(bucket_name)

        # Check if the bucket belongs to the current project
        project_bucket_ids = [bckt.id for bckt in client.list_buckets()]
        if bucket_name in project_bucket_ids:
            print(
                f"Bucket '{bucket_name}' exists and belongs to your project. Proceeding..."
            )
        else:
            print(
                f"A bucket with the name '{bucket_name}' already exists, but it does not belong to your project."
            )
            sys.exit(1)

    except NotFound:
        # If the bucket doesn't exist, create it
        bucket = client.create_bucket(bucket_name)
        print(f"Created bucket '{bucket_name}'")
    except Forbidden:
        # If the request is forbidden, it means the bucket exists but you don't have access to see details
        print(
            f"A bucket with the name '{bucket_name}' exists, but it is not accessible. Bucket name is taken. Please try a different bucket name."
        )
        sys.exit(1)


def verify_gcs_upload(blob_name):
    return storage.Blob(bucket=bucket, name=blob_name).exists(client)


def upload_to_gcs(file_path, max_retries=3):
    filename = os.path.basename(file_path)

    if filename.startswith("yellow"):
        folder = "yellow"
    elif filename.startswith("green"):
        folder = "green"
    else:
        print(f"Unknown dataset for file {filename}, skipping upload.")
        folder = "unknown"

    blob_name = f"{folder}/{filename}"
    blob = bucket.blob(blob_name)
    blob.chunk_size = CHUNK_SIZE


    for attempt in range(max_retries):
        try:
            print(f"Uploading {file_path} to {BUCKET_NAME} (Attempt {attempt + 1})...")
            blob.upload_from_filename(file_path)
            print(f"Uploaded: gs://{BUCKET_NAME}/{blob_name}")

            if verify_gcs_upload(blob_name):
                print(f"Verification successful for {blob_name}")
                return
            else:
                print(f"Verification failed for {blob_name}, retrying...")
        except Exception as e:
            print(f"Failed to upload {file_path} to GCS: {e}")

        time.sleep(5)

    print(f"Giving up on {file_path} after {max_retries} attempts.")


if __name__ == "__main__":
    create_bucket(BUCKET_NAME)

    # Generate all combinations of dataset, year, and month
    download_params = [
        (dataset, year, month) 
        for dataset in DATASETS 
        for year in YEARS 
        for month in MONTHS
        ]
    # Download files in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=4) as executor:
        file_paths = list(executor.map(download_file, download_params))

    #Collect file paths in a list to ensure we have all downloads before starting uploads
    file_paths = [
        os.path.join(DOWNLOAD_DIR, f)
        for f in os.listdir(DOWNLOAD_DIR)
        if f.endswith(".csv.gz")
    ]
    print(f"Starting upload {len(file_paths)} files to GCS...")
   
    # Upload files to GCS in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(upload_to_gcs, filter(None, file_paths)))  # Remove None values

    print("All files processed and verified.")
