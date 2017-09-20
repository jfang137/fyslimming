#!/usr/bin/python
# -*- coding: utf-8 -*-
import os,re

import sys, getopt

opts, args = getopt.getopt(sys.argv[1:], "hr:s:")
start_files = ['main.m',]
root_path =''
for op, value in opts:
    if op == "-r":
        root_path = value
    elif op == "-s":
        start_files = value.split(',')
        if start_files.count <= 0:
            start_files = ['main.m',]
    elif op == "-h":
        print('no params')
        sys.exit()

if root_path == '':
    print('no root path param')
    sys.exit()
    pass

class OCClass(object):
    """docstring for OCClass"""
    def __init__(self, name, file_name):
        super(OCClass, self).__init__()
        self.name = name
        self.file_name = file_name
        if file_name.endswith('.h'):
            self.h_file_name = file_name
            self.m_file_name = file_name.replace('.h','.m')
        else:
            self.m_file_name = file_name
            self.h_file_name = file_name.replace('.m','.h')
        self.isUsed = False

class FYFile(object):
    def __init__(self,path):
        self.path = path
        p = re.compile(r'\w+[\-\+]?\w*\.[hm]')
        self.name = re.search(p,path).group()

    def getRefListWithPath(self,path):
        text = open(path).read()
        p = re.compile(r'#import\s+\"\w+[\-\+]?\w*\.[hm]\"')
        tmp = re.findall(p,text)
        findlist = []
        for item in tmp:
            p = re.compile(r'\w+[\-\+]?\w*\.[hm]')
            rt = re.search(p,item).group()
            findlist.append(rt)
        self.isUsed = False
        self.refList = findlist

    def getPublicClasses(self):
        if self.name.endswith('.m'):
            return []
        text = open(self.path).read()
        p = re.compile(r'@interface\s+\w+\s*:')
        tmp = re.findall(p,text)
        public_class_list = []
        for item in tmp:
            p = re.compile(r'\s\w+')
            rt = re.search(p,item).group()
            c = OCClass(rt[1:],self.name)
            public_class_list.append(c)
        self.public_class_list = public_class_list
        return public_class_list;

def removecomment(text):
    p = re.compile(r'/\s*\*.*?\*\s*/|(?<![:/])//.*?\n',re.S) 
    newtext = re.sub(p,'\n',text)
    return newtext

fileList = []
def gci(filepath):
    files = os.listdir(filepath)
    for fi in files:
        fi_d = os.path.join(filepath,fi)            
        if os.path.isdir(fi_d):
            if not fi_d.endswith('Pods'):
                gci(fi_d)
        else:
            if fi_d.endswith('.h') or fi_d.endswith('.m') or fi_d.endswith('.mm') :
                f = FYFile(fi_d)
                f.getRefListWithPath(f.path)
                fileList.append(f)

gci(root_path)

def checkUsedBy(fileName):
    found = False
    for f in fileList:
        if f.name == fileName :
            found = True
            if f.isUsed == False : 
                f.isUsed = True
                for ref in f.refList:
                    checkUsedBy(ref)
            if '.h' in fileName:
                mName = fileName.replace('.h','.m')
                checkUsedBy(mName)
                mName = mName.replace('.m','.mm')
                checkUsedBy(mName)
            break

for s in start_files:
    checkUsedBy(s)
unusedCount = 0
referenced_list = []
class_list = []

print('-------------------')
print('files below are not referenced:')

for f in fileList:
    if f.isUsed == False:
        print(f.path)
        unusedCount += 1
    else:
        referenced_list.append(f)
        class_list += f.getPublicClasses()
print('total count:%d'%(unusedCount))
print('-------------------')

cached_file_dic = {}
def checkClassUsed(cls):
    isUsed = False
    for f in referenced_list:
        text = cached_file_dic.get(f.name)
        if text == None :
            text = open(f.path).read()
            text = removecomment(text)
            cached_file_dic[f.name] = text
        p = re.compile(r'@interface.*?@end|@implementation.*?@end',re.S)
        ioms = re.findall(p,text)

        for iom in ioms :

            p = re.compile(r'@\w+\s+(\w+)[\s\(:]')
            iom_name = re.match(p,iom).group(1)
            if iom_name == cls.name:
                continue
            elif cls.name in iom:
                isUsed = True
                break
    return isUsed

print('-------------------')
print('classes below are public classes not used in referenced files,searching!!!')
unusedCount = 0
for c in class_list:
    used = checkClassUsed(c)
    if used == False :
        unusedCount += 1
        print(c.name)
print('total count:%d'%unusedCount)
print('-------------------')

