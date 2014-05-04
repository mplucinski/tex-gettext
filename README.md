tex-gettext
===========

![alt text](https://github.com/mplucinski/tex-gettext/raw/master/docs/logo_small.png "tex-gettext")

Localization tool for TeX/LaTeX documents.


Ever thought, why maintaining multiple language version is harder in case of documents, than computer software? One reason may be that great tool called "gettext" ( https://www.gnu.org/software/gettext/ ) exists, and makes localization of application very smooth process. The aim of this tool is to bring the power of gettext to TeX/LaTeX documents.

NOTE: this software should be considered as alpha stage - it has been tested in quite simple test cases


Quick how-to
============
So, you have a TeX document, and want to localize it into another languages? Here is the way:

1. Add ```\usepackage{gettext}``` in the part of your document where you load external packages.

2. Find all strings that shall be translated. Replace them with calls of one of ```\gettext``` pseudo-commands (pseudo - as they are not really TeX commands, but are handled entirely in preprocessor)

  For simple phrases:

  ```\gettext{Hello world!}```

  If you need to use the same phrase again, but you suppose the translation may differ from the first one, attach a context description:

  ```\pgettext{in another world}{Hello world!}```

  If your phrase contains external argument that may be singular, or plural, use:

  ```\ngettext{Order one beer}{Order #1 beers}{#1}```

3. Now, your document is ready to extract the phrases. Invoke:

  ```$ generate.py --input=the_document.tex --languages=pt_BR,fr_FR```

  Remember that every element in languages list must be an actual locale name, in Unix format (two lowercase letters for language, underscore, two uppercase letters for country)

4. Now, you will get translation files, in our example they will be ```the_document.pt_BR.po``` and ```the_document.fr_FR.po``` . You can edit them manually, or use one of many available applications.

  For KDE users, I'd suggest to use Lokalize (http://userbase.kde.org/Lokalize). GNOME equivalent is called Gtranslator (https://wiki.gnome.org/Apps/Gtranslator)

5. When your files are ready, run generator again:

  ```$ generate.py --input=the_document.tex```

  Note, that you do not need to specify languages again, as generate.py will find matching .po files automatically.

If everything went well, you should see three PDF files now: ```the_document.en_US.pdf```, ```the_document.pt_BR.pdf``` and ```the_document.fr_FR.pdf```. If you use Linux, all of them should be automatically opened in your default PDF viewer.
