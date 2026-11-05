
from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator


default_args = {
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


with DAG(
    dag_id="usgs_earthquake_pipeline",
    description="Orchestrates the USGS earthquake data pipeline",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    dagrun_timeout=timedelta(minutes=15),
    tags=["earthquakes", "data-engineering"],
) as dag:

    run_earthquake_pipeline = BashOperator(
        task_id="run_earthquake_pipeline",
        bash_command="python /opt/airflow/project/src/earthquake_pipeline.py",
        execution_timeout=timedelta(minutes=10),
    )
