#encoding:utf-8
"""
Author : Gaopengfei
Date: 2017.3
OutputFormat:
    dict(
        key = (ID, database)
        value = list(Tonset positions)
    )
"""
import os
import sys
import json
import math
import pickle
import random
import pywt
import time
import glob
import pdb
from multiprocessing import Pool

import numpy as np
from sklearn.ensemble import RandomForestClassifier
import matplotlib
import matplotlib.pyplot as plt
from numpy import pi, r_
from scipy import optimize
import Tkinter
import tkMessageBox

curfilepath =  os.path.realpath(__file__)
curfolderpath = os.path.dirname(curfilepath)
# my project components
from mcmc.post_p import post_p_mcmc



debugmod = True

class PwavePicker:
    def __init__(self):

        tableau20 = [(31, 119, 180), (174, 199, 232), (255, 127, 14), (255, 187, 120),    
             (44, 160, 44), (152, 223, 138), (214, 39, 40), (255, 152, 150),    
             (148, 103, 189), (197, 176, 213), (140, 86, 75), (196, 156, 148),    
             (227, 119, 194), (247, 182, 210), (127, 127, 127), (199, 199, 199),    
             (188, 189, 34), (219, 219, 141), (23, 190, 207), (158, 218, 229)]
        self.colors = []
        for color_tri in tableau20:
            self.colors.append((color_tri[0]/255.0,color_tri[1]/255.0,color_tri[2]/255.0))



    def pick(self, raw_sig, start_index = 0):
        fig = plt.figure(1)

        rect = 0.1,0.1,0.8,0.8
        ax = fig.add_axes(rect)
        ax.grid(color=(0.8,0.8,0.8), linestyle='--', linewidth=2)
        ax.set_title('Please Press space to refresh')
        browser = PointBrowser(raw_sig, fig, ax, start_index)

        fig.canvas.mpl_connect('pick_event', browser.onpick)
        fig.canvas.mpl_connect('key_press_event', browser.onpress)

        plt.show()

class PointBrowser(object):
    """
    Click on a point to select and highlight it -- the data that
    generated the point will be shown in the lower axes.  Use the 'n'
    and 'p' keys to browse through the next and previous points
    """


    def __init__(self, raw_sig, fig, ax, start_index):
        self.fig = fig
        self.ax = ax
        self.SaveFolder = os.path.join(curfolderpath, 'results')


        self.text = self.ax.text(0.05, 0.95, 'selected: none',
                            transform=self.ax.transAxes, va='top')
        # ============================
        self.recInd = start_index
        self.recname = ''
        self.rawSig = raw_sig
        self.expLabels = None

        tableau20 = [(31, 119, 180), (174, 199, 232), (255, 127, 14), (255, 187, 120),    
             (44, 160, 44), (152, 223, 138), (214, 39, 40), (255, 152, 150),    
             (148, 103, 189), (197, 176, 213), (140, 86, 75), (196, 156, 148),    
             (227, 119, 194), (247, 182, 210), (127, 127, 127), (199, 199, 199),    
             (188, 189, 34), (219, 219, 141), (23, 190, 207), (158, 218, 229)]
        self.colors = []
        for color_tri in tableau20:
            self.colors.append((color_tri[0]/255.0,color_tri[1]/255.0,color_tri[2]/255.0))
        # ===========================
        # Mark list
        self.poslist = []
        self.totalWhiteCount = 0

    def onpress(self, event):
        if event.key not in ('n', 'p',' ','x','a','d'):
            return

        if event.key == 'n':
            # Finishing marking
            annots = PwaveBroadcast(self.rawSig, self.poslist, 500)
            annots = post_p_mcmc(self.rawSig, annots, 500)
            self.expLabels = annots
            # clear Marker List
            self.reDraw()
            return None
        elif event.key == ' ':
            self.reDraw()
            
            return None
        elif event.key == 'x':
            # Delete markers in stack
            if len(self.poslist) > 0:
                del self.poslist[-1]

        elif event.key == 'a':
            step = -200
            xlims = self.ax.get_xlim()
            new_xlims = [xlims[0]+step,xlims[1]+step]
            self.ax.set_xlim(new_xlims)
        elif event.key == 'd':
            step = 200
            xlims = self.ax.get_xlim()
            new_xlims = [xlims[0]+step,xlims[1]+step]
            self.ax.set_xlim(new_xlims)
        else:
            pass

        self.update()
    def saveWhiteMarkList2Json(self):
        with open(os.path.join(self.SaveFolder,'{}_poslist.json'.format(self.recname)),'w') as fout:
            result_info = dict(
                    ID = self.recname,
                    database = 'QTdb',
                    poslist = self.poslist,
                    type = 'Tonset')
            json.dump(result_info, fout, indent = 4, sort_keys = True)
            print 'Json file for record {} saved.'.format(self.recname)

    def clearWhiteMarkList(self):
        self.poslist = []
        self.totalWhiteCount = 0
        

    def addMarkx(self,x):
        # mark data
        pos = int(x)
        self.poslist.append(pos)

        self.ax.plot(pos, self.rawSig[pos],
                marker = 'x',
                color = self.colors[7],
                markersize = 22,
                markeredgewidth = 4,
                alpha = 0.9,
                label = 'Tonset')
        self.ax.set_xlim(pos - 500, pos + 500)

        
    def onpick(self, event):
        '''Mouse click to mark target points.'''
        # The click locations
        x = event.mouseevent.xdata
        y = event.mouseevent.ydata

        # add white Mark
        self.addMarkx(x)
        self.text.set_text('Marking Tonset: ({}) [whiteCnt {}]'.format(self.poslist[-1],len(self.poslist)))

        # update canvas
        self.fig.canvas.draw()

    def RepeatCheck(self):
        '''Check repeat results.'''
        result_file_name = os.path.join(self.SaveFolder,'{}_poslist.json'.format(self.recname))
        if os.path.exists(result_file_name):
            window = Tkinter.Tk()
            window.wm_withdraw()
            tkMessageBox.showinfo(title = 'Repeat', message = 'The record %s is already marked!' % self.recname)
            window.destroy()

            # Go to next record
            self.next_record()
            self.clearWhiteMarkList()
            self.reDraw()
        
        
    def reDraw(self):

        self.RepeatCheck()

        ax = self.ax
        ax.cla()

        self.text = self.ax.text(0.05, 0.95, 'selected: none',
                            transform=self.ax.transAxes, va='top')
        ax.grid(color=(0.8,0.8,0.8), linestyle='--', linewidth=2)

        # ====================================
        # load ECG signal

        ax.set_title('QT {} (Index = {})'.format(self.recname,self.recInd))
        ax.plot(self.rawSig, picker=5)  # 5 points tolerance
        # plot Expert Labels
        if self.expLabels is not None:
            self.plotExpertLabels(ax)

        # draw Markers
        for pos in self.poslist:
            # draw markers
            self.ax.plot(pos, self.rawSig[pos],
                    marker = 'x',
                    color = self.colors[7],
                    markersize = 22,
                    markeredgewidth = 4,
                    alpha = 0.9,
                    label = 'Tonset')

        self.ax.set_xlim(0, len(self.rawSig))
        # update draw
        self.fig.canvas.draw()

    def update(self):
        #self.ax2.text(0.05, 0.9, 'mu=%1.3f\nsigma=%1.3f' % (xs[dataind], ys[dataind]),
                 #transform=self.ax2.transAxes, va='top')
        #self.ax2.set_ylim(-0.5, 1.5)

        self.fig.canvas.draw()

    def next_record(self):
        self.recInd += 1
        self.recname = ''
        return True

    def plotExpertLabels(self,ax):

        #get label Dict
        labelSet = set()
        labelDict = dict()
        for pos,label in self.expLabels:
            if label in labelSet:
                labelDict[label].append(pos)
            else:
                labelSet.add(label)
                labelDict[label] = [pos,]

        # plot to axes
        for label,posList in labelDict.iteritems():
            # plot marker for current label
            if label[0]=='T':
                color = self.colors[4]
            elif label[0]=='P':
                color  = self.colors[5]
            elif label[0]=='R':
                color  = self.colors[6]
            # marker
            if 'onset' in label:
                marker = '<'
            elif 'offset' in label:
                marker = '>'
            else:
                marker = 'o'
            ax.plot(posList,map(lambda x:self.rawSig[x],posList),marker = marker,color = color,linestyle = 'none',markersize = 14,label = label)
        ax.legend(numpoints = 1)

def PwaveBroadcast(raw_sig, pwave_poslist, fs):
    '''
        Input: 
            raw_sig:ECG
            pwave_poslist: (ponset, p, poffset) index
        Output:
            annots with R, Ponset, P and Poffset
    '''

    from dpi.DPI_QRS_Detector import DPI_QRS_Detector as DPI
    dpi = DPI(debug_info = dict())
    r_list = dpi.QRS_Detection(raw_sig, fs = fs)
    r_list.sort()

    Rpos = None
    for rpos in r_list:
        if rpos > pwave_poslist[2]:
            Rpos = rpos
            break

    if Rpos is None:
        raise Exception('No QRS is found behind labeled P wave!')
    annots = zip(r_list, ['R',] * len(r_list))
    for rpos in r_list:
        ponset = rpos - Rpos + pwave_poslist[0]
        p = rpos - Rpos + pwave_poslist[1]
        poffset = rpos - Rpos + pwave_poslist[2]

        if ponset >= 0 and ponset < len(raw_sig):
            annots.append([ponset, 'Ponset'])
        if p >= 0 and p < len(raw_sig):
            annots.append([p, 'P'])
        if poffset >= 0 and poffset < len(raw_sig):
            annots.append([poffset, 'Poffset'])
    return annots
    



def get_QTdb_recordname(index = 1):
    QTdb = QTloader()
    reclist = QTdb.getQTrecnamelist()
    return reclist[index]

def test1():
    '''Testing with changgeng data.'''
    from randomwalk.changgengLoader import ECGLoader as cLoader
    loader = cLoader(1, 1)
    sig = loader.loadID('2259')
        
    tool = PwavePicker()
    tool.pick(sig, start_index = 0)
    pass


if __name__ == '__main__':
    test1()
