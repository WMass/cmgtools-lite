import ROOT, optparse, os


if __name__ == '__main__':
    parser = optparse.OptionParser(usage='usage: %prog [opts] ', version='%prog 1.0')
    parser.add_option('', '--config' , type='string'       , default=''    , help='config file with location of fitresults files')
    parser.add_option('', '--outdir' , type='string'       , default=''    , help='output directory with directory structure and plots')
    parser.add_option('', '--runtoys', action='store_true' , default=False , help='run also toys, not only hessian. takes longer')
    (options, args) = parser.parse_args()


    ## this loads the path for all the results in a config
    results = {}
    execfile(options.config, results)

    ## make the output directory first
    os.system('mkdir -p {od}'.format(od=options.outdir))

    ## get the channel from the filename of the config.txt
    muEl = 'mu' if 'mu' in options.config else 'el'

    ## check if running also toys
    toysHessian = ['hessian']
    if options.runtoys:
        toysHessian += ['toys']

    ## diff nuisances
    ## ================================
    print 'running diffNuisances'
    tmp_outdir = options.outdir+'/diffNuisances/'
    os.system('mkdir -p {od}'.format(od=tmp_outdir))
    os.system('cp ~mdunser/public/index.php {od}'.format(od=tmp_outdir))
    
    ## make diff Nuisance plots for pdf and other nuisances
    for t in toysHessian:
        for nuis in ['pdf', 'muR,muF,muRmuF,wpt', 'CMS_']:
            diffNuisances_cmd = 'python w-helicity-13TeV/diffNuisances.py --outdir {od} --pois {p}'.format(od=tmp_outdir, p=nuis)
            os.system('{cmd} --infile {inf} --suffix floatingPOIs_{t} --type {t} '.format(cmd=diffNuisances_cmd, inf=results['both_floatingPOIs_'+t], t=t))
            os.system('{cmd} --infile {inf} --suffix fixedPOIs_{t}    --type {t} '.format(cmd=diffNuisances_cmd, inf=results['both_fixedPOIs_'+t]   , t=t))
    
    ## plot syst ratios
    ## ================================
    print 'running systRatios for a few things'
    tmp_outdir = options.outdir+'/systRatios/'
    os.system('mkdir -p {od}'.format(od=tmp_outdir))
    os.system('cp ~mdunser/public/index.php {od}'.format(od=tmp_outdir))
    for nuis in ['pdf', 'muR,muF,muRmuF,alphaS,wpt']:
        os.system('python w-helicity-13TeV/systRatios.py --outdir {od} -s {p} {d} {ch}'.format(od=tmp_outdir, p=nuis, d=results['basedir'], ch=muEl))
    
    ## plot correlation matrices
    ## ================================
    print 'making correlation matrices'
    tmp_outdir = options.outdir+'/correlationMatrices/'
    os.system('mkdir -p {od}'.format(od=tmp_outdir))
    os.system('cp ~mdunser/public/index.php {od}'.format(od=tmp_outdir))
    for t in toysHessian:
        for nuis in ['pdf', 'muR,muF,muRmuF,alphaS,wpt', 'CMS_']:
            os.system('python w-helicity-13TeV/subMatrix.py {inf} --outdir {od} --params {p} --type {t} --suffix floatingPOIs_{t} '.format(od=tmp_outdir, t=t, p=nuis, inf=results['both_floatingPOIs_'+t]))
            os.system('python w-helicity-13TeV/subMatrix.py {inf} --outdir {od} --params {p} --type {t} --suffix fixedPOIs_{t} '   .format(od=tmp_outdir, t=t, p=nuis, inf=results['both_fixedPOIs_'+t]))

    ## plot rapidity spectra
    ## ================================
    print 'plotting rapidity spectra'
    tmp_outdir = options.outdir+'/rapiditySpectra/'
    os.system('mkdir -p {od}'.format(od=tmp_outdir))
    os.system('cp ~mdunser/public/index.php {od}'.format(od=tmp_outdir))
    for t in toysHessian:
        cmd  = 'python w-helicity-13TeV/plotYW.py '
        cmd += ' -C plus,minus --xsecfiles {xp},{xm} '.format(xp=results['xsecs_plus'],xm=results['xsecs_minus'])
        cmd +=  '--infile {inf} --outdir {od} --type {t} --suffix floatingPOIs_{t} '.format(od=tmp_outdir, t=t, inf=results['both_floatingPOIs_'+t])
        os.system(cmd)
    
