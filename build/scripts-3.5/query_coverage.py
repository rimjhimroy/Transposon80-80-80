#!python

# Adapted  and improved for python3 by Rimjhim Roy Choudhury from https://github.com/jeevka/BLAST_Filter/blob/master/BLAST_Filter_Table.py by Jeevan Karloss

from __future__ import division
from collections import Counter
import sys
import os
import re
import operator
import argparse
from Bio import SeqIO



#################################################################
###################### SUB PROGRAMS #############################
#################################################################

# Store the coverage


def store_results_1(data, temp, RL):
    try:
        Cov = float((int(temp[7])-int(temp[6]))/RL[int(temp[0])])
    except:
        Cov = float((int(temp[7])-int(temp[6]))/RL[str(temp[0])])

    if temp[0] in data:
        if temp[1] in data[temp[0]]:
            data[temp[0]][temp[1]] += Cov
        else:
            data[temp[0]][temp[1]] = Cov
    else:
        data[temp[0]] = {}
        data[temp[0]][temp[1]] = Cov

    return data

# Store the Identity


def store_results_2(data, temp):
    if temp[0] in data:
        if temp[1] in data[temp[0]]:
            data[temp[0]][temp[1]] += float(temp[2])
            data[temp[0]][temp[1]] /= 2
        else:
            data[temp[0]][temp[1]] = float(temp[2])
    else:
        data[temp[0]] = {}
        data[temp[0]][temp[1]] = float(temp[2])

    return data


def store_results_3(data, temp):
    if temp[0] in data:
        if temp[1] in data[temp[0]]:
            data[temp[0]][temp[1]].append(str(temp[6]) + "-" + str(temp[7]))
        else:
            data[temp[0]][temp[1]] = [str(temp[6])+ "-" + str(temp[7])]
    else:
        data[temp[0]] = {}
        data[temp[0]][temp[1]] = [str(temp[6]) + "-" + str(temp[7])]

    return data


def store_identity(Ind_IDN, temp):
    if int(temp[6]) < int(temp[7]):
        qrange = temp[6] + "-" + temp[7]
    else:
        qrange = temp[7] + "-" + temp[6]

    if temp[0] in Ind_IDN:
        if temp[1] in Ind_IDN[temp[0]]:
            Ind_IDN[temp[0]][temp[1]][qrange] = float(temp[2])
        else:
            Ind_IDN[temp[0]][temp[1]] = {qrange: float(temp[2])}
    else:
        Ind_IDN[temp[0]] = {temp[1]: {qrange: float(temp[2])}}

    return Ind_IDN

##########################################################
# COMBINING ALL THE HITS TO CALCULATE THE OVERALL COVERAGE
##########################################################


def update_coverage(BAC_Range, AID, FID, Fos_Range, HT):
    HITS = []

    for i in range(len(BAC_Range)):
        temp1 = BAC_Range[i].split("-")

        ###########################################
        # Length of the hit must be >=100 basepairs
        ###########################################
        if (int(temp1[1]) - int(temp1[0])) >= HT or int(temp1[0]) - int(temp1[1]) >= HT:
            if int(temp1[1]) > int(temp1[0]):
                HITS = HITS + list(range(int(temp1[0]), int(temp1[1])))
            else:
                HITS = HITS + list(range(int(temp1[1]), int(temp1[0])))

    HITS1 = list(set(HITS))
    HITS1.sort()
    l2 = len(HITS1)

    # Since the hit size should be >=100bps, some hits may not have any results
    if l2 > 0:
        # STORE THE MAPPING RANGE
        if AID in Fos_Range:
            Fos_Range[AID][FID] = str(HITS1[0]) + "-" + str(HITS1[-1])
        else:
            Fos_Range[AID] = {}
            Fos_Range[AID][FID] = str(HITS1[0]) + "-" + str(HITS1[-1])

    return l2, Fos_Range


def update_coverage_Broken_Genes(BAC_Range, Fos_Range, RID, COV1, IDN, HL, Identity, QC, OF):
    HITS = []
    M = 0
    N = 0
    H = {}
    H1 = {}
    COV_Temp = {}

    for i in BAC_Range:
        HITS2 = []
        if IDN[RID][i] >= Identity:
            for j in range(len(BAC_Range[i])):
                temp1 = BAC_Range[i][j].split("-")

                if int(temp1[1]) > int(temp1[0]):
                    if int(temp1[1]) - int(temp1[0]) >= HL:
                        HITS = HITS + range(int(temp1[0]), int(temp1[1])+1)
                else:
                    if int(temp1[0]) - int(temp1[1]) >= HL:
                        HITS = HITS + range(int(temp1[1]), int(temp1[0])+1)

                if int(temp1[1]) > int(temp1[0]):
                    if int(temp1[1]) - int(temp1[0]) >= HL:
                        HITS2 = HITS2 + range(int(temp1[0]), int(temp1[1])+1)
                else:
                    if int(temp1[0]) - int(temp1[1]) >= HL:
                        HITS2 = HITS2 + range(int(temp1[1]), int(temp1[0])+1)

            CN = i.split("_")
            Chr_NO = CN[len(CN)-1]

            HITS1 = list(set(HITS2))
            HITS1.sort()
            l2 = len(HITS1)
            COVV = l2/RL[RID]

            COV_Temp[i] = COVV

            # Ex. H["unmapped"] = 0.098
            # Ex. H1["unmapped"] = [`jcf2355567331_0-656_unmapped`]

            if COVV != 0:
                if Chr_NO in H:
                    H[Chr_NO] += l2/RL[RID]
                    H1[Chr_NO].append(i)
                else:
                    H[Chr_NO] = l2/RL[RID]
                    H1[Chr_NO] = [i]

            M += IDN[RID][i]
            N += 1

    HITS1 = list(set(HITS))
    HITS1.sort()
    l2 = len(HITS1)

    CC = l2/RL[RID]

    ##########################################################
    # DECIDE THE TYPE OF THE HITS
    # CASE I: ONLY UNMAPPED, GAPEND, GAPSTART
    # CASE II: ONE CHR WITH UNMAPPED OR GAP START OR GAP END
    # CASE III: DIFFERENT CHR NUMBERS
    ##########################################################

    # Check for differnt chromosome numbers
    NDC = 0  # Number of different Chromosomes
    NNC = 0  # Number of NON-chromosomes
    for i in H:
        if re.search("ssa", i):
            NDC += 1
        else:
            NNC += 1

    # Check for CASE I
    if NDC == 0 and NNC >= 1:
        Type = "THREE"
    elif NDC == 1 and NNC >= 1:
        Type = "FOUR"
    elif NDC == 1 and NNC == 0:
        Type = "TWO"
    elif NDC > 1:
        Type = "FIVE"
    elif NDC == 0 and NNC == 1:
        Type = "TWO"

    ################################
    # PRINTING PART
    ################################
    Type = "TWO"
    for i in H1:
        for j in H1[i]:
            if CC*100 >= QC:
                # print Type,"\t",RID,"\t",j,"\t",IDN[RID][j],"\t",COV_Temp[j]*100,"\t",CC*100
                # txt = Type + "\t" + str(RID) + "\t" + j + "\t" + str(IDN[RID][j]) + "\t" + str(COV_Temp[j]*100) + "\t" + str(CC*100) + "\n"
                txt = str(RID) + "\t" + j + "\t" + \
                    str(IDN[RID][j]) + "\t" + \
                    str(COV_Temp[j]*100) + "\t" + "\n"
                OF.write(txt)

    return 0

# Procduces First outout file for overall plotting


def fix_overlapping_cov_1(COV, RANGE, RL, IDN, Identity, QC, HL, OF1):
    Fos_Range = {}
    Fos_Range_1 = {}
    N = 0
    for i in RANGE:
        N += 1
        COVV = 0
        M = 0
        for j in RANGE[i]:
            l, Fos_Range = update_coverage(RANGE[i][j], i, j, Fos_Range, HL)
            COV[i][j] = l/RL[i]

            # Check the coverage and identity
            if COV[i][j]*100 >= QC and IDN[i][j] >= Identity:
                # print "ONE\t", i,"\t",j,"\t",IDN[i][j],"\t",COV[i][j]*100,"\t",COV[i][j]*100
                # txt = "ONE\t" + i + "\t" + j  + "\t" + str(IDN[i][j]) + "\t" + str(COV[i][j]*100) + "\t" + str(COV[i][j]*100) + "\n"
                ID = float("{0:.2f}".format(IDN[i][j]))
                COCC = COV[i][j]*100
                COCC = float("{0:.2f}".format(COCC))
                txt = i + "\t" + j + "\t" + \
                    str(ID) + "\t" + str(COCC) + "\t" + "\n"
                OF1.write(txt)
                M = 1

            if COV[i][j] > COVV:
                COVV = COV[i][j]

        ##################################################################
        # Some of the RNA-Seqs are mapping to multiple scaffolds/contigs
        # without overlaps which may mean that these scaffolds/contigs can
        # be joined/put together after further analysis.
        # To list out the list of scaffolds/contigs which may be put together.
        ##################################################################

        # If the Maximum coverage of a RNA-Seq in any mapping scaffold/Contig
        # is less than 90% then check for mapping scaffolds/contigs of RNA-Seq
        # if COVV*100 < QC:

        # if M == 0:
        #	update_coverage_Broken_Genes(RANGE[i],Fos_Range_1,i,COVV,IDN,HL,Identity,QC,OF)

    return 0


def choose_idn_group(IDN):
    if IDN >= 98:
        G = ">=98%"
    elif IDN >= 95 and IDN < 98:
        G = "95-98%"
    elif IDN > 90 and IDN < 95:
        G = "91-94%"
    elif IDN >= 81 and IDN <= 90:
        G = "81-90%"
    else:
        G = "<=80%"

    return G


# Procduces second outout file for detail plotting
def fix_overlapping_cov_2(COV, RANGE, RL, IDN, Identity, QC, HL, OF2, Ind_IDN):
    Fos_Range = {}
    Fos_Range_1 = {}
    N = 0
    for i in RANGE:
        COVV = 0
        M = 0
        for j in RANGE[i]:
            l, Fos_Range = update_coverage(RANGE[i][j], i, j, Fos_Range, HL)
            COV[i][j] = l/RL[i]
            for k in RANGE[i][j]:
                N += 1
                temp = k.split("-")
                G = choose_idn_group(Ind_IDN[i][j][k])
                if COV[i][j]*100 >= QC and Ind_IDN[i][j][k] >= Identity:
                    COVT = float("{0:.2f}".format(COV[i][j]*100))
                    txt1 = i + "\t" + j + "\t" + str(Ind_IDN[i][j][k]) + "\t" + str(
                        COVT) + "\t" + temp[0] + "\t" + G + "\t" + str(RL[i]) + "\t" + str(N) + "\n"
                    txt2 = i + "\t" + j + "\t" + str(Ind_IDN[i][j][k]) + "\t" + str(
                        COVT) + "\t" + temp[1] + "\t" + G + "\t" + str(RL[i]) + "\t" + str(N) + "\n"
                    OF2.write(txt1)
                    OF2.write(txt2)

    return 0


################################################################
##################### MAIN PROGRAM #############################
################################################################
print()

# create variables that can be entered as arguments in command line
parser = argparse.ArgumentParser(
    description='This script takes a blast output file and Identity cuttoff%, Query coverage%, Minimum hit length in bps,')
parser.add_argument('-blout', type=str, metavar='blast_output',
                    required=True, help='REQUIRED: Full path to the blast output file')
parser.add_argument('-query', type=str, metavar='blast_query',
                    required=True, help='REQUIRED: Full path to query file')
parser.add_argument('-identity', type=float, metavar='identity_cutoff',
                    default=80, help='Minimum identity cutoff in %% (float) [80]')
parser.add_argument('-querycov', type=float, metavar='query_coverage_cutoff',
                    default=20, help='Minimum query coverage cutoff in %% (float) [20]')
parser.add_argument('-hitlength', type=int, metavar='hit_length',
                    default=80, help='Minimum hit length cutoff in bps [80]')
args = parser.parse_args()

# GO TO THE MAIN DATA
COV = {}
IDN = {}
Ind_IDN = {}
RANGE = {}
RL = {}

# Input BLAST OUTPUT File
In_File = args.blout
Identity = args.identity
Query_Coverage = args.querycov
Hit_Length = args.hitlength

# parse query fasta
my_query = SeqIO.index(args.query, "fasta")

# Open result files


outfile = os.path.splitext(args.blout)[0]+".filtered."+str(args.identity) + \
    "percIDN.out"
outf = open(outfile, "w+")

out1name = os.path.splitext(args.blout)[0]+".SignificantHits_"+str(args.identity)+"percIDN_"+str(
    args.querycov)+"percQuerycov_min"+str(args.hitlength)+"bpHitLen.txt"
out2name = os.path.splitext(args.blout)[0]+".plotting.txt"
output_file_1 = out1name
output_file_2 = out2name
OF1 = open(output_file_1, "w+")
OF2 = open(output_file_2, "w+")

txt = "Query_Seq\tSubject\tIdentity\tQuery_Coverage\n"
OF1.write(txt)


# BLAST OUTPUT FILES
with open(In_File) as infile:
    header=['query', 'subject', 'perc_identity','aln_length', 'mismatch', 'gapopen','qstart', 'qend','sstart', 'send', 'evalue', 'bitscore']
    outf.write('\t'.join(header[0:])+'\n')
    for i in infile:
	    temp = i.split()
	    if float(temp[2]) > args.identity:
		    records = temp
		    outf.write('\t'.join(map(str, records[0:])) + '\n')
		    
	    
	    # STORE QUERY LENGTH
	    RL[temp[0]] = len(my_query[temp[0]].seq)
	    # Store COV
	    COV = store_results_1(COV, temp, RL)
	    # STORE IDN
	    IDN = store_results_2(IDN, temp)
	    Ind_IDN = store_identity(Ind_IDN, temp)
	    # STORE RANGES
	    RANGE = store_results_3(RANGE, temp)
"""		
for i in Ind_IDN:
	for j in Ind_IDN[i]:
		print i,j,Ind_IDN[i][j]
sys.exit()
"""
##################################################################
# REMOVE OVERLAPPING and Calculate coverage
#################################################################
# COV,Fos_Range = fix_overlapping_cov(COV,RANGE,RL,IDN,Identity,Query_Coverage,Hit_Length,OF)

fix_overlapping_cov_1(COV, RANGE, RL, IDN, Identity,
                      Query_Coverage, Hit_Length, OF1)

fix_overlapping_cov_2(COV, RANGE, RL, IDN, Identity,
                      Query_Coverage, Hit_Length, OF2, Ind_IDN)

OF1.close()
OF2.close()
