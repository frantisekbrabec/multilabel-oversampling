import numpy as np
import pandas as pd
from sklearn.utils import shuffle
import copy
import seaborn as sns
from tqdm import tqdm
import matplotlib.pyplot as plt
import random
import os
import math


def seed_everything(seed=1):
    """"
    Seed everything.
    """   
    random.seed(seed)
    np.random.seed(seed)

def create_fake_data(size=1, seed=1):
    seed_everything(seed)
    y1 = np.concatenate((np.ones(16*size), np.zeros(4*size))).astype(int)
    y2 = np.concatenate((np.ones(12*size), np.zeros(8*size))).astype(int)
    y3 = shuffle(np.concatenate((np.ones(4*size), np.zeros(16*size)))).astype(int)
    y4 = shuffle(np.concatenate((np.ones(4*size), np.zeros(16*size)))).astype(int)
    size = 20* size
    x = [f"img_{x}.jpg" for x in range(size)]
    df = pd.DataFrame({"y1": y1, "y2": y2, "y3": y3, "y4": y4, "x": x})
    return df

class MultilabelOversampler:
    
    def __init__(self, number_of_adds=1000, number_of_tries=100, tqdm_disable=False, details=False, plot=True):
        """

        
        Args:
            number_of_add: Maximum number of new rows add to df. Total number of iterations.
            number_of_tries: Maximum number of draws from df within total number of iterations.
            tqdm_disable: Enable progress bar for each iteration.
            details: Enable detailed feedback for each try
            plot: Plot all tries (iteration vs. std) after process is finished.
        """
        if number_of_adds:
            self.number_of_adds = number_of_adds
        else:
            self.number_of_adds = 1e6
        if number_of_tries:
            self.number_of_tries = number_of_tries
        else:
            self.number_of_tries = 1e6

        self.tqdm_disable = tqdm_disable
        self.details = details
        self.plot = plot
            

    def fit(self, df, target_list=["y1", "y2", "y3", "y4"]):
        """

        Args:
            df: Unbalanced DataFrame
            target_list: List of target variables. All other variables are treated as explanatory variables. 
        """
        self.reset()
        self.target_list = target_list
        self.df = copy.deepcopy(df)
        df_new = copy.deepcopy(df)
        res_std = []
        res_bad = []
        
        
        for iter_ in tqdm(range(self.number_of_adds),desc="Iteration", disable=self.tqdm_disable):
            current_std = df_new[self.target_list].sum().std()

            # Take random row and add to df_new
            not_working = []
            for try_ in tqdm(range(self.number_of_tries), desc=f"Iter {iter_}", disable=True):
                random_row = df.sample(n = 1)
                df_interim = pd.concat((df_new, random_row))
                new_std = df_interim[self.target_list].sum().std()
                # If std improves add row, otherwise add to not_working list
                if new_std < current_std:
                    df_new = df_interim
                    res_std.append(new_std)
                    if self.details:
                        print(f"Iter {iter_:3}: Worked after {try_:5} tries with row {random_row.index[0]:4}, Std: {current_std:.3f}, New: {new_std:.3f}, Shape: {df_new.shape}", flush=True)
                    break
                else:
                    not_working.append((random_row.index[0], new_std))
            if (try_+1) == self.number_of_tries:
                print(f"No improvement after {self.number_of_tries} tries in iter {iter_}.")
                break
            res_bad.append(not_working)
        #plt.plot(res_std)
        #plt.show()
        #df_new.sum().plot.bar()
        self.df_new = df_new
        self.res_std = res_std
        self.res_bad = res_bad
        if (len(res_std) > 0) and self.plot:
            plot_at = self.plot_all_tries(self.res_std, self.res_bad)
            plt.title("All tries per iteration with \n corresponding standard deviation")
            plt.show()
            return df_new, plot_at
        return df_new
    
    def reset(self):
        self.target_list = None
        self.df = None
        self.df_new = None
        self.res_std = None
        self.res_bad = None
        
    @staticmethod
    def plot_all_tries(res_std, res_bad):
        y_max = max([x[1] for x in res_bad[0]]) * 1.1
        plt.plot(res_std)
        plt.scatter(range(len(res_std)), res_std)
        plt.ylim(0, y_max)
        for i, row_std in enumerate(res_bad):
            for idx, (j, s) in enumerate(row_std):
                #plt.text(i + idx*0.02, s, f"{j}", fontsize=8)
                plt.scatter(i + idx*0.01, s)
        plt.xlabel('Iters')#, fontsize=18)
        plt.ylabel('Std')#, fontsize=16)
        return plt

    def plot_results(self):
        plt.subplot(2,2,1)
        self.plot_distr(self.df, "before")
        plt.subplot(2,2,2)
        self.plot_distr(self.df_new, "after")
        plt.subplot(2,2,(3,4)) # MatplotlibDeprecationWarning
        self.plot_index_counts(self.df_new)
        plt.tight_layout()
        plt.show()
        return plt

    def plot_distr(self, df, when):
        df[self.target_list].sum().plot.bar()
        plt.title(f"Label distribution \n{when} upsampling")
        return plt
    
    def plot_index_counts(self, df_new):
        """TODO make better xticks alignment"""
        idxs = list(df_new.index)
        lens = len(set(idxs))
        plt.hist(idxs, bins=lens,  width=.1)#, edgecolor='k')
        xint = range(min(idxs), math.ceil(max(idxs))+1)
        plt.xticks(xint)
        plt.title("Draws per index\n in new df")
        return plt
 
if __name__ == '__main__':
    df = create_fake_data(size=1, seed=3)
    print(df)
    mlo = MultilabelOversampler(number_of_adds=100)
    df_new = mlo.fit(df)
    mlo.plot_results()