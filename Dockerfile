FROM apache/flink:1.20.0-scala_2.12-java17

ENV HADOOP_VERSION=3.3.6

# -------------------------------------------------------------------
# Set workdir to Flink lib to drop extra jars
# -------------------------------------------------------------------
WORKDIR /opt/flink/lib

# --- Hadoop JARs (3.3.6) ---
RUN curl -fLO https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-common/${HADOOP_VERSION}/hadoop-common-${HADOOP_VERSION}.jar \
 && curl -fLO https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-hdfs/${HADOOP_VERSION}/hadoop-hdfs-${HADOOP_VERSION}.jar \
 && curl -fLO https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-mapreduce-client-core/${HADOOP_VERSION}/hadoop-mapreduce-client-core-${HADOOP_VERSION}.jar \
 && curl -fLO https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-auth/${HADOOP_VERSION}/hadoop-auth-${HADOOP_VERSION}.jar

# --- Hadoop-aws JARs (3.3.6) ---
RUN curl -fLO https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-client/3.3.6/hadoop-client-3.3.6.jar \
 && curl -fLO https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.6/hadoop-aws-3.3.6.jar \
 && curl -fLO https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.566/aws-java-sdk-bundle-1.12.566.jar

# --- Parquet JARs (1.13.0) ---
RUN curl -fLO https://repo1.maven.org/maven2/org/apache/parquet/parquet-jackson/1.13.0/parquet-jackson-1.13.0.jar \
 && curl -fLO https://repo1.maven.org/maven2/org/apache/parquet/parquet-encoding/1.13.0/parquet-encoding-1.13.0.jar \
 && curl -fLO https://repo1.maven.org/maven2/org/apache/parquet/parquet-common/1.13.0/parquet-common-1.13.0.jar \
 && curl -fLO https://repo1.maven.org/maven2/org/apache/parquet/parquet-format-structures/1.13.0/parquet-format-structures-1.13.0.jar \
 && curl -fLO https://repo1.maven.org/maven2/org/apache/parquet/parquet-column/1.13.0/parquet-column-1.13.0.jar \
 && curl -fLO https://repo1.maven.org/maven2/org/apache/parquet/parquet-hadoop/1.13.0/parquet-hadoop-1.13.0.jar

# --- Flink Kafka SQL Connector (3.4.0-1.20) ---
RUN curl -fLO https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-kafka/3.4.0-1.20/flink-sql-connector-kafka-3.4.0-1.20.jar

# --- Flink Parquet Connector (1.20.0) ---
RUN curl -fLO https://repo1.maven.org/maven2/org/apache/flink/flink-parquet/1.20.0/flink-parquet-1.20.0.jar
# --- Woodstox (6.5.1) ---
RUN curl -fLO https://repo1.maven.org/maven2/com/fasterxml/woodstox/woodstox-core/6.5.1/woodstox-core-6.5.1.jar

# --- StAX API (1.0-2) ---
RUN curl -fLO https://repo1.maven.org/maven2/javax/xml/stream/stax-api/1.0-2/stax-api-1.0-2.jar

# -------------------------------------------------------------------
# Configure Flink REST API / Web UI to be accessible externally
# -------------------------------------------------------------------
WORKDIR /opt/flink
RUN echo "rest.address: 0.0.0.0" >> conf/flink-conf.yaml \
 && echo "rest.bind-address: 0.0.0.0" >> conf/flink-conf.yaml \
 && echo "rest.port: 8081" >> conf/flink-conf.yaml

EXPOSE 8081

# -------------------------------------------------------------------
# Start Flink cluster
# -------------------------------------------------------------------
WORKDIR /opt/flink/bin
CMD ["./start-cluster.sh"]
