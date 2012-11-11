#!/usr/bin/python2.7
# MPI producer + multiple consumer implementation

# Rank 1 pushes work onto the queue
# Ranks > 1 consume the work
# Rank 0 co-ordinates

from mpi4py import MPI

from multiprocessing import Process,Pipe
# Efficient queue object
from collections import deque
import time
import random

def SpawnScanner():
    pipesend,piperecv=Pipe()
    p=Process(target=ProduceWork,args=(pipesend,))
    p.start()
    return(piperecv)

def ProduceWork(pipe):    
    file=0
    while file < 10:
        pipe.send(file)
        file+=1
    #Shutdown
    pipe.send("EOF")
    return(0)


def DispatchWork(pipe):
    files=deque()
    idleworkers=deque()

    while 1:
        if pipe.poll():
            data=pipe.recv()
            files.appendleft(data)

        if comm.Iprobe(source=MPI.ANY_SOURCE,tag=1):
            status,data=comm.recv(source=MPI.ANY_SOURCE,tag=1)
            idleworkers.appendleft(data)
        
        # try for dispatch
        if len(files) > 0 and len(idleworkers) > 0:
            worker=idleworkers.pop()
            workunit=files.pop()
            # check for the end of queue
            if workunit=="EOF":
                print "Done"
                break
            
            comm.send(workunit,dest=worker,tag=1)
            # If this is a directory, we need to wait for the worker to finish before
            # we can continue

            if workunit==5:
                print "5 is blocking"
                status,data=comm.recv(source=worker,tag=1)
                print status,data
                print "unblocking 5"
                idleworkers.appendleft(data)

def ConsumeWork():
    while 1:
        comm.isend(("WAITING",rank),dest=0,tag=1)
        work=comm.recv(source=0,tag=1)
        if work==None:
            print "rank %i shutdown" %rank
            exit(0)
        print "**Rank %i doing  work %i" %(rank,work)
        # do some work
        time.sleep(random.randint(0,5))
        # if we were doing a directory send confirmation


def ShutdownWorkers():
    # send shutdown to workers
    for r in range(1,size):
        comm.isend(None,dest=r,tag=1)

comm=MPI.COMM_WORLD
rank=comm.Get_rank()
size=comm.size
        
if rank==0: # master
    print size," processes launched"
    print "I am the master now! (rank 0)"    

    pipe=SpawnScanner()
    print "Rank 0 waiting for slaves..."
    DispatchWork(pipe)
    ShutdownWorkers()

else:  # consumer
    ConsumeWork()
