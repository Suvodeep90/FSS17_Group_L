import sys
#sys.stdout = open('output.txt', 'w')
sys.path.insert(0, '../part2')
import tbl
import math
import random
import statistics
import numpy

################ Unsupervised Discretization #####################

def ranges(table, colIndex):
    indep_values = get_values(table, colIndex)
    col = table.cols["all"][colIndex]
    sd = statistics.stdev(indep_values)
    indep_values.sort()
    unsup_bins = make_bins(indep_values, sd)
    return unsup_bins

# Expects already sorted list
def make_bins(numList, sd):

    # Initalize bin variables
    n = len(numList)
    epsilon = 0.2*statistics.stdev(numList)
    print("Epsilon: " + str(epsilon))
    minBinSize = round(math.sqrt(n))
    numInitBins = math.floor(n/minBinSize) #total number of initial bins
    print(str(numInitBins) + " Num of Bins\n" + str(minBinSize) +  " Min bin size\n")

    #(1) >=minBinsize
    #(2) ranges differ by epsilon
    #(3) span of range > epsilon
    #(4) low is greater than hi of prev range

    # Create bins (1) that are >= minBinSize
    bins = []
    cur_pos = 0
    for i in range(1, numInitBins+1):
            start = cur_pos
            end = cur_pos + minBinSize -1 #inclusive
            bin_dict = {}
            bin_dict['low'] = numList[start]
            bin_dict['high'] = numList[end]
            bin_dict['span'] = bin_dict['high'] - bin_dict['low']
            bin_dict['n'] = minBinSize
            # in case there are fewer elements than minBinsSize at the end
            # add it to the last bin
            if(i == numInitBins and end < n-1):
                bin_dict['high'] = numList[n-1]
                bin_dict['span'] = bin_dict['high'] - bin_dict['low']
                bin_dict['n'] = minBinSize + ((n-1)-end)
            bins.append(bin_dict)
            cur_pos = cur_pos + minBinSize

    # Traverses bins and combines bins if they match conditionFunc
    def combine_bins(conditionFunc):
        i = 0
        while i < len(bins):
            if len(bins) <= 1:
                break
            if i == len(bins)-1:
                while conditionFunc(bins[i-1], bins[i]):
                    merge_bins(i-1, 1)
                    i -= 1 # If you've deleted the last, now look at what you just merged into
            else:
                while conditionFunc(bins[i], bins[i+1]):
                    merge_bins(i, i+1)
            i += 1

    # Merge second bin into the first bin
    def merge_bins(i1, i2):
        bin1, bin2 = bins[i1], bins[i2]
        bin1['high'] = bin2['high']
        bin1['span'] = bin2['high'] - bin1['low']
        bin1['n'] = bin1['n'] + bin2['n']
        del bins[i2]

    # Print bins before checks
    for bin_dict in bins:
        print(bin_dict)

    #(2)?
            
    # (3) Combine bins if the span is less than some epsilon
    combine_bins(lambda b, placeholder: b['span'] < epsilon )

    # (4) Combine bins if the span is less than some epsilon
    combine_bins(lambda b1, b2: b2['low'] < b1['high'] )

    # Print bins after checks
    print("\n--- After combining ---")
    for bin_dict in bins:
        print(bin_dict)

        
################ Supervised Discretization #####################

def super_ranges(table, colIndex, depIndex):
    indep_values = get_values(table, colIndex)
    sd = table.cols["all"][colIndex].sd
    if depIndex == "dom":
        dep_values = table.doms
    else:   
        dep_values = get_values(table, depIndex)
    comb_list = list(zip(indep_values,dep_values))
    unsup_ranges = make_bins(comb_list, sd)

    breaks = [] # Array of the splits to keep
    range_indeces = list(unsup_ranges.keys())
    x =  numpy.array(comb_list)

    def combine(lo, hi, comb_list):
        #print("Looking from " + str(lo) + " to " + str(hi))
        x =  numpy.array(comb_list)
        best = statistics.stdev(x[:,1])
        cut = None
        cut_location = None
        n = len(comb_list)
        # for each split:
        # - Get values to the left and right of split
        # - Calculate expected value of the split
        # - If split is better so far, set best and cut
        i = 0
        for j in range(lo, hi):
            #print("--- Looking at spliting after range " + str(j))
            cur_bin_size = unsup_ranges[j]["n"]
            l = comb_list[0:i+cur_bin_size]
            l = numpy.array(l)
            l = l[:,1]
            r = comb_list[i+cur_bin_size:]
            r = numpy.array(r)
            r = r[:,1]
            i += cur_bin_size
            exp_val = (len(l)/n)*statistics.stdev(l) + (len(r)/n)*statistics.stdev(r)
            if exp_val < best:
                cut = j
                cut_location = i
                best = exp_val
        #print("Found best cut: " + str(cut) + "\n")

        # Recurse!
        if cut is not None:
            combine(lo,cut,comb_list[0:cut_location])
            combine(cut+1,hi,comb_list[cut_location:])
        else:
            breaks.append(hi)

    combine(range_indeces[0], range_indeces[len(range_indeces)-1], comb_list)
    super_ranges = create_supers(unsup_ranges, breaks)
    printDictionary(super_ranges)
    return super_ranges
    

# Pass the ranges and indeces of ranges you want to break at the top of
def create_supers(unsup_ranges, splits):
    super_ranges = {}
    i = 1
    for key, u_range in unsup_ranges.items():
        if key in splits:
            super_ranges[i] = {"label":i, "most":u_range["high"]}
            i += 1
    return super_ranges


################ Helpers #####################
# delete none value keys
def cleanDict(dict):
    clean_dict = {}
    i = 1
    for key, val in dict.items():
        if(val is not None):
            clean_dict[i] = val
            i += 1
    return clean_dict
#print the dictionary
def printDictionary(dict):
    for key,value in dict.items():
        print(str(key) + ": " + str(value))
    return

# return a list of random numbers
# the size of the list = count, range for numbers = [0,1]
# Comment out seed: random.seed(5)
def randomList(count):
    numList = []
    for x in range(0, count):
        numList.append(random.random())
    return numList

def get_values(table, colIndex):
    values = []
    for r in table.rows:
        row = table.rows[r]
        value = row.cells[colIndex]
        if value is not None:
            values.append(value)
    return values


################ Run #####################
# Create table
table = tbl.Tbl();
table.update({0:"$someNumeric"})
randomValues = randomList(50)
for val in randomValues:
    r = 2*random.random()/100
    #print(r)
    if val < .2:
        y = .2 + r
    elif val < .6:
        y = .6 + r
    else:
        y = .9 + r
    #print(val,y)
    row = {0:val,1:y}
    table.update(row)

# Print table
#for i, col in table.cols["all"].items():
#col.summarize()


# Run dicretizers
print("\n================ UNSUPERVISED BINS ================")
ranges(table, 0)
#print("\n================ SUPERVISED BINS ==================")
#super_ranges(table, 0, 1)
