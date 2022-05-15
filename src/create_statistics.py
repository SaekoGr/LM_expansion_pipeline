import os
import numpy as np
import matplotlib.pyplot as plt
import collections
import scipy.stats

stats_filename = "statistics_97fd5ea8e10e158c877c0648798e6c60.tsv"
stats_path = os.getcwd()
absolute_path = os.path.join(stats_path, "statistics_czech", stats_filename)

absolute_path = "/home/sabi/Desktop/LM_expansion_pipeline/src/graph_stats/CS/statistics_8450ffe6d017e16c334b77d13d1e798f.tsv"

def get_column(content, index):
    new_content = [line[index] for line in content]
    return new_content

def read_statistics_file(filepath):
    with open(filepath, 'r') as in_f:
        header = in_f.readline()
        content = in_f.readlines()
        content = [line.strip('\n').split('\t') for line in content]
        
    #print(content)
    return content, header


def plot_document_lengths(raw_len, clean_len, bins=50):
    plt.figure(figsize=(6, 4))
    plt.title("Full document vs. clean document length")
    plt.xlabel('Length of document')
    plt.ylabel('Number of documents')
    plt.style.use('seaborn-deep')
    plt.xlim(0,max(raw_len))
    plt.hist([raw_len, clean_len], bins=bins, label=['Raw length','Clean length'])
    plt.legend(loc='upper right')
    plt.show()
    full_raw = np.sum(raw_len)
    full_clean = np.sum(clean_len)
    total_gain = full_clean / full_raw * 100
    print("Total gain is ", str(total_gain))
    
def plot_links_per_term(terms_dict, bins=20):
    just_occurances = np.array(list(terms_dict.values()), dtype=np.int16)
    plt.figure(figsize=(6, 4))
    plt.title("Number of links obtained")
    plt.xlabel('Number of links')
    plt.ylabel('Number of terms')
    plt.style.use('seaborn-deep')
    plt.xlim(0,max(just_occurances))
    plt.hist([just_occurances], bins=bins, label=['#link for each term'])
    plt.legend(loc='upper right')
    plt.show()
    
def assess_occurance(data, bins=50):
    plt.figure(figsize=(6, 4))
    plt.title("Number of links obtained")
    plt.xlabel('Number of links')
    plt.ylabel('Number of terms')
    plt.style.use('seaborn-deep')
    #ticks = np.arange(0, max(data), 100)
    plt.hist([data], bins=bins)
    #plt.xticks(ticks)
    plt.legend(loc='upper right')
    plt.show()
    
    occurances = collections.Counter(data)
    hit_rate = occurances["YES"] / (occurances['YES'] + occurances['NO']) * 100
    print("LANG ID hit rate " + str(hit_rate))


def gaussian_mle(data):                                                                                                                                                                               
    mu = data.mean(axis=0)                                                                                                                                                                            
    var = np.sqrt(data.var(axis=0))
    return mu, var  


def graph_terms_gain(content, bins=50):
    print("GAIN GRAPH")
    trigrams = get_column(content, 0)
    raw_lens = get_column(content, 5)
    
    values = list(zip(trigrams, raw_lens))
    val_dict = {}
    #print(values)
    print(len(trigrams))
    print(len(raw_lens))
    
    for x,_ in values:
        val_dict[x] = 0
        
    for x,y in values:
        if int(y) > 0:
            val_dict[x] = val_dict[x] + 1
            
    obtained_data = list(val_dict.values())
    #obtained_data.sort()
    print(obtained_data)
    #print(len(obtained_data))
    
    plt.style.use('seaborn-deep')
    
    plt.figure(figsize=(6, 4))
    mu, var = gaussian_mle(np.array(obtained_data))
    print(mu, var)
    x_axis = np.linspace(0, 50, 1000)
    y_axis = scipy.stats.norm.pdf(x_axis, mu, var)
    #plt.xlim(0,30)
    #plt.ylim(0,1)
    
    
    plt.title("Number of relevant documents per term")
    plt.hist([obtained_data], bins=bins, density=True)
    plt.plot(x_axis, y_axis,color='m')
    plt.ylabel('Frequency')
    plt.xlabel('Number of obtained documents')
    #plt.xticks(ticks)
    #plt.legend(loc='upper right')
    plt.show()

all_data, header = read_statistics_file(absolute_path)
print(header)

raw_len = np.array(get_column(all_data, 2), dtype=np.int16)
clean_len = np.array(get_column(all_data, 5), dtype=np.int16)
#plot_document_lengths(raw_len, clean_len)

ngrams = collections.Counter(get_column(all_data,0))
#plot_links_per_term(ngrams)

lang_id = get_column(all_data, 3)
#assess_occurance(lang_id,2)

ppl = np.array(get_column(all_data, 4), dtype=np.float128)
#print(ppl)
#assess_occurance(ppl)
graph_terms_gain(all_data)
