#!/usr/bin/env python

from localconfig import *
from datetime import datetime
import sys, subprocess, os
import string as s

def check_output(command):
    return subprocess.Popen(command, stdout=subprocess.PIPE).communicate()[0]
    
if sys.argv[1] == '-c':
    try:
        cores = int(sys.argv[2])
    except:
        print 'Number of cores -c must be an integer number, %r is not. Default is %s.' % (sys.argv[2], cores) 
        sys.exit(1)
    del sys.argv[1:3]
    
if len(sys.argv) != 4:
    print sys.argv[0], '[-c n_cores] <hhblits db> <jackhmmer db> <sequence file>'
    sys.exit(0)

hhblitsdb = sys.argv[1]
jackhmmerdb = sys.argv[2]
seqfile = sys.argv[3]

rundir = seqfile.rfind('/')
if rundir < 0:
    rundir = '.'
else:
    rundir = seqfile[:rundir]

if not os.path.exists(hhblitsdb + '_a3m_db'):
    print hhblitsdb + '_a3m_db', 'does not exist'
    sys.exit(1)
if not os.path.exists(jackhmmerdb):
    print jackhmmerdb, 'does not exist'
    sys.exit(1)
if not os.path.exists(seqfile):
    print seqfile, 'does not exist'
    sys.exit(1)

f = open(seqfile).read()

if os.path.exists(seqfile + '.fasta'):
    subprocess.call(['mv', seqfile + '.fasta', seqfile +'.bak'])

f2 = open(seqfile +'.fasta', 'w')
if f[0] != '>':
    f2.write('>target\n' + f +'\n')
else:
    x = f.split('\n')
    if len(x[0]) > 6:
        target = x[0][1:5] + x[0][6]
    f2.write('>target\n' + "".join(x[1:]) + '\n')
f2.close()

names = ['E4', 'E0', 'E10', 'E40']
cutoffs = ['1e-4', '1', '1e-10', '1e-40']

jhpredictionnames = []
hhpredictionnames = []
failed = []

for i in range(4):
    if not os.path.exists(seqfile + '.jh' + names[i] + '.fas'):
        sys.stderr.write(str(datetime.now()) + ' jackhmmer ' + names[i] + ': generating alignment\nThis may take quite a few minutes!\n ')
        t = check_output([jackhmmer, '--cpu', str(cores), '-N', '5', '-E', cutoffs[i], '-A', seqfile +'.jh' + names[i] + '.ali', seqfile + '.fasta', jackhmmerdb])
        check_output([reformat, 'sto', 'fas', seqfile + '.jh' + names[i] + '.ali', seqfile + '.jh' + names[i] + '.fas'])
        check_output(['rm', seqfile + '.jh' + names[i] + '.ali'])

    if not os.path.exists(seqfile + '.jh' + names[i] + '.psicov'):
        t = check_output([trim, seqfile + '.jh' + names[i] + '.fas'])
        f = open(seqfile + '.jh' + names[i] + '.jones', 'w')
        f.write(t)
        f.close()

        t = ''
        sys.stderr.write(str(datetime.now()) + ' jackhmmer ' + names[i] + ': running PSICOV\nThis may take more than an hour.\n')
        if not os.path.exists(seqfile + '.jh' + names[i] + '.psicov'):
            try:
                t = check_output([psicov, seqfile + '.jh' + names[i] + '.jones'])
            except:
                t = ''
            f = open(seqfile + '.jh' + names[i] + '.psicov', 'w')
            f.write(t)
            f.close()

    jhpredictionnames.append(seqfile + '.jh' + names[i] + '.psicov')
    
    if not os.path.exists(seqfile + '.jh' + names[i] + '.plmdca'):
        t = check_output([trim2, seqfile + '.jh' + names[i] + '.fas'])
        f = open(seqfile + '.jh' + names[i] + '.trimmed', 'w')
        f.write(t)
        f.close()

        sys.stderr.write(str(datetime.now()) + ' jackhmmer ' + names[i] + ': running plmDCA\nThis may take more than an hour.\n')
        if plmdca:
            t = check_output([plmdca, seqfile + '.jh' + names[i] + ".trimmed", seqfile + '.jh' + names[i] + ".plmdca", "0.01", "0.01", "0.1", str(cores)])
        else:
            t = check_output([matlab, '-nodesktop', '-nosplash', '-r', "path(path, '" + scriptpath + "/plmDCA_symmetric_v2'); path(path, '" + scriptpath + "/plmDCA_symmetric_v2/functions'); path(path, '" + scriptpath + "/plmDCA_symmetric_v2/3rd_party_code/minFunc/'); plmDCA_symmetric ( '" + seqfile + '.jh' + names[i] + ".trimmed', '" + seqfile + '.jh' + names[i] + ".plmdca', 0.01, 0.01, 0.1, " + str(cores) + "); exit"])

    jhpredictionnames.append(seqfile + '.jh' + names[i] + '.plmdca')

    if not os.path.exists(seqfile + '.hh' + names[i] + '.fas'):
        sys.stderr.write(str(datetime.now()) + ' HHblits' + names[i] + ': generating alignment\nThis may take quite a few minutes!\n ')
        t = check_output([hhblits, '-all', '-oa3m', seqfile + '.hh' + names[i] + '.a3m', '-e', cutoffs[i], '-cpu', str(cores), '-i', seqfile + '.fasta', '-d', hhblitsdb])
        check_output([reformat, 'a3m', 'fas', seqfile + '.hh' + names[i] + '.a3m', seqfile + '.hh' + names[i] + '.fas'])
    
    if not os.path.exists(seqfile + '.hh' + names[i] + '.psicov'):
        t = check_output([trim, seqfile + '.hh' + names[i] + '.fas'])
        f = open(seqfile + '.hh' + names[i] + '.jones', 'w')
        f.write(t)
        f.close()
        
        sys.stderr.write(str(datetime.now()) + ' HHblits ' + names[i] + ': running PSICOV\nThis may take more than an hour.\n')
        t = ''
        if not os.path.exists(seqfile + '.hh' + names[i] + '.psicov'):
            try:
                t = check_output([psicov, seqfile + '.hh' + names[i] + '.jones'])
            except:
                t = ''
            f = open(seqfile + '.hh' + names[i] + '.psicov', 'w')
            f.write(t)
            f.close()

    hhpredictionnames.append(seqfile + '.hh' + names[i] + '.psicov')
    
    if not os.path.exists(seqfile + '.hh' + names[i] + '.plmdca'):
        t = check_output([trim2, seqfile + '.hh' + names[i] + '.fas'])
        f = open(seqfile + '.hh' + names[i] + '.trimmed', 'w')
        f.write(t)
        f.close()

        sys.stderr.write(str(datetime.now()) + ' HHblits ' + names[i] + ': running plmDCA\nThis may take more than an hour.\n')
        if plmdca:
            t = check_output([plmdca, seqfile + '.hh' + names[i] + ".trimmed", seqfile + '.hh' + names[i] + ".plmdca", "0.01", "0.01", "0.1", str(cores)])
        else:
            t = check_output([matlab, '-nodesktop', '-nosplash', '-r', "path(path, '" + scriptpath + "/plmDCA_symmetric_v2'); path(path, '" + scriptpath + "/plmDCA_symmetric_v2/functions'); path(path, '" + scriptpath + "/plmDCA_symmetric_v2/3rd_party_code/minFunc/'); plmDCA_symmetric ( '" + seqfile + '.hh' + names[i] + ".trimmed', '" + seqfile + '.hh' + names[i] + ".plmdca', 0.01, 0.01, 0.1, " + str(cores) + "); exit"])
    hhpredictionnames.append(seqfile + '.hh' + names[i] + '.plmdca')

sys.stderr.write("Predicting...\n")
l = [os.path.dirname(os.path.abspath(sys.argv[0])) + '/predict.py']
l.extend(jhpredictionnames)
l.extend(hhpredictionnames)
results = check_output(l)

print results
