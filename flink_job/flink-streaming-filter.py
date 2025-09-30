from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment, EnvironmentSettings
from pyflink.datastream.checkpointing_mode import CheckpointingMode
from pyflink.datastream.checkpoint_storage import FileSystemCheckpointStorage

checkpoint_storage_path = "s3a://flink-filter/checkpoints-docker"
file_system_checkpoint_storage = FileSystemCheckpointStorage(checkpoint_storage_path)
env = StreamExecutionEnvironment.get_execution_environment()
env.set_parallelism(2) # Setting a low parallelism for local testing to avoid idle partitions.
env.enable_checkpointing(60000)  # every 1m
env.get_checkpoint_config().set_checkpointing_mode(CheckpointingMode.EXACTLY_ONCE)
env.get_checkpoint_config().set_checkpoint_storage(file_system_checkpoint_storage)
env_settings = EnvironmentSettings.in_streaming_mode()
t_env = StreamTableEnvironment.create(env, environment_settings=env_settings)
t_env.get_config().set_local_timezone("Asia/Jakarta")

#config:
#    'sink.partition-commit.trigger' = 'partition-time', 
#    'sink.partition-commit.policy.kind' = 'success-file',
#    'sink.partition-commit.delay' = '10s',
#   WATERMARK FOR event_time AS event_time - INTERVAL '10' MINUTE
#  event_time AS TO_TIMESTAMP_LTZ(`date`, 3),
#   'sink.batch.flush.on.checkpoint' = 'true',

# 2. Add necessary dependencies
# Flink requires connectors for Kafka and S3 (Parquet). You need to ensure these JAR files
# are available to your Flink job. The S3 connector for Hadoop is often the one to use.
# For local development, you typically place them in the 'opt' directory of your Flink installation.
# The following line can be used to add them dynamically if you are running from a client.
# t_env.get_config().set("pipeline.jars", "file:///path/to/flink-sql-connector-kafka-1.18.1.jar;file:///path/to/flink-s3-fs-hadoop-1.18.1.jar")

# 3. Kafka source
# Ensure the Kafka topic 'user_events' exists and has data.
t_env.execute_sql("""
CREATE TABLE user_events (
    id STRING,
                  `date` BIGINT,
    event ROW<event_type STRING,url STRING>
) WITH (
                  'connector' = 'kafka',
                  'topic' = 'user_events',
                  'properties.bootstrap.servers' = 'kafka:9092',
                  'properties.group.id' = 'testDocker',
                  'scan.startup.mode' = 'earliest-offset',
                  'format' = 'json',
                  'json.fail-on-missing-field' = 'true',
                  'json.ignore-parse-errors' = 'false'
)
""")

# 4. MinIO parquet sink for good events
# 'path.style.access' is crucial for MinIO, as it doesn't use virtual hosted style.
# The s3a:// prefix is used for Hadoop's S3 filesystem implementation, which you must have.
# Flink will read the S3 configuration from the environment variables set at the top of the script.
t_env.execute_sql("""
CREATE TABLE parquet_sink_good (
    user_id STRING,
    event_date STRING,
    event_ts TIMESTAMP(0),
    event_type STRING,
    url STRING
) PARTITIONED BY (event_date)
WITH (
    'connector' = 'filesystem',
    'path' = 's3a://flink-filter/flink-docker-good/',
    'format' = 'parquet',
    'sink.rolling-policy.file-size' = '5MB',
    'sink.rolling-policy.rollover-interval' = '60s',
    'parquet.compression' = 'SNAPPY'
)
""")

t_env.execute_sql("""
CREATE TABLE parquet_sink_bad (
    user_id STRING,
    event_date STRING,
    event_ts TIMESTAMP(0),
    event_type STRING,
    url STRING
) PARTITIONED BY (event_date)
WITH (
    'connector' = 'filesystem',
    'path' = 's3a://flink-filter/flink-docker-bad/',
    'format' = 'parquet',
    'sink.rolling-policy.file-size' = '5MB',
    'sink.rolling-policy.rollover-interval' = '60s',
    'parquet.compression' = 'SNAPPY'
)
""")


# 5. Flatten and filter the data
# Use a TEMPORARY TABLE instead of a view for better compatibility and to ensure a separate,
# defined table. Also, add the new field for user_id.
t_env.execute_sql("""
CREATE TEMPORARY VIEW flattened_events AS
SELECT
    id AS user_id,
    DATE_FORMAT(TO_TIMESTAMP_LTZ(`date`, 3), 'yyyy-MM-dd') AS event_date,
    TO_TIMESTAMP_LTZ(`date`, 3) AS event_ts,
    event.event_type,
    event.url
FROM user_events
""")
# 6. Use a Statement Set for atomic insertion into multiple sinks
# This ensures the 'flattened_events' view is only scanned once.
statement_set = t_env.create_statement_set()

# 7. Insert into the sink
# The WHERE clause is correct for filtering the data.
statement_set.add_insert_sql("""
INSERT INTO parquet_sink_good
SELECT
    user_id,
    event_date,
    event_ts,
    event_type,
    url
FROM flattened_events
WHERE event_type IN ('commented', 'liked')
""")

statement_set.add_insert_sql("""
INSERT INTO parquet_sink_bad
SELECT
    user_id,
    event_date,
    event_ts,
    event_type,
    url
FROM flattened_events
WHERE event_type NOT IN ('commented', 'liked')
""")

statement_set.execute()