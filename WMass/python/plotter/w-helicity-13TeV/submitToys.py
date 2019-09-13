#!/bin/env python

# usage: python submitToys.py cards_el/Wel_card_withXsecMask.hdf5 10000 -n 20 --outdir output -q 8nh
#
# python w-helicity-13TeV/submitToys.py cards/diffXsec_2018_06_29_group10_absGenEta_moreEtaPtBin/Wel_plus_card_withXsecMask.meta 11000 -n 2 --outdir toys/diffXsec_2018_06_29_group10_absGenEta_moreEtaPtBin_newGenXsec/ -t 1 -q cmscaf1nd
#
# python w-helicity-13TeV/submitToys.py cards/diffXsec_mu_2018_11_24_group10_onlyBkg/Wmu_card_withXsecMask_sparse_outBkgNorm3p8_noSyst.hdf5 11000 -n 5 -t 1 -r 24 --outdir toys/diffXsec_mu_2018_11_24_group10_onlyBkg_noSyst/


jobstring  = '''#!/bin/sh
ulimit -c 0 -S
ulimit -c 0 -H
set -e
cd CMSSWBASE
export SCRAM_ARCH=slc6_amd64_gcc530
eval `scramv1 runtime -sh`
cd OUTDIR
COMBINESTRING

'''


jobstring_tf = '''#!/bin/sh
ulimit -c 0 -S
ulimit -c 0 -H
set -e
export SCRAM_ARCH=slc6_amd64_gcc700
cd CMSSWBASE
eval `scramv1 runtime -sh`
cd OUTDIR
COMBINESTRING

'''

def makeCondorFile(jobdir, srcFiles, options, logdir, errdir, outdirCondor):
    dummy_exec = open(jobdir+'/dummy_exec.sh','w')
    dummy_exec.write('#!/bin/bash\n')
    dummy_exec.write('bash $*\n')
    dummy_exec.close()
     
    condor_file_name = jobdir+'/condor_submit.condor'
    condor_file = open(condor_file_name,'w')
    condor_file.write('''Universe = vanilla
Executable = {de}
use_x509userproxy = $ENV(X509_USER_PROXY)
Log        = {ld}/$(ProcId).log
Output     = {od}/$(ProcId).out
Error      = {ed}/$(ProcId).error
getenv      = True
next_job_start_delay = 1
environment = "LS_SUBCWD={here}"
+MaxRuntime = {rt}\n
'''.format(de=os.path.abspath(dummy_exec.name), ld=os.path.abspath(logdir), od=os.path.abspath(outdirCondor),ed=os.path.abspath(errdir),
           rt=int(options.runtime*3600), here=os.environ['PWD'] ) )
    if os.environ['USER'] in ['mdunser', 'psilva']:
        condor_file.write('+AccountingGroup = "group_u_CMST3.all"\n\n\n')
    if options.nThreads:
        condor_file.write('request_cpus = {nt} \n\n'.format(nt=options.nThreads))
    for sf in srcFiles:
        condor_file.write('arguments = {sf} \nqueue 1 \n\n'.format(sf=os.path.abspath(sf)))
    condor_file.close()
    return condor_file_name


import ROOT, random, array, os, sys

if __name__ == "__main__":
    
    from optparse import OptionParser
    parser = OptionParser(usage='%prog file.hdf5 ntoys [prefix] [options] ')
    parser.add_option('-n'  , '--ntoy-per-job'  , dest='nTj'           , type=int           , default=None , help='split jobs with ntoys per batch job')
    parser.add_option('-t'  , '--threads'       , dest='nThreads'      , type=int           , default=None , help='use nThreads in the fit (suggested 2 for single charge, 1 for combination)')
    parser.add_option(        '--dry-run'       , dest='dryRun'        , action='store_true', default=False, help='Do not run the job, only print the command');
    parser.add_option('-r'  , '--runtime'       , default=8            , type=int                          , help='New runtime for condor resubmission in hours. default None: will take the original one.');
    parser.add_option(        '--bbb'           , dest='binByBin'      , action='store_true', default=False, help='Use the bin by bin uncertainties to incorporate the templates MC stat');
    parser.add_option('--outdir', dest='outdir', type="string", default=None, help='outdirectory');
    parser.add_option("","--binByBinStat", default=False, action='store_true', help="add bin-by-bin statistical uncertainties on templates (using Barlow and Beeston 'lite' method")
    parser.add_option("","--correlateXsecStat", default=False, action='store_true', help="Assume that cross sections in masked channels are correlated with expected values in templates (ie computed from the same MC events)")
    (options, args) = parser.parse_args()

    ## for tensorflow the ws has to be the .hdf5 file made from the datacard with text2hdf5.py!
    
    workspace = args[0]; 
    wsbase = os.path.basename(workspace).split('.')[0]
    ntoys = int(args[1])
    prefix = args[2] if len(args)>2 else wsbase
    charge = 'plus' if 'plus' in wsbase else 'minus'
    fixPOIs = 'XsecMask' not in workspace

    print "Submitting {nt} toys with workspace {ws} and prefix {pfx}...".format(nt=ntoys,ws=workspace,pfx=prefix)

    absopath  = os.path.abspath(options.outdir)
    if not options.outdir:
        raise RuntimeError, 'ERROR: give at least an output directory. there will be a HUGE number of jobs!'
    else:
        if not os.path.isdir(absopath):
            print 'making a directory and running in it'
            os.system('mkdir -p {od}'.format(od=absopath))

    if options.correlateXsecStat and not options.binByBinStat:
        raise RuntimeError, 'ERROR: --correlateXsecStat makes sense only with --binByBinStat!'

    if options.binByBin:
        if options.correlateXsecStat or options.binByBinStat:
            raise RuntimeError, '--bbb cannot be used with --binByBinStat or --correlateXsecStat. The first is equivalent to calling both the second ones'

    jobdir = absopath+'/jobs/'
    if not os.path.isdir(jobdir):
        os.system('mkdir {od}'.format(od=jobdir))
    logdir = absopath+'/logs/'
    if not os.path.isdir(logdir):
        os.system('mkdir {od}'.format(od=logdir))
    errdir = absopath+'/errs/'
    if not os.path.isdir(errdir):
        os.system('mkdir {od}'.format(od=errdir))
    outdirCondor = absopath+'/outs/'
    if not os.path.isdir(outdirCondor):
        os.system('mkdir {od}'.format(od=outdirCondor))
        
    random.seed()

    srcfiles = []
    for j in xrange(int(ntoys/int(options.nTj))):
        ## make new file for evert parameter and point
        job_file_name = jobdir+'/job_{j}_toy{n:.0f}To{nn:.0f}.sh'.format(j=j,n=j*int(options.nTj),nn=(j+1)*int(options.nTj))
        log_file_name = logdir+'/job_{j}_toy{n:.0f}To{nn:.0f}.log'.format(j=j,n=j*int(options.nTj),nn=(j+1)*int(options.nTj))
        tmp_file = open(job_file_name, 'w')

        tmp_filecont = jobstring_tf
        cmd = 'combinetf.py -t {n} --seed {j}{jn} {dc} '.format(n=int(options.nTj),dc=os.path.abspath(workspace),j=j*int(options.nTj)+1,jn=(j+1)*int(options.nTj)+1)        
        if fixPOIs: cmd += ' --POIMode none '
        else:  cmd += ' --doSmoothnessTest '
        if options.binByBinStat : 
            cmd += ' --binByBinStat '
            if options.correlateXsecStat: cmd += ' --correlateXsecStat '  # make sense only with --binByBinStat
        if options.binByBin: cmd += ' --binByBinStat --correlateXsecStat '
        if options.nThreads: 
            cmd += ' --nThreads {nt}'.format(nt=options.nThreads) 
        tmp_filecont = tmp_filecont.replace('COMBINESTRING', cmd)
        tmp_filecont = tmp_filecont.replace('CMSSWBASE', os.environ['CMSSW_BASE']+'/src/')
        tmp_filecont = tmp_filecont.replace('OUTDIR', absopath+'/')
        tmp_file.write(tmp_filecont)
        tmp_file.close()
        srcfiles.append(job_file_name)
    cf = makeCondorFile(jobdir,srcfiles,options, logdir, errdir, outdirCondor)
    subcmd = 'condor_submit {rf} '.format(rf = cf)

    print subcmd

    sys.exit()

