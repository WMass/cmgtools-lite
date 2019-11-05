import ROOT, os, re
from array import array
ROOT.gROOT.SetBatch(True)

if __name__ == "__main__":

    from optparse import OptionParser
    parser = OptionParser(usage='%prog dirwithtrees [options] ')
    parser.add_option('-c','--channel', dest='channel', default='el', type='string', help='el or mu')
    parser.add_option('-o','--outdir', dest='outdir', default='.', type='string', help='outdput directory to save the plots')
    parser.add_option('-s','--selection', dest='selection', default='trigger', type='string', help='type of selection: trigger or selection')
    (options, args) = parser.parse_args()
    
    if len(args)<1:
        raise RuntimeError, "Need a directory with T&P trees as argument."

    indir = args[0]

    chain = ROOT.TChain("IDIsoToHLT/fitter_tree")
    for ds in os.listdir(indir):
        if not re.match('{seltype}TnP\S+\.root'.format(seltype=options.selection),ds): continue
        chain.Add('{indir}/{fname}'.format(indir=indir,fname=ds))

    ptbinsize = 1.5
    if options.channel=='el':
        minpt=30
        nptbins=10
        etabins = [-2.5 + 0.1*i for i in xrange(10)]
        etabins+= [-1.566,-1.4442]
        etabins+= [-1.4 + 0.1*i for i in xrange(15)]
        etabins+= [-eta for eta in reversed(etabins[:-1])]
    else:
        minpt=25
        nptbins=14
        etabins = [-2.4 + 0.1*i for i in xrange(49)]
    maxpt=60 # just not to have boundary issues at least on the higher end

    ptbins = [minpt+1.5*i for i in xrange(nptbins+1)]

    # cuts
    fiducial = 'probe_lep_pt>{minpt} && probe_lep_truept>{minpt} && probe_lep_pt<{maxpt} && probe_lep_truept<{maxpt} && probe_lep_matchMC'.format(minpt=minpt,maxpt=maxpt)
    if options.channel=='el':
        fiducial += ' && abs(probe_lep_trueeta)<2.5 && (abs(probe_lep_eta)<1.566 || (abs(probe_lep_eta)>1.4442)) && (abs(probe_lep_trueeta)<1.566 || (abs(probe_lep_trueeta)>1.4442))'
        if options.selection=='trigger':
            dencut = '{fiducial} && probe_lep_hltSafeId && probe_lep_customId && probe_lep_tightCharge'.format(fiducial=fiducial)
            numcut = dencut + ' && probe_eleTrgPt>0'
        else:
            dencut = '{fiducial} && probe_eleTrgPt>0 && probe_lep_matchMC'.format(fiducial=fiducial)
            numcut = dencut + ' && probe_lep_hltSafeId && probe_lep_customId && probe_lep_tightCharge'
    else:
        fiducial += ' && abs(probe_lep_trueeta)<2.4'
        if options.selection=='trigger':
            dencut = '{fiducial} && probe_lep_fullLepId>0.5'.format(fiducial=fiducial)
            numcut = dencut + ' && (probe_muTrgPt  > 0 || probe_tkMuTrgPt > 0)'
        else:
            dencut = '{fiducial} && (probe_muTrgPt  > 0 || probe_tkMuTrgPt > 0) && probe_lep_matchMC'.format(fiducial=fiducial)
            numcut = dencut + ' && probe_lep_fullLepId > 0.5'

    print "DENOMINATOR CUT = ",dencut
    print "NUMERATOR CUT = ",numcut

    effMapReco_den = ROOT.TH2D('effMapReco_den','',len(etabins)-1,array('d',etabins),len(ptbins)-1,array('d',ptbins))
    effMapReco_den.Sumw2()
    effMapReco_den.SetContour(100)
    effMapReco_num = effMapReco_den.Clone('effMapReco_num')
    effMapTrue_den = effMapReco_den.Clone('effMapTrue_den')
    effMapTrue_num = effMapReco_den.Clone('effMapTrue_num')
 
    chain.Draw('probe_lep_pt:probe_lep_eta>>effMapReco_den',dencut)
    chain.Draw('probe_lep_pt:probe_lep_eta>>effMapReco_num',numcut)
    chain.Draw('probe_lep_truept:probe_lep_trueeta>>effMapTrue_den',dencut)
    chain.Draw('probe_lep_truept:probe_lep_trueeta>>effMapTrue_num',numcut)

    effMapReco_num.Divide(effMapReco_den)
    effMapTrue_num.Divide(effMapTrue_den)
    effMapReco_num.GetZaxis().SetRangeUser(0.4,1.0)
    effMapTrue_num.GetZaxis().SetRangeUser(0.4,1.0)
    effRatio = effMapReco_num.Clone('effRatio')
    effRatio.Divide(effMapTrue_num)
    effRatio.GetZaxis().SetRangeUser(0.95,1.05)

    effPull = effMapReco_num.Clone('effRatio')
    effPull.GetZaxis().SetRangeUser(-3.,3.)
    effPull1D = ROOT.TH1D('effPull1D','',70,-3.,3.)
    for xb in xrange(len(etabins)-1):
        for yb in xrange(len(ptbins)-1):
            val = (effMapReco_num.GetBinContent(xb+1,yb+1)-effMapTrue_num.GetBinContent(xb+1,yb+1))/effMapReco_num.GetBinError(xb+1,yb+1) if effMapReco_num.GetBinError(xb+1,yb+1)>0 else 0
            effPull.SetBinContent(xb+1,yb+1,val)
            effPull1D.Fill(val if val else -999)

    histos = {'effreco' : effMapReco_num,
              'efftrue' : effMapTrue_num,
              'effratio': effRatio,
              'effpull' : effPull,
              'effpull1D': effPull1D}

    ROOT.gStyle.SetOptStat(0)
    ROOT.gStyle.SetPalette(ROOT.kLightTemperature)
    canv = ROOT.TCanvas('canv','',800,600)
    for k,v in histos.iteritems():
        if  v.InheritsFrom('TH2'):
            gopt = 'colz0'
            v.GetXaxis().SetTitle('#eta')
            v.GetYaxis().SetTitle('p_{T} (GeV)')
            v.SetContour(100)
        else:
            gopt = 'hist'
            v.GetXaxis().SetTitle('(#epsilon_{recobin}-#epsilon_{truebin})/#sigma_{#epsilon}')
        v.Draw(gopt)
        for ext in ['pdf', 'png']:
            canv.SaveAs('{od}/{name}_{sel}_{ch}.{ext}'.format(od=options.outdir,name=k,sel=options.selection,ch=options.channel,ext=ext))
    
