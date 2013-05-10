import csv
import os
from math import sqrt
import matplotlib.pyplot as plt
import numpy as np
import sys

class Experiment(object):
    def __init__(self, name, headers):
        self.name = name
        self.headers = headers
        self.trials = 0
        self.results =[]
        self.avg = []
        self.stdev = []
        self.stderr = []

    def add_result(self, row, column, result):
        while row >= len(self.results):
            self.results.append([[]])
        while column >= len(self.results[row]):
            self.results[row].append([])
        self.results[row][column].append(result)
        if len(self.results[row][column]) > self.trials:
            self.trials = len(self.results[row][column])

    def tally(self):
        for row in self.results:
            self.avg.append([])
            self.stdev.append([])
            self.stderr.append([])
            for cell in row:
                self.avg[-1].append(sum(cell) / len(cell))
                self.stdev[-1].append(sqrt(sum([(x - self.avg[-1][-1])**2 for x in cell]) / (len(cell) - 1)))
                self.stderr[-1].append(self.stdev[-1][-1] / sqrt(len(cell)))

    def get_statistic(self, column):
        stat_avg = [row[column] for row in self.avg]
        stat_stdev = [row[column] for row in self.stdev]
        stat_stderr = [row[column] for row in self.stderr]
        return (stat_avg, stat_stdev, stat_stderr)

def initialize_results(filename):
    f = open(filename, 'r')
    reader = csv.reader(f)
    initial_results = []
    reader.next()
    for row in reader:
        initial_results.append([[] for _ in range(len(row))])
    f.close()
    return initial_results


def get_headers(filename):
    tempf = open(filename, 'r')
    reader = csv.reader(tempf)
    headers = reader.next()
    tempf.close()
    return headers

def write_results(filename, r):
    f = open(filename, 'wb')
    writer = csv.writer(f)
    for row in r:
        writer.writerow(row)
    f.flush()
    f.close()

def aggregate_results(experiment_name, experiment_subtitle):
    data_dir = sys.argv[1]
    results_dir = sys.argv[2]
    if not data_dir.endswith('/'):
        data_dir += '/'
    if not results_dir.endswith('/'):
        results_dir += '/'
    experiments = {}
    for filename in os.listdir(data_dir):
        tokens = filename.replace(".csv", "").split('_')
        series_name = ""
        for i in range(len(tokens) - 1):
            if i > 0:
                series_name += " "
            series_name += tokens[i]
        if series_name not in experiments:
            headers = get_headers(data_dir + filename)
            experiments[series_name] = Experiment(series_name, headers)
        experiment = experiments[series_name]
        filename = data_dir + filename
        f = open(filename, 'r')
        try:
            reader = csv.reader(f)
            reader.next()
        except:
            print filename
            continue
        for i,row in enumerate(reader):
            for j,val in enumerate(row):
                experiment.add_result(i,j,float(val))
        f.close()
    for experiment in experiments.values():
        experiment.tally()
        trials = experiment.trials
    stats = { }
    for name,experiment in experiments.iteritems():
        for i in range(1,len(experiment.headers)):
            stat_name = experiment.headers[i]
            if stat_name not in stats:
                stats[stat_name] = { }
            stats[stat_name][name] = experiment.get_statistic(i)
    for stat_name,stat in stats.iteritems():
        files = [open(results_dir + stat_name.lower() + '_avg.csv', 'wb'), open(results_dir + stat_name.lower() + '_stdev.csv', 'wb'), open(results_dir + stat_name.lower() + '_stderr.csv', 'wb')]
        writer = [csv.writer(f) for f in files]
        metrics = [[],[],[]]
        headers = ['Hands']
        for experiment,vals in stat.iteritems():
            headers.append(experiment)
            for metric,rows in enumerate(metrics):
                for iteration,val in enumerate(vals[metric]):
                    while iteration >= len(rows):
                        rows.append([len(rows)])
                    rows[iteration].append(val)
        for metric,rows in enumerate(metrics):
            writer[metric].writerow(headers)
            for row in rows:
                writer[metric].writerow(row)
            files[metric].flush()
            files[metric].close()
        avg = [np.array(stat[experiment][0]) for experiment in headers[1:]]
        stdev = [np.array(stat[experiment][1]) for experiment in headers[1:]]
        stderr = [np.array(stat[experiment][2]) for experiment in headers[1:]]
        plot(results_dir, experiment_name, experiment_subtitle, stat_name, avg, stdev, stderr, trials, headers)

def transpose_results(results):
    t = [[] for _ in range(len(results[0]))]
    for row in results:
        for i,cell in enumerate(row):
            t[i].append(cell)
    return t
    
def plot(results_dir, experiment_name, experiment_subtitle, stat_name, avg, stdev, stderr, trials, series):
    #avg = [np.array(x) for x in transpose_results(avg)]
    #stdev = [np.array(x) for x in transpose_results(stdev)]
    #stderr = [np.array(x) for x in transpose_results(stderr)]
    colors = ['red','blue','yellow', 'green', 'orange', 'purple', 'brown'] # max 7 lines
    ax = plt.subplot(111)
    for i in range(len(avg)):
        xvals = [hand for hand in range(1,len(avg[i])+1)]
        plt.xlim([0,len(xvals)])
        # Plot each series
        plt.plot(xvals, avg[i], label=series[i+1].replace(' ','\n'), color=colors[i])
        plt.fill_between(xvals, avg[i] + stderr[i], avg[i] - stderr[i], facecolor=colors[i], alpha=0.2)
    plt.xlabel(series[0])
    plt.ylabel(stat_name)
    #plt.ylim([0,1])
    plt.title('{0}\n({1}, {2} trials)'.format(experiment_name, experiment_subtitle, trials))
    # Shink current axis by 25%
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.75, box.height])
    # Put a legend to the right of the current axis
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.savefig('{0}{1}.pdf'.format(results_dir, stat_name.lower()))
    plt.clf()
        
        
        
        
if len(sys.argv) != 5:
    print "Format: python plot_results.py data_dir results_dir experiment_name experiment_subtitle"
    exit(1)
print "Plotting {0}".format(sys.argv[1])
aggregate_results(experiment_name=sys.argv[3],experiment_subtitle=sys.argv[4])
