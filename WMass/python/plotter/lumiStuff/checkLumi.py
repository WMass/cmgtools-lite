#!/usr/bin/env python  

from shutil import copyfile
import re, sys, os, os.path, subprocess, json, ROOT
import numpy as np
import argparse

from runPerEra import runsForEra as rfe

parser = argparse.ArgumentParser()
args = parser.parse_args()

inputfile = "lumiStuff/runlumi.csv" # copied from /afs/cern.ch/user/b/bendavid/cmspublic/runlumi.csv

eras = list(rfe.keys())
lumiPerEra = {era : 0.0 for era in eras}

with open(inputfile) as f:
    for line in f:
        run,lumi = line.strip().split(',')
        run = int(run)
        lumi = float(lumi)
        #print(f"{run} -> {lumi}")
        for era in eras:
            if run in rfe[era]:
                lumiPerEra[era] += lumi
                break # if run was found, no need to check following eras

for era,intlumi in iter(lumiPerEra.items()):
    print(f"{era} : {intlumi}")
