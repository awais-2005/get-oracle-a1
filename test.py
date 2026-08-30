import threading
import time

def abc(i, st):
    while True:
        if st.is_set():
            break
        print(i)
        i += 1
        time.sleep(1)


stop = threading.Event()

thread = threading.Thread(target=abc, args=(1, stop))

thread.start()
input("Press key exit: ")
stop.set()
