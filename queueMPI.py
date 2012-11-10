#!/software/python-2.7.3/bin/python
# MPI producer + multiple consumer implementation

# Rank 1 pushes work onto the queue
# Ranks > 1 consume the work
# Rank 0 co-ordinates

from mpi4py import MPI
import time
import random

class queue:
    def __init__(self):
        self.queuelist=[]

    def __len__(self):
        return (len(self.queuelist))

    def __iter__(self):
        pass

    def enqueue(self,item):
        self.queuelist.insert(0,item)
        return(0)

    def dequeue(self):
        return(self.queuelist.pop())

    def length(self):
        pass

comm=MPI.COMM_WORLD
rank=comm.Get_rank()
size=comm.size

if rank==0: # master
    print size," processes launched"
    print "I am the master now! (rank 0)"    
    print "Rank 0 waiting for slaves..."
    files=queue()
    idleworkers=queue()

    while 1:
        data=comm.recv(source=MPI.ANY_SOURCE,tag=1)
        if data[0]=="NEWOBJ":
            files.enqueue(data[1])
        if data[0]=="WAITING":
            idleworkers.enqueue(data[1])

        # try for dispatch
        if len(files) > 0 and len(idleworkers) > 0:
            worker=idleworkers.dequeue()
            workunit=files.dequeue()
            # check for the end of workunit
            if workunit==None:
                print "Done"
                break

            comm.send(workunit,dest=worker,tag=1)
            # If this is a directory, we need to wait for the worker to finish before
            # we can continue

    # send shutdown to workers
    for r in range(1,size):
        comm.send(None,dest=r,tag=1)
    
elif rank==1:  # Producer
    file=0
    while file < 10:
        data=("NEWOBJ",file)
        comm.send(data,dest=0,tag=1)
        file+=1
    #Shutdown
    comm.send(("NEWOBJ",None),dest=0,tag=1)
    exit(0)

else:  # consumer
    count=0
    while 1:
        # ask for work
        data=("WAITING",rank)
        comm.send(data,dest=0,tag=1)
        work=comm.recv(source=0,tag=1)

        if work==None:
            print "rank %i shutdown" %rank
            exit(0)
        print "**Rank %i doing  work %i" %(rank,work)
        # do some work
        time.sleep(random.randint(0,5))
        # if we were doing a directory send confirmation
