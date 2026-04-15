# Infrastructure Extraction Protocol

Extract infrastructure patterns that define how data flows *outside* of databases and APIs — cloud storage, message queues, scheduled jobs, deployment topology, and configuration surfaces. Especially important for pipeline/orchestration services with few or no database entities.

**Skip condition:** If a service already has rich SCH- and API- extractions (10+ entities, 20+ endpoints), infrastructure extraction is lower priority. Focus on services where API + ERD extraction produced thin results.

## Detection signals

For each repo, scan for:

1. **Cloud storage clients:** `google.cloud.storage`, `boto3`, `s3fs`, `gcsfs` in dependency files. If found, grep source code for path-building patterns: `gs://`, `s3://`, f-strings or `.format()` calls constructing storage paths, constants defining bucket names or path prefixes.

2. **Message queues:** `celery`, `pika`, `kombu`, `confluent-kafka`, `kafka-python` in deps. If found, scan for task definitions, queue names, topic names, consumer group configs.

3. **Deployment topology:** `docker-compose.yml`, `compose.yaml`, Dockerfiles, `helm/`, `kubernetes/`, `k8s/` directories. Scan for service definitions, port mappings, volume mounts, environment variable references.

4. **Configuration surface:** `.env.example`, `.env.template`, or settings modules that read from environment. Extract the list of expected env vars, which are secrets vs config, and what they connect to.

5. **Scheduled jobs / cron:** Prefect schedules, Celery beat configs, cron definitions, APScheduler configs. Extract job names, schedules, and I/O descriptions.

## Output files

Write to `sources/infra/{service}/`. If no infrastructure signals are found for a service, skip it. Do not create empty files.

### `storage.md`

```markdown
# Storage Patterns — {service}

> Extracted by scanning source code for cloud storage path-building patterns.

## Buckets

| Bucket / Prefix | Purpose | Code Reference |
|----------------|---------|----------------|
| {bucket-name or env var} | {what it stores} | `{path/to/config}` |

## Path Conventions

| Pattern | Example | Used In |
|---------|---------|---------|
| `{path template with placeholders}` | `gs://bucket/projects/123/datasets/456/splits/train/` | `{source file}` |

## File Formats

| Format | Extension | Schema/Fields | Used In |
|--------|-----------|--------------|---------|
| {Parquet/CSV/JSON/Avro/Protobuf} | {.parquet, .csv} | {key fields if discoverable} | `{source file}` |
```

### `runtime.md`

```markdown
# Runtime Topology — {service}

> Extracted from docker-compose/Kubernetes/Helm configurations.

## Services

| Service | Image/Build | Ports | Depends On | Purpose |
|---------|------------|-------|------------|---------|
| {service-name} | {image or build context} | {ports} | {dependencies} | {what it does} |

## Environment Variables

| Variable | Source | Purpose | Secret? |
|----------|--------|---------|---------|
| {VAR_NAME} | {.env.example / docker-compose / settings} | {what it configures} | {yes/no} |

## Volumes / Storage Mounts

| Mount | Host Path / Volume | Container Path | Purpose |
|-------|-------------------|----------------|---------|
```

### `queues.md`

```markdown
# Message Queues — {service}

> Extracted from task/consumer definitions in source code.

## Tasks / Consumers

| Name | Queue/Topic | Trigger | Input | Output | Retry | Code |
|------|------------|---------|-------|--------|-------|------|
| {task-name} | {queue or topic} | {schedule/event/manual} | {params} | {result} | {policy} | `{source}` |
```

## Report format

After extraction, report:

```
Infrastructure patterns extracted:

| Service  | Storage | Runtime | Queues | Key Finding |
|----------|---------|---------|--------|-------------|
| Pipeline | 3 buckets, 12 path patterns | 4 Docker services | 0 | GCS-centric data flow |
| Orders   | 0 | 2 Docker services | 3 Celery tasks | Background job processing |
| Platform | 0 | 5 Docker services | 0 | Multi-service deployment |
```
