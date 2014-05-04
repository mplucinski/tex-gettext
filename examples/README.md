There is currently one example that presents basic tool functionality.

There are a few important files in this directory:

sample_doc.tex - This is base document. You can see, how would look a document that is ready to translation

sample_doc.de_DE.po - This is the translation file for German

sample_doc.pl_PL.po - This is the translation file for Polish

gettext.sty - This is additional package that is included by sample_doc.tex



To generate output, run:

```$ ../generate.py --input=sample_doc.tex```

A bunch of files will be generated (sorry, this is general TeX issue!), and in the end, three final PDFs will be generated (and if you use Linux, automatically opened using xdg-open).