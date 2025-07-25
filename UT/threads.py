import threading
import time

start_time = time.perf_counter()

def do_domething():
    # Placeholder for the function that does something
    print("Doing something...")
    print("Do nothing, sleeping for some seconds...")
    time.sleep(1)
    print("woah, that was a long sleep")

t1 = threading.Thread(target=do_domething)
t2 = threading.Thread(target=do_domething)

t1.start()
t2.start()

t1.join()
t2.join()
print("Both threads have finished execution.")
end_time = time.perf_counter()
print(f"Total time taken: {end_time - start_time:.2f} seconds")