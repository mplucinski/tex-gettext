tex-gettext
===========

![alt text](https://github.com/mplucinski/tex-gettext/raw/master/docs/logo_small.png "tex-gettext")

Localization tool for TeX/LaTeX documents.


Ever thought, why maintaining multiple language version is harder in case of documents, than computer software? One reason may be that great tool called "gettext" ( https://www.gnu.org/software/gettext/ ) exists, and makes localization of application very smooth process. The aim of tex-gettext (or getTeXt) is to bring the power of gettext to TeX/LaTeX documents.

NOTE: this software should be considered as alpha stage - it has been tested in quite simple test cases only.

Requirements
============

LaTeX part requires following packages: ```intcalc```. To properly handle unicode characters, your document should use ```fontspec``` package, and you should also have XeTeX installed.

Python part requires following packages: ```icu```, ```tz```, ```tzlocal```


Quick how-to
============
So, you have a TeX document, and want to localize it into another languages? Here is the way:

1. Add ```\usepackage{gettext}``` in the part of your document where you load external packages.

2. Copy gettext.sty into your document's directory - or install it in place where TeX will see it

3. Find all strings that shall be translated. Replace them with calls of one of ```\gettext``` pseudo-commands (pseudo - as they are not really TeX commands, but are handled entirely in preprocessor)

  For simple phrases:

  ```\gettext{Hello world!}```

  If you need to use the same phrase again, but you suppose the translation may differ from the first one, attach a context description:

  ```\pgettext{in another world}{Hello world!}```

  If your phrase contains external argument that may be singular, or plural, use:

  ```\ngettext{Order one beer}{Order #1 beers}{#1}```

4. Now, your document is ready to extract the phrases. Invoke:

  ```$ generate.py --input=the_document.tex --languages=pt_BR,fr_FR```

  Remember that every element in languages list must be an actual locale name, in Unix format (two lowercase letters for language, underscore, two uppercase letters for country)

5. Now, you will get translation files, in our example they will be ```the_document.pt_BR.po``` and ```the_document.fr_FR.po``` . You can edit them manually, or use one of many available applications.

  For KDE users, I'd suggest to use Lokalize (http://userbase.kde.org/Lokalize). GNOME equivalent is called Gtranslator (https://wiki.gnome.org/Apps/Gtranslator)

6. When your files are ready, run generator again:

  ```$ generate.py --input=the_document.tex```

  Note, that you do not need to specify languages again, as generate.py will find matching .po files automatically.

If everything went well, you should see three PDF files now: ```the_document.en_US.pdf```, ```the_document.pt_BR.pdf``` and ```the_document.fr_FR.pdf```. If you use Linux, all of them should be automatically opened in your default PDF viewer.


Available (pseudo) macros
=========================
As written above, getTeXt's macros aren't real TeX macros, as they are entirely handled and replaced by their results during ```.tex``` files generating, and are not exposed to TeX engine itself. Nevertheless, here is the list of available options:

Translation macros (gettext family)
-----------------------------------

Following macros are meant to provide core functionality of getTeXt:

###  ```\gettext{phrase}```

This is basic translation macro. It gets only one argument and work very predictably.

#### Arguments:

  ```phrase``` - The phrase that shall be translated.

#### Result:

  Matching phrase in target language.

### ```\pgettext{context description}{phrase}```

This macro is intended to be used, when the same phrase appears in the document, but some occurencies describe diffent things than others. It is possible (and indeed very usual) that those phrases will not look that same in target languages. Adding context description makes them to appear as different entities in localization ```.po``` files, and place them correctly in final documents.

#### Arguments:

  ```context description``` - String describing the context of the phrase. It does not appear in final document, but is visible in ```.po``` file to help translator in distinguishing them.

  ```phrase``` - The phrase that shall be translated.

#### Result:

  Matching phrase in target language.

### ```\ngettext{phrase singular}{phrase plural}{count}```

This macro allows to handle cases, when grammatical form of words changes when associated count increases. In most languages, phrase differs while talking about single or multiple things (singular and plural forms), but some languages have even more (3, 4 and maybe more...) available forms and quite complicated rules describing when one should be used. This macro allows to handle such situations.

A long, detailed description on the subject of handling plural forms is available in gettext's documentation: https://www.gnu.org/software/gettext/manual/gettext.html#Plural-forms . getTeXt tries to stricly follow gettext's approach, including parsing source ```Plural-Forms``` headers and generating TeX equivalents.

#### Arguments:

  ```phrase singular``` - The singular form of phrase in source language

  ```phrase plural``` - The plural form of phrase in source language

  ```count``` - The "count" of things that are described by phrases. It is used to select appropriate form of sentence. May be outer-macro attribute, like ```#1```.

#### Result:

  TeX code that is able to select proper form of target phrase according to counter value.

### ```\npgettext{context description}{phrase singular}{phrase plural}{count}```

This macro is connection of ```\pgettext``` and ```\ngettext```. It is helpful when dealing with issue of different context *and* handling plural forms, in one phrase.

#### Arguments:

  ```context description``` - String describing the context of the phrase. It does not appear in final document, but is visible in ```.po``` file to help translator in distinguishing them.

  ```phrase singular``` - The singular form of phrase in source language

  ```phrase plural``` - The plural form of phrase in source language

  ```count``` - The "count" of things that are described by phrases. It is used to select appropriate form of sentence. May be outer-macro attribute, like ```#1```.

#### Result:

  TeX code that is able to select proper form of target phrase according to counter value.


Support macros
--------------

Those macros are especially defined to be helpful in handling some common localization issues, unrealted to phrase-translation matching.

### ```\today```

This macro returns current date, in format preffered in target language. For example, target ```en_US``` shows me today ```Tuesday, May 6, 2014```, while ```de_DE``` shows ```Dienstag, 6. Mai 2014``` and ```pl_PL``` shows ```wtorek, 6 maja 2014```.

### ```\formatdate{day}{month}{year}```

This macro returns given date in format preffered in target language. For example, command ```\formatdate{21}{12}{2012}``` in ```en_US``` gives ```Friday, December 21, 2012```, while in ```de_DE``` it is ```Freitag, 21. Dezember 2012```, and in ```pl_PL``` it shows ```piątek, 21 grudnia 2012```.
