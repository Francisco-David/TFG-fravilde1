import pycamunda
import time

# REST API endpoint
url = 'http://localhost:8080/hello-world'

def run_worker():
    while True:
        fetch = pycamunda.externaltask.FetchAndLock(
            url=url,
            worker_id='python-worker',
            max_tasks=1,
            topics=[{'topicName': 'hello-topic', 'lockDuration': 10000}]
        )
        tasks = fetch()
        if not tasks:
            time.sleep(1)
            continue
        task = tasks[0]
        print(f"Fetched task id={task.id_}, topic={task.topic_name}")

        # Optionally process task variables here

        complete = pycamunda.externaltask.Complete(
            url=url,
            id_=task.id_,
            worker_id='python-worker'
        )
        complete()
        print(f"Completed task id={task.id_}")

if __name__ == '__main__':
    print("Starting external task worker...")
    run_worker()
