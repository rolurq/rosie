import time
import newserver
import thread

__author__ = 'Silvio'

if __name__ == '__main__':
    my_server = newserver.newServer(50007)
    thread.start_new_thread(my_server.run, ())
    thread.start_new_thread(my_server.sender_thread(), ())

    while 1:
        time.sleep(2)
