-- Create a unified external dataset for yellow taxi Jan to Jun 2024
CREATE OR REPLACE EXTERNAL TABLE de-zoomcamp-2026-486710.ny_taxi.external_yellow_tripdata
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://dezoomcamp-ny-taxi-0119/yellow_tripdata_2024-*.parquet']
);

--Create native table of yellow taxi
CREATE OR REPLACE TABLE de-zoomcamp-2026-486710.ny_taxi.native_yellow_tripdata AS
SELECT * FROM de-zoomcamp-2026-486710.ny_taxi.external_yellow_tripdata
;


-- Query to count distinct number of PULocationIDs
-- on external dataset
SELECT
  COUNT(DISTINCT PULocationID) PULid_counts
FROM de-zoomcamp-2026-486710.ny_taxi.external_yellow_tripdata
;

-- on native dataset
SELECT
  COUNT(DISTINCT PULocationID) AS distinct_pu_locations
FROM de-zoomcamp-2026-486710.ny_taxi.native_yellow_tripdata
;

-- Count fare_amount = 0
SELECT 
  COUNT (*) 
FROM de-zoomcamp-2026-486710.ny_taxi.native_yellow_tripdata
WHERE fare_amount = 0
;

-- Create a table Partitioned by tpep_dropoff_datetime and Clustered on VendorID
CREATE OR REPLACE TABLE de-zoomcamp-2026-486710.ny_taxi.yellow_tripdata_partitioned_clustered
PARTITION BY DATE(tpep_dropoff_datetime)
CLUSTER BY VendorID
AS
SELECT *
FROM de-zoomcamp-2026-486710.ny_taxi.native_yellow_tripdata
;

-- Query distinct VendorIDs between 2024-03-01 and 2024-03-15
-- on partintioned and clustered table
SELECT DISTINCT
  VendorID
FROM de-zoomcamp-2026-486710.ny_taxi.yellow_tripdata_partitioned_clustered
WHERE DATE(tpep_dropoff_datetime)
      BETWEEN DATE '2024-03-01' 
        AND DATE '2024-03-15'
;

-- on non-partitioned and non-clustered table
SELECT DISTINCT
  VendorID
FROM de-zoomcamp-2026-486710.ny_taxi.native_yellow_tripdata
WHERE DATE(tpep_dropoff_datetime)
      BETWEEN DATE '2024-03-01' 
        AND DATE '2024-03-15'
;

-- Optional question
SELECT
  COUNT(*)
FROM de-zoomcamp-2026-486710.ny_taxi.native_yellow_tripdata
;




