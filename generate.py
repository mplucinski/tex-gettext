#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import logging
import os
import os.path
import re
import sqlite3
import subprocess
import sys
import time
import translator

VERSION='0.1'

logging.basicConfig(level=logging.DEBUG)

def generate(input, languages=None):
	document = translator.Document.load(input)
	translations = [translator.Translation(input, 'en_US')]+translator.find_translations(input, languages=languages.split(',') if languages else None)
	changed = False
	for i in translations:
		if i.update(document):
			changed = True

	if changed:
		sys.stderr.write('Some translations has changed. Please update them and restart the process\n')
		sys.exit(1)

	outputs = []
	for i in translations:
		i = i.translate(document)
		outputs.append(i.generate())

	for i in outputs:
		subprocess.check_call(['xdg-open', i])

def main():
	parser = argparse.ArgumentParser(description='Documents internationalization tool (version {})'.format(VERSION))
	parser.add_argument('--input', action='store',
		help='Name of input file (default: input.tex)', default='input.tex')
	parser.add_argument('--languages', action='store',
		help='List of language codes for which outputs will be generated.'+
		'Default list is built from names of found translation files', default=None)
	args = parser.parse_args()
	generate(input=args.input, languages=args.languages)

if __name__ == '__main__':
	main()

