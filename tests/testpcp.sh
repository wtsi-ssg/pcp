#!/bin/bash

PCP="../pcp"

setUp() {
    mkdir $SHUNIT_TMPDIR/a
    mkdir $SHUNIT_TMPDIR/b
}

tearDown() {
    rm -rf $SHUNIT_TMPDIR/a
    rm -rf $SHUNIT_TMPDIR/b
}

testBase() {
    $PCP -V 
    assertEquals "Basic check failed." 0 $?
}

testHelp() {
    RESULT=`mpirun -n 1 $PCP -h | grep "show this help message"`
    assertEquals  "MPI execution failed." "$RESULT" "  -h, --help     show this help message and exit"
}

test2procs() {
    RESULT=`mpirun -n 1 $PCP -v $SHUNIT_TMPDIR/a $SHUNIT_TMPDIR/b | grep "ERROR: Only 1 processes running"`
    assertEquals  "Program tried to run with only one MPI rank." "$RESULT" "ERROR: Only 1 processes running. Did you invoke me via mpirun?"

}

testcopy() {
    dd if=/dev/urandom bs=1M count=1 of=$SHUNIT_TMPDIR/a/testfile > /dev/null 2>&1
    mpirun -n 2 $PCP  $SHUNIT_TMPDIR/a $SHUNIT_TMPDIR/b 
    assertEquals "Basic copy failed" 0 $?
    cmp $SHUNIT_TMPDIR/a/testfile $SHUNIT_TMPDIR/b/testfile
    assertEquals "Basic copy failed" 0 $?
}

testcopyChecksum() {
    dd if=/dev/urandom bs=1M count=1 of=$SHUNIT_TMPDIR/a/testfile > /dev/null 2>&1
    mpirun -n 2 $PCP -c  $SHUNIT_TMPDIR/a $SHUNIT_TMPDIR/b 
    assertEquals "Basic copy failed" 0 $?
    cmp $SHUNIT_TMPDIR/a/testfile $SHUNIT_TMPDIR/b/testfile
    assertEquals "Basic copy failed" 0 $?
}

testchunkcopy() {
    dd if=/dev/urandom bs=1M count=10 of=$SHUNIT_TMPDIR/a/testfile > /dev/null 2>&1
    mpirun -n 2  $PCP -b 1  $SHUNIT_TMPDIR/a $SHUNIT_TMPDIR/b 
    assertEquals "File not copied in chunks" 0 $?
    cmp $SHUNIT_TMPDIR/a/testfile $SHUNIT_TMPDIR/b/testfile
    assertEquals "Chunk copy corrupted file" 0 $?
}

testmulticopy() {
    FILES=5
    RANKS=3
    for X in `seq 1 $FILES`  ; do
	dd if=/dev/urandom bs=1M count=1 of=$SHUNIT_TMPDIR/a/testfile$X > /dev/null 2>&1
    done
    mpirun -n $RANKS $PCP  $SHUNIT_TMPDIR/a $SHUNIT_TMPDIR/b 
    assertEquals "Copy failed" 0 $?
    for X in `seq 1 $FILES` ; do
	cmp $SHUNIT_TMPDIR/a/testfile$X $SHUNIT_TMPDIR/b/testfile$X
	assertEquals "Basic copy failed" 0 $?
    done
}


testpreserve() {
    FILES=5
    RANKS=2
    for X in `seq 1 $FILES`  ; do
	dd if=/dev/urandom bs=1M count=1 of=$SHUNIT_TMPDIR/a/testfile$X > /dev/null 2>&1
    done
    touch  -t 200001020300.00 $SHUNIT_TMPDIR/a/testfile1
    touch  -t 201002030610.12 $SHUNIT_TMPDIR/a/testfile2
    touch  -t 202003040920.45 $SHUNIT_TMPDIR/a/testfile3
    touch  -t 203004051230.32 $SHUNIT_TMPDIR/a/testfile4
    touch  -t 204005061544.23 $SHUNIT_TMPDIR/a/testfile5
    touch  -t 198501020300.00 $SHUNIT_TMPDIR/a

    mpirun -n $RANKS $PCP -p  $SHUNIT_TMPDIR/a $SHUNIT_TMPDIR/b 
    assertEquals "copy failed" 0 $?

    assertEquals "`stat -c%y  $SHUNIT_TMPDIR/b/testfile1`" "2000-01-02 03:00:00.000000000 +0000"
    assertEquals "`stat -c%y  $SHUNIT_TMPDIR/b/testfile2`" "2010-02-03 06:10:12.000000000 +0000"
    assertEquals "`stat -c%y  $SHUNIT_TMPDIR/b/testfile3`" "2020-03-04 09:20:45.000000000 +0000"
    assertEquals "`stat -c%y  $SHUNIT_TMPDIR/b/testfile4`" "2030-04-05 12:30:32.000000000 +0100"
    assertEquals "`stat -c%y  $SHUNIT_TMPDIR/b/testfile5`" "2040-05-06 15:44:23.000000000 +0000"
    assertEquals "`stat -c%y  $SHUNIT_TMPDIR/b`" "1985-01-02 03:00:00.000000000 +0000"

}

testmultichecksum() {
    FILES=5
    RANKS=3
    for X in `seq 1 $FILES`  ; do
	dd if=/dev/urandom bs=1M count=1 of=$SHUNIT_TMPDIR/a/testfile$X > /dev/null 2>&1
    done    
    mpirun -n $RANKS $PCP -c  $SHUNIT_TMPDIR/a $SHUNIT_TMPDIR/b 
    assertEquals "pcp failed" 0 $?
    for X in `seq 1 $FILES` ; do
	cmp $SHUNIT_TMPDIR/a/testfile$X $SHUNIT_TMPDIR/b/testfile$X
	assertEquals "Checksum copy failed" 0 $?
    done
}

testmultichecksumchunk() {
    FILES=5
    RANKS=3
    for X in `seq 1 $FILES`  ; do
	dd if=/dev/urandom bs=1M count=10 of=$SHUNIT_TMPDIR/a/testfile$X > /dev/null 2>&1
    done    
    mpirun -n $RANKS $PCP -b 1 -c  $SHUNIT_TMPDIR/a $SHUNIT_TMPDIR/b 
    assertEquals "pcp failed" 0 $?
    for X in `seq 1 $FILES` ; do
	cmp $SHUNIT_TMPDIR/a/testfile$X $SHUNIT_TMPDIR/b/testfile$X
	assertEquals "Checksum copy failed" 0 $?
    done
}

    
. /usr/bin/shunit2
