import sys
import re
# from numpy.random import choice
import numpy as np
import os
from multiprocessing import Process, Manager, Pool
from random import random
import time

def rand(minimum, maximum):
    return minimum + (maximum - minimum) * random()

class Sparse:
	def __init__(self, dim, count, limit):
		self.dim = dim
		self.sparse = {}
		for i in range(count):
			self.sparse[int(rand(0, dim))] = rand(-limit, limit)
#dim = dimension of vector
#count = number of non-zero values
#limit = range of the non-zero values

	def value(self):
		a = []
		for i in range(self.dim):
			try:
				a.append(self.sparse[i])
			except:
				a.append(0)
		return a

def add(a, b, weight=1):
	c = a
	for i in b.sparse:
		try:
			c.sparse[i] += (weight * b.sparse[i])
		except:
			c.sparse[i] = (weight * b.sparse[i])
	return c



def cleanhtml(raw_html):
	cleanr = re.compile('<.*?>')
	cleantext = re.sub(cleanr, ' ', raw_html)
	return cleantext

class MySentences(object):
	def __init__(self, dirname):
		self.dirname = dirname

	def __iter__(self):
		punct = '!"#$%&\'()*+,.:;<=>?@[\\]^`{|}~'
		for root, dirs, files in os.walk(self.dirname):
			for filename in files:
				file_path = root + '/' + filename
				for line in open(file_path, encoding="utf-8"):
					sline = line.strip()
					if sline == "":
						continue
					if sline.startswith('<doc'):
						sline = 'title/resource/' + sline.split('title="')[1].split('">')[0].replace(' ', '_')
					rline = cleanhtml(sline)
					yield re.sub(r'[%s]' % punct, '', rline).lower().split()

#using numpy
# def randomVector(num):
#   q = 1./30
#   return choice([0, 1], size=num, p=[1 - q, q])

# generate sparse random vectors fast using time.time()

#using fastrand
# def randomVector(dim):
#   rv = np.zeros(dim)
#   for i in range(10):
#       rv[fastrand.pcg32bounded(dim)] = fastrand.pcg32bounded(5)
#   return rv

def generateEmbeddings(index, embeddings, sentence, title):
	dim = 500#vector dimens
	window = 2#window for context words
	count = 2#number of non-zero values
	limit = 5#range of non-zero values
	try:
		index[title]
	except:
		index[title] = Sparse(dim, count, limit)

	if len(sentence) >= window:
		for i in range(len(sentence) - window):
			if sentence[i].startswith("resource/"):
				#add index vector of title entity
				try:
					embeddings[sentence[i]] = add(embeddings[sentence[i]], index[title], 3)
				except:
					embeddings[sentence[i]] = Sparse(dim, 0, 1)
					embeddings[sentence[i]] = add(embeddings[sentence[i]], index[title], 3)

				#neighbouring words
				for j in range(int(i - window/2), i):#left context
					try:
						embeddings[sentence[i]] = add(embeddings[sentence[i]], index[sentence[j]])
					except:
						index[sentence[j]] = Sparse(dim, count, limit)
						embeddings[sentence[i]] = add(embeddings[sentence[i]], index[sentence[j]])
				for j in range(i + 1, int(i + (window/2) + 1)):#right context
					try:
						embeddings[sentence[i]] = add(embeddings[sentence[i]], index[sentence[j]])
					except:
						index[sentence[j]] = Sparse(dim, count, limit)
						embeddings[sentence[i]] = add(embeddings[sentence[i]], index[sentence[j]])

	# print("Processed ", str(wc), " words.", end="\r")
			# print(sentence[i] + '(' + str(embeddings[sentence[i]]) + ')')
			# print(sentence[i], end=' ')

if __name__ == '__main__':
	directory = sys.argv[1]
	sentences = MySentences(directory)
	manager = Manager()
	embeddings = manager.dict()
	index = manager.dict()
	wc = 0
	title = ''
	now = time.time()

	pool = Pool()
	for sentence in sentences:
		wc += len(sentence)
		if len(sentence) > 0 and sentence[0].startswith('title/'):
			title = sentence[0].split('title/')[1]
			print(sentence)
		else:
			pool.apply_async(generateEmbeddings, args=(index, embeddings, sentence, title))
	pool.close()
	pool.join()

	print("Processed ", str(wc), " words.")

	print("Time elapsed: ", str(time.time() - now), 's')

	embeddings = dict(embeddings)
	index = dict(index)

	with open('embeddings', 'w+', encoding="utf-8") as output:
		with open('labels', 'w+', encoding="utf-8") as op:
			for word in embeddings:
				# output.write(word + ' ==')
				op.write(word + '\n')
				for i in embeddings[word].value():
					output.write(' ' + str(i))
				output.write('\n')

	with open('index', 'w+', encoding="utf-8") as output:
		for word in index:
			output.write(word + ' ==')
			for i in index[word].value():
				output.write(' ' + str(int(i)))
			output.write('\n')
