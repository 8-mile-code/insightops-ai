FROM apache/airflow:3.2.2

RUN pip install --no-cache-dir clickhouse-connect==1.3.0

USER root

RUN mkdir -p /opt/airflow/config \
    && chown airflow:0 /opt/airflow/config \
    && chmod 770 /opt/airflow/config

COPY --chown=airflow:0 \
    docker/airflow/init_simple_auth.py \
    /opt/airflow/init_simple_auth.py

USER airflow
