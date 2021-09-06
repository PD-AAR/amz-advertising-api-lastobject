from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from google.api_core.exceptions import BadRequest
from google.cloud.bigquery.schema import SchemaField

import datetime
import logging
logging.basicConfig(level='INFO')
import re

def get_schema_from_json_list(project_id, dataset, json_list):
    json_list = format_list_of_dicts_for_bq(json_list)
    bq_client = bigquery.Client(project=project_id)
    table = "temp_table_for_schema_definition_xxx"

    # Check if BQ Dataset exist for customer else create it
    dataset_id_constructor = f"{project_id}.{dataset}"
    try:
        bq_client.get_dataset(dataset)
    except NotFound:
        logging.info(f"Dataset with id {dataset} not found - creating it.")
        dataset = bigquery.Dataset(dataset_id_constructor)
        dataset.location = "EU"
        dataset = bq_client.create_dataset(dataset, timeout=30)
    
    table_id_constructor = f"{project_id}.{dataset}.{table}"
    try:
        bq_client.get_table(table_id_constructor)
    except NotFound:
        table = bigquery.Table(table_id_constructor)
        table = bq_client.create_table(table)
    
    job_config = bigquery.LoadJobConfig()
    job_config.write_disposition = bigquery.WriteDisposition.WRITE_TRUNCATE

    load_job = bq_client.load_table_from_json(json_list, table_id_constructor, job_config=job_config)
    logging.info('Starting job {}'.format(load_job.job_id))

    try:
        load_job.result()
        logging.info(f"Job {load_job.job_id} completed successfully!")
    except BadRequest as e:
        error_string = ""
        for e in load_job.errors:
            error_string += f"ERROR: {e['message']}\n"
        logging.error(error_string)
        raise Exception(error_string)

    table = bq_client.get_table(table_id_constructor)
    schema = table.schema

    schema_json = bq_client.schema_to_json(schema,"./temp_json_schema.json")

    bq_client.delete_table(table_id_constructor)
    return "Success"

def bq_load_json_list(project_id, dataset, table_name, json_list,partition_date,schema):
    json_list = format_list_of_dicts_for_bq(json_list)
    bq_client = bigquery.Client(project=project_id)

    bq_dataset = bq_client.dataset(dataset)


    table_id_constructor = f"{project_id}.{dataset}.{table_name}"
    # Check if table exists for view ID else create it
    try:
        table = bq_client.get_table(table_id_constructor)
    except NotFound:
        logging.info(f"Table with id {table_name} not found - creating it.")
        table = bigquery.Table(table_id_constructor, schema=schema)
        table.time_partitioning = bigquery.TimePartitioning(type_=bigquery.TimePartitioningType.DAY,field="date")
        logging.info(f"Table partitioned by DAY")
        table = bq_client.create_table(table)

    table = bq_dataset.table(f"{table_name}${partition_date}")
    # Place data in table
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        time_partitioning=bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="date"
        )
    )

    load_job = bq_client.load_table_from_json(json_list, table, job_config=job_config)

    try:
        return load_job.result()
    except BadRequest as e:
        error_string = ""
        for e in load_job.errors:
            error_string += f"ERROR: {e['message']}\n"
        logging.error(error_string)
        return error_string

def format_list_of_dicts_for_bq(list_of_dicts):
    list_to_return = []
    for dictionary in list_of_dicts:
        new_dict = {}
        for k,v in dictionary.items():
            cleaned_key = re.sub(r"[^0-9a-zA-Z]+","_",k).lower()
            try:
                v = float(v)
            except:
                v = v
            new_dict[cleaned_key] = v
        list_to_return.append(new_dict)
    return list_to_return