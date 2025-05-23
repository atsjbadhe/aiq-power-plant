from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
from io import BytesIO
import pandas as pd
import os
from botocore.exceptions import ClientError
import boto3
from minio import Minio
import traceback

from app.models import PowerPlant
from app.services import get_s3_client, get_data_from_s3, S3_BUCKET_NAME
from app.utils.data_cleaner import clean_csv_data, clean_excel_data, convert_to_api_format
from app.utils.logger import logger, log_audit

router = APIRouter(prefix="/api/power-plants", tags=["power-plants"])

# In-memory cache for available states
states_cache = None

@router.post("/upload")
async def upload_csv(
    file: UploadFile = File(...), 
    s3_client = Depends(get_s3_client)
):
    """
    Upload a CSV file to S3 bucket.
    The file should follow the structure of the GEN23 sheet from EPA's eGRID dataset.
    """
    logger.info(f"Received file upload request: {file.filename}")
    
    if not file.filename.endswith(('.csv', '.xlsx')):
        logger.warning(f"Rejected file upload: {file.filename} (unsupported file type)")
        raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")
    
    try:
        contents = await file.read()
        logger.debug(f"Read file contents: {file.filename} ({len(contents)} bytes)")
        
        # Clean and process the file data
        if file.filename.endswith('.csv'):
            logger.info(f"Processing CSV file: {file.filename}")
            df = clean_csv_data(contents)
        else:
            logger.info(f"Processing Excel file: {file.filename}")
            df = clean_excel_data(contents)
        
        # Convert to API format
        logger.debug("Converting data to API format")
        api_df = convert_to_api_format(df)
        
        if api_df.empty:
            logger.warning(f"Empty dataframe after processing: {file.filename}")
            raise HTTPException(
                status_code=400, 
                detail="Could not extract required data from the file. Ensure it has the necessary columns."
            )
        
        # Write cleaned data to a buffer
        buffer = BytesIO()
        api_df.to_csv(buffer, index=False)
        buffer.seek(0)
        
        # Object key for the file
        object_key = f"cleaned_{file.filename.rsplit('.', 1)[0]}.csv"
        logger.info(f"Uploading processed data to S3: {object_key}")
        
        # Upload to S3 - handle different client types
        if isinstance(s3_client, Minio):
            # For MinIO client
            logger.debug("Using MinIO client for upload")
            s3_client.put_object(
                bucket_name=S3_BUCKET_NAME,
                object_name=object_key,
                data=buffer,
                length=buffer.getbuffer().nbytes,
                content_type='text/csv'
            )
        else:
            # For boto3 client (default case)
            logger.debug("Using boto3 client for upload")
            s3_client.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=object_key,
                Body=buffer.getvalue()
            )
        
        # Clear the cache to refresh data
        logger.debug("Clearing states cache")
        global states_cache
        states_cache = None
        
        logger.info(f"File uploaded successfully: {object_key} ({len(api_df)} records)")
        return {
            "filename": object_key, 
            "status": "uploaded",
            "records_count": len(api_df)
        }
    
    except ClientError as e:
        logger.error(f"S3 error during file upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"S3 error: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@router.get("/states", response_model=List[str])
async def get_states(
    s3_client = Depends(get_s3_client)
):
    """
    Get list of all available states in the dataset.
    """
    logger.info("Fetching available states")
    global states_cache
    
    try:
        # Always fetch data to ensure we have the latest
        logger.debug("Fetching data from S3")
        data = await get_data_from_s3(s3_client)
        
        if data.empty:
            logger.warning("No data found in S3")
            return []
        
        # Get unique states from the data
        current_states = sorted(data["PSTATEABB"].unique().tolist())
        
        # Check if the states in the data match the cached states
        if states_cache is not None:
            cached_set = set(states_cache)
            current_set = set(current_states)
            
            # If the sets are different, update the cache
            if cached_set != current_set:
                logger.info(f"States have changed. Updating cache from {states_cache} to {current_states}")
                states_cache = current_states
            else:
                logger.debug("States match the cache")
        else:
            # Initialize cache if it's None
            logger.debug("Initializing states cache")
            states_cache = current_states
        
        logger.info(f"Found {len(states_cache)} states: {', '.join(states_cache)}")
        return states_cache
        
    except Exception as e:
        logger.error(f"Error retrieving states: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error retrieving states: {str(e)}")

@router.get("/", response_model=List[PowerPlant])
async def get_plants(
    state: str = Query(..., description="State abbreviation (e.g., CA, NY)"),
    limit: int = Query(10, description="Number of top plants to return"),
    s3_client = Depends(get_s3_client)
):
    """
    Get top N power plants by net generation for a specific state.
    """
    logger.info(f"Fetching top {limit} power plants for state: {state}")
    
    try:
        logger.debug("Fetching data from S3")
        data = await get_data_from_s3(s3_client)
        if data.empty:
            logger.warning("No data found in S3")
            return []
        
        # Filter by state and calculate totals for each plant
        state_data = data[data["PSTATEABB"] == state]
        
        if state_data.empty:
            logger.warning(f"No data found for state: {state}")
            return []
        
        logger.debug(f"Found {len(state_data)} records for state: {state}")
        
        # Group by plant and sum the generation values
        plant_totals = state_data.groupby(["ORISPL", "PNAME"]).agg({
            "GENNTAN": "sum"
        }).reset_index()
        
        # Sort by net generation (descending) and take top N
        plant_totals = plant_totals.sort_values("GENNTAN", ascending=False).head(limit)
        
        # Convert to list of PowerPlant models
        plants = [
            PowerPlant(
                id=str(row["ORISPL"]),
                name=row["PNAME"],
                state=state,
                netGeneration=float(row["GENNTAN"])
            )
            for _, row in plant_totals.iterrows()
        ]
        
        logger.info(f"Returning {len(plants)} power plants for state: {state}")
        return plants
    except Exception as e:
        logger.error(f"Error retrieving plants for state {state}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error retrieving plants: {str(e)}") 