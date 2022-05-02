import os
import numpy as np
import matplotlib.pyplot as plt
import collections

stats_filename = "statistics_97fd5ea8e10e158c877c0648798e6c60.tsv"
stats_path = os.getcwd()
absolute_path = os.path.join(stats_path, "statistics_czech", stats_filename)


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


all_data, header = read_statistics_file(absolute_path)
print(header)

raw_len = np.array(get_column(all_data, 2), dtype=np.int16)
clean_len = np.array(get_column(all_data, 5), dtype=np.int16)
plot_document_lengths(raw_len, clean_len)

ngrams = collections.Counter(get_column(all_data,0))
plot_links_per_term(ngrams)

lang_id = get_column(all_data, 3)
assess_occurance(lang_id,2)

ppl = np.array(get_column(all_data, 4), dtype=np.float128)
print(ppl)
assess_occurance(ppl)
