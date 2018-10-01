broker_url = "pyamqp://guest:guest@rabbit//"
result_backend = "redis://redis/0"

task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'UTC'
enable_utc = True