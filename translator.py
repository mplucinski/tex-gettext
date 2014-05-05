#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import icu
import locale
import os
import re
import shutil
import subprocess
import sys
import tex_math
import tzlocal
import unittest

RE_PO_FILE = re.compile(r'.*\.(.*)\.po$')
DEFAULT_PLURAL = 'nplurals=2; plural=n != 1'

class Tag:
	class Argument:
		def __init__(self, content, begin_pos, end_pos):
			self.content = content
			self.begin_pos = begin_pos
			self.end_pos = end_pos

		def __hash__(self):
			return hash(self.content)

		def __eq__(self, other):
			return isinstance(other, Tag.Argument) and self.content == other.content

		def __str__(self):
			return self.content

	def __init__(self, name, args, begin_pos, end_pos):
		self.name = name
		self.args = args
		self.begin_pos = begin_pos
		self.end_pos = end_pos

	def __eq__(self, other):
		return isinstance(other, Tag) and self.name == other.name and self.args == other.args

	def __hash__(self):
		return hash(self.name)+sum([hash(i) for i in self.args])

	def __str__(self):
		return self.name+''.join(['{'+str(i)+'}' for i in self.args])

class Document:
	@staticmethod
	def load(file):
		return Document(file)

	def __init__(self, name):
		self.name = name

	def __str__(self):
		return self.name

	def generate(self):
		root, _ = os.path.splitext(self.name)
		output = root+'.pdf'
		subprocess.check_call(['xelatex', self.name])
		return output

	def find_tags(self, tag, nargs=1):
		with open(self.name) as file:
			doc = file.read()
			texts = list()
			pos = 0

			def _find_matching_closing(i):
				depth = 0
				while True:
					pc = doc[i-1] if i-1 > 0 else None
					c = doc[i]
					if c == '{' and pc != '\\':
						depth += 1
					elif c == '}' and pc != '\\':
						depth -= 1
					if depth == 0:
						break
					i += 1
				return i

			while True:
				i = doc.find(tag, pos)
				if i < 0:
					break
				args = []
				start_tag = i
				end = start = pos = start_tag+len(tag)
				for n in range(nargs):
					try:
						end = _find_matching_closing(start)
					except Exception as e:
						raise Exception('Could not find end for tag that starts at {pos} character ({text})'.format(pos=start, text=(doc[max(start-20, 0):start]+' --> '+doc[start:min(start+20, len(doc))])))
					start += 1 #skip initial '{'
					args.append(Tag.Argument(doc[start:end], start, end))
					start = doc.find('{', end)
				texts.append(Tag(tag, args, start_tag, end))
			return texts

class Translation:
	ALLOW_NOT_EXISTING = 1

	TAG_MSGID = 'msgid'
	TAG_MSGID_PLURAL = 'msgid_plural'
	TAG_MSGSTR = 'msgstr'
	TAG_MSGCTXT = 'msgctxt'

	@staticmethod
	def load(input_file, file, flags=0):
		_, name = os.path.split(file)
		name = RE_PO_FILE.match(name)
		if not flags & Translation.ALLOW_NOT_EXISTING:
			if not os.path.exists(file):
				raise Exception('File "{}" does not exists'.format(file))
		return Translation(input_file, name.group(1), file)

	def __init__(self, input, locale, file=None):
		self.input = input
		self.locale = locale
		self.file = file
		self._parsed = None
		self._icu_locale = icu.Locale.createFromName(self.locale)
		self._icu_date_full = icu.DateFormat.createDateInstance(icu.DateFormat.FULL, self._icu_locale)

	def __repr__(self):
		return 'Translation(input={input}, locale={locale}, file={file})'.format(
			input=self.input, locale=self.locale, file=self.file
		)

	def update(self, document):
		if not self.file:
			return False #nothing to update
		template_name = self.generate_template(document)
		sys.stderr.write('Updating translation {}...\n'.format(self))
		if not os.path.exists(self.file):
			sys.stderr.write('Generating new translation file: {}...\n'.format(self.file))
			subprocess.check_call(['msginit', '-i', template_name,
					'-l', self.locale, '-o', self.file])
			return True
		with open(self.file, 'rb') as f:
			old = f.read()
		sys.stderr.write('Merging template into translation file: {}...\n'.format(self.file))
		new = subprocess.check_output(['msgmerge', self.file, template_name])
		with open(self.file, 'wb') as f:
			f.write(new)
		return old != new

	def translate(self, document):
		sys.stderr.write('Translating {} to {}...\n'.format(document, self))
		tags = self.find_all_tags(document)
		tags += document.find_tags('\\today', 0)
		tags += document.find_tags('\\formatdate', 3)
		tags = sorted(tags, key=lambda x: x.begin_pos)
		translated, ext = os.path.splitext(self.input)
		translated += '.' + self.locale + ext
		with open(document.name) as input_file:
			doc = input_file.read()
			sys.stderr.write('Generating file {}...\n'.format(translated))
			with open(translated, 'w') as output:
				elems = []
				prev = 0
				for i in tags:
					elems.append(doc[prev:i.begin_pos])
					elems.append(self.translate_tag(i))
					prev = i.end_pos+1
				elems.append(doc[prev:])
				output.write(''.join(elems))
		return Document.load(translated)

	def find_all_tags(self, document):
		tags = []
		tags += document.find_tags('\\gettext')
		tags += document.find_tags('\\pgettext', 2)
		tags += document.find_tags('\\ngettext', 3)
		return tags

	def generate_template(self, document):
		with open(document.name) as doc:
			doc = doc.read()
			tags = self.find_all_tags(document)
			tags = set(tags)
			tags = sorted(tags, key=lambda x: x.begin_pos)
			template_name, _ = os.path.splitext(document.name)
			template_name = template_name+'.pot'
			sys.stderr.write('Generating template "{}"...\n'.format(template_name))
			with open(template_name, 'w') as template:
				template.write('msgid ""\n')
				template.write('msgstr ""\n')
				#template.write('"Project-Id-Version: PACKAGE VERSION\\n"\n')
				#template.write('"Report-Msgid-Bugs-To: \\n"\n')
				##template.write('"POT-Creation-Date:   2014-05-03 22:18+0200\\n"\n')
				#time = datetime.datetime.now(tz=tzlocal.get_localzone())
				#time = time.strftime('%Y-%m-%d %H:%M%z')
				#template.write('"POT-Creation-Date: {}\\n"\n'.format(time))
				#template.write('"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n"\n')
				template.write('"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n"\n')
				#template.write('"Language-Team: LANGUAGE <LL@li.org>\\n"\n')
				template.write('"Language: \\n"\n')
				template.write('"MIME-Version: 1.0\\n"\n')
				template.write('"Content-Type: text/plain; charset=UTF-8\\n"\n')
				template.write('"Content-Transfer-Encoding: 8bit\\n"\n')
				template.write('"Plural-Forms: nplurals=INTEGER; plural=EXPRESSION;\\n"\n')
				template.write('\n')
				for tag in tags:
					def escape(s):
						return s.replace('\\', '\\\\').replace('\n', '"\n"')
					if tag.name == '\\gettext':
						template.write('{} "{}"\n'.format(self.TAG_MSGID, escape(tag.args[0].content)))
						template.write('{} ""\n'.format(self.TAG_MSGSTR))
					elif tag.name == '\\ngettext':
						template.write('{} "{}"\n'.format(self.TAG_MSGID, escape(tag.args[0].content)))
						template.write('{} "{}"\n'.format(self.TAG_MSGID_PLURAL, escape(tag.args[1].content)))
						template.write('{}[0] ""\n'.format(self.TAG_MSGSTR))
						template.write('{}[1] ""\n'.format(self.TAG_MSGSTR))
					elif tag.name == '\\pgettext':
						template.write('{} "{}"\n'.format(self.TAG_MSGCTXT, escape(tag.args[0].content)))
						template.write('{} "{}"\n'.format(self.TAG_MSGID, escape(tag.args[1].content)))
						template.write('{} ""\n'.format(self.TAG_MSGSTR))
					template.write('\n')
			return template_name

	def translate_tag(self, tag):
		if tag.name == '\\gettext':
			if not self.file:
				return tag.args[0].content
			else:
				return self[(tag.args[0].content, None)][self.TAG_MSGSTR]
		elif tag.name == '\\ngettext':
			if not self.file:
				rule = DEFAULT_PLURAL
				variants = (tag.args[0].content, tag.args[1].content)
			else:
				rule = self.get_header('Plural-Forms')
				variants = self[(tag.args[0].content, None)]
				variants = [ (k, v) for k,v in variants.items() if k.startswith(self.TAG_MSGSTR+'[')]
				variants = sorted(variants, key=lambda x: x[0])
				variants = [ i[1] for i in variants ]
			return convert_plurals(rule, tag.args[2].content, variants)
		elif tag.name == '\\pgettext':
			if not self.file:
				return tag.args[1].content
			return self[(tag.args[1].content, tag.args[0].content)][self.TAG_MSGSTR]
		elif tag.name == '\\today':
			return self._icu_date_full.format(float(datetime.datetime.now().timestamp()))
		elif tag.name == '\\formatdate':
			return self._icu_date_full.format(float(datetime.datetime(*[int(i.content) for i in tag.args][::-1]).timestamp()))
		else:
			raise Exception('Unknown tag: '+tag.name)

	def _ensure_parsed(self):
		if not self.file:
			raise Exception('Translation instance has no associated file')
		if self._parsed:
			return
		print('Parsing {}'.format(self.file))
		with open(self.file) as f:
			self._parsed = {}
			def add_tr(tag):
				key = (tag[self.TAG_MSGID], tag.get(self.TAG_MSGCTXT, None))
				if key in self._parsed:
					raise Exception('Key already exists: '+repr(key))
				self._parsed[key] = tag

			tag = {}
			def add_tag(key, value):
				value = value.replace('\n', '').replace('""', '').strip('"').replace('\\\\', '\\')
				tag[key] = value

			next_tag = None
			for line in f:
				print('LINE: '+line)
				if line.startswith('#'):
					continue
				if not line.startswith('"'):
					if tag and line.startswith(self.TAG_MSGID+' '):
						print('Translation ended: '+repr(tag))
						add_tr(tag)
						tag = {}

					print('Line is new tag')
					if next_tag is not None:
						print('NEXT TAG: '+next_tag+' -> '+next_tag_content)
						add_tag(next_tag, next_tag_content)

					sep = line.find(' ')
					next_tag = line[:sep].strip()
					next_tag_content = line[sep:].strip()
					print('Start of next tag: '+next_tag)
				else:
					next_tag_content += line
			add_tag(next_tag, next_tag_content)
			add_tr(tag)

			for i in self._parsed:
				print('TRANSLATIONS<'+repr(i)+'>=<'+repr(self._parsed[i])+'>')

		if ('',None) in self._parsed:
			self._header = {}
			headers = self._parsed.pop(('',None))[self.TAG_MSGSTR].split('\\n')
			print(repr(headers))
			for i in headers:
				sep = i.find(':')
				key = i[:sep].strip()
				value = i[sep+1:].strip()
				if key:
					self._header[key] = value

		for i in self._header:
			print('HEADER: "'+i+'" -> "'+self._header[i]+'"')

	def get_header(self, key):
		self._ensure_parsed()
		return self._header[key]

	def __getitem__(self, key):
		self._ensure_parsed()
		key = (key[0], key[1])
		print('GETITEM key="'+repr(key)+'" value="'+repr(self._parsed[key])+'"')
		return self._parsed[key]


def find_translations(input_file, directory=None, languages=None):
	directory = directory or os.getcwd()
	result = []
	if languages:
		base_name, _ = os.path.splitext(input_file)
		for i in languages:
			filename = os.path.join(directory, base_name+'.'+i+'.po')
			result.append(Translation.load(input_file, filename, Translation.ALLOW_NOT_EXISTING))
	else:
		for i in os.listdir(directory):
			if RE_PO_FILE.match(i):
				result.append(Translation.load(input_file, os.path.join(directory, i)))
	return result

def convert_plurals(description, n, variants):
	try:
		NPLURALS='nplurals'
		PLURAL='plural'
		desc = description.split(';')

		nplurals = desc[0].strip()
		if not nplurals.startswith(NPLURALS):
			raise Exception('First element "{}" does not start with "{}"'.format(
				nplurals, NPLURALS))
		nplurals = nplurals[len(NPLURALS):]
		nplurals = int(nplurals.strip('='))

		plural = desc[1].strip()
		if not plural.startswith(PLURAL):
			raise Exception('Second element "{}" does not start with "{}"'.format(
				plural, PLURAL))
		plural = plural[len(PLURAL):]
		plural = plural.strip('=')
		plural = tex_math.Parser(plural)
		plural.override_identifier('n', n)
		plural = tex_math.Generator(plural.parse()).generate()
	except Exception as e:
		raise Exception('Plurals definition must be formed as "nplurals: <n>; plural=<rule>"')

	if len(variants) != nplurals:
		raise Exception('Invalid number of variants found (expected {}, but {} found)'.format(nplurals, len(variants)))

	s = ''
	ending = ''
	s += '\\setcounter{_gettext_n}{'
	s += plural
	s += '}'
	for i in range(nplurals-1):
		s += '\\ifthenelse{\\equal{\\value{_gettext_n}}{'+str(i)+'}}{'
		s += variants[i]
		s += '}{'
		ending += '}'
	s += variants[-1]
	s += ending
	return s
	return 'convert\_plurals('+description+','+msgid1+','+msgid2+','+n+')'

if __name__ == '__main__':
	import unittest
	unittest.main()
