from modules import BACKGROUND_TASK_NUMBER_OF_THREADS, queue, threading
from utils import Logging

Log = Logging(__name__)

task_queue = queue.Queue()


def worker():
    while True:
        try:
            task = task_queue.get(timeout=1)
            Log.info(f"Executing task: {task}")
            task()  # Execute the task
            Log.info(f"Task {task} completed")
            task_queue.task_done()
        except queue.Empty:
            continue


def start_worker():
    Log.info(f"Starting worker threads ({BACKGROUND_TASK_NUMBER_OF_THREADS})")
    # Start worker threads
    for _ in range(BACKGROUND_TASK_NUMBER_OF_THREADS):
        t = threading.Thread(target=worker, daemon=True)
        t.start()


def add_task_in_queue(task):
    task_queue.put(task)


if __name__ == "__main__":
    # Start the worker threads when the module is imported
    start_worker()
    # Example usage
    add_task_in_queue(lambda: print("Sending email to user@example.com"))
    add_task_in_queue(lambda: print("Sending email to admin@example.com"))
    add_task_in_queue(lambda: print("Sending email to support@example.com"))
    # Wait for all queued emails (optional)
    task_queue.join()  # Note: This will block until all tasks have been processed
