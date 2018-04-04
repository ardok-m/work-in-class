#!/usr/bin/python

import numpy as np
import sys
from matplotlib import pyplot as plt
from matplotlib import cm
from matplotlib import colors


class Histograms():
    def __init__(self):
        self.fname = ''
        self.data = []
        self.histograms = []
        self.histograms_rf = []
        self.bins = []
        self.means = []
        self.sigmas = []
        self.correlations = []
        self.covariance = []

    def read_file(self, fname, header=True):
        """
        Read the file with the binned data.

        header = True or False. If True read extract bins from file header.
        """
        self.fname = fname

        self.data = np.loadtxt(fname, unpack=True)

        if header:
            with open(self.fname) as f:
                f.readline()
                header = f.readline()

            self.bins = map(float, header.strip('# ').split())

    def _compute_histograms(self, bins):
        """
        Compute the histograms of the data

        Output: [[hist, bin_edges], ...]
        """
        histograms = np.empty(len(self.data)).tolist()

        for i, data in enumerate(self.data):
            histograms[i] = np.histogram(data, bins=bins)  # histogram[i] = [hist, bin_edges]

        self.histograms = histograms

    def _reflect_histogram(self, histogram, center=0):
        """
        Reflex the histogram by its lowest X value.
        """

        x = histogram[1]
        y = histogram[0]

        x0 = min(x)

        x_rf = np.flip(2 * x0 - x[1:], axis=0)  # = x0 - (x - x0), x excluding x0

        y_rf = np.flip(y, axis=0)

        X = np.concatenate([x_rf, x])
        Y = np.concatenate([y_rf, y])

        if center == 0:
            X -= x0
        elif center:
            X += center - x0

        return [Y, X]

    def compute_means(self):
        """
        Compute the mean for each bin.
        """
        self.means = np.mean(self.data, axis=1)

    def compute_sigmas(self):
        """
        Compute the intervals that contains the 68% of the data around the means.
        """
        sigmas = np.empty(len(self.data)).tolist()

        for index, dataRaw in enumerate(self.data):
            data = dataRaw.copy()
            data.sort()
            mean = self.means[index]
            sigmaData = int(0.34*len(data) + 0.5)
            mean_index = np.abs(data-mean).argmin()
            try:
                sigma_up = data[mean_index + sigmaData] - mean
            except:
                sys.stderr.write("Upper 68% limmit not well defined for bin {}\n".format(index))
                if (mean_index + sigmaData - len(data)) == 0:
                    sys.stderr.write("Making an approximation\n")
                    sigma_up = data[mean_index + sigmaData - 1] - mean
                else:
                    sigma_up = np.nan
            try:
                sigma_down = data[mean_index - sigmaData] - mean
            except:
                sys.stderr.write("Lower 68% limmit not well defined for bin {}\n".format(index))
                if (mean_index - sigmaData) == -1:
                    sys.stderr.write("Making an approximation\n")
                    sigma_down = data[mean_index + sigmaData + 1] - mean
                else:
                    sigma_down = np.nan

            sigmas[index] = np.array([np.abs(sigma_down), sigma_up])  # Error are positive

        self.sigmas = sigmas

    def compute_correlations(self):
        """
        Compute all correlations between variables.
        """
        # TODO: Use symmetry to speed up the calc.

        if (self.covariance == []) or (np.nan in self.covariance):
            self.compute_covariance_matrix()

        c = np.diag(self.covariance)

        self.correlations = self.covariance / np.sqrt(c * c[:, None])

    def compute_covariance_matrix(self):
        """
        Compute the covariance matrix
        """
        self.covariance = np.cov(self.data)

    def compute_covariance_bin(self, zbin):
        """
        Compute <w(zbin)w_i> correlation values.
        """
        if self.means == []:
            self.compute_means()

        if self.covariance == []:
            self.covariance = [np.nan] * len(self.bins)

        wzbin_half = self.data[zbin] - self.means[zbin]

        self.covariance[zbin] = np.mean([wzbin_half*(w - w_mean) for w, w_mean
                                         in zip(self.data, self.means)], axis=1)

    def compute(self, bins='auto'):
        """
        Compute histograms
        """
        self._compute_histograms(bins)

    def reflect_histograms(self, center=0):
        """
        Reflex the stored histograms

        center = If True, center around min(xbin). If a number, center around
        that number.
        """
        for histogram in self.histograms:
            self.histograms_rf.append(self._reflect_histogram(histogram, center))

    def rebin_histograms_unit_variance(self):
        """
        Rebin histograms so that they have unit variance
        """
        for histogram_rf in self.histograms_rf:
            self.histograms_rf_rb.append(self._rebin_unit_variance(histogram_rf))

    def plot_histogram(self, index, variable_binned='bin_i', xlabel='x',
                       xlim=[None, None], outpath=''):
        """
        Plot histogram for bin with index, index
        """
        data = self.data[index].copy()
        data.sort()
        histogram = self.histograms[index]

        bins = histogram[1][:-1]
        density = histogram[0]/histogram[0].sum(dtype=float)

        plt.bar(bins, density, width=np.diff(histogram[1]), color='b', align='edge')
        plt.plot(bins + 0.5 * np.diff(histogram[1]), density, c='r')

        if self.means != []:
            mean = self.means[index]
            plt.axvline(mean, c='black', label='mean')
            if self.sigmas != []:
                sigma = self.sigmas[index]
                plt.axvspan(mean - sigma[0], mean + sigma[1], alpha=0.5, color='grey', label='68% data')

            plt.legend(loc=0)

        plt.xlim(xlim)
        plt.xlabel(xlabel)
        plt.ylabel('Normalized frequency')
        plt.title('{} = {}'.format(variable_binned, self.bins[index]))
        self._plt_close_figure(plt, outpath)

    def plot_evolution(self, xlabel='x', ylabel='y', scale=['linear', 'linear'],
                       outpath=''):
        """
        Plot evolution.
        """
        # TODO: Check error on shapes
        freq, y = zip(*self.histograms)
        prob = np.concatenate(np.array([row/np.sum(row, dtype=float) for row in freq]))
        y = np.array([row[:-1] for row in y])
        x = np.concatenate(np.array([self.bins[i]*np.ones(len(row)) for i, row in enumerate(y)]))
        y = np.concatenate(y)

        # TODO: Interpolate 0-prob values? Log scale removes them.
        cax = plt.scatter(x, y, c=prob, s=2, cmap=cm.hot_r, norm=colors.LogNorm())

        cb = plt.colorbar(cax)
        cb.set_label('% data')
        plt.ylabel(ylabel)
        plt.xlabel(xlabel)
        plt.xscale(scale[0])
        plt.yscale(scale[1])
        self._plt_close_figure(plt, outpath)

    def plot_correlation_matrix(self, xlabel='x_i', ylabel='y_i',
                                clabel='Correlation', outpath=''):
        """
        Plot the correlation matrix.
        """
        plt.imshow(self.correlations)
        cbar = plt.colorbar()

        plt.xticks(range(len(self.bins))[::50], self.bins[::50])
        plt.yticks(range(len(self.bins))[::50], self.bins[::50])

        cbar.set_label(clabel)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.title('Correlation matrix')

        self._plt_close_figure(plt, outpath)

    def _plt_close_figure(self, plt, outpath=''):
        """
        Show, save, if desired, and close figure.
        """

        if outpath:
            plt.savefig(outpath)

        plt.show()
        plt.close()

    def reset(self):
        """
        Reset the default values (erase everything)
        """
        self.__init__()