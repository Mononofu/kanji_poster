# Kanji Poster

![screenshot](screenshot.jpg)

A simple python script to generate the LaTeX source for a poster to show all [jōyō kanji](https://en.wikipedia.org/wiki/List_of_jōyō_kanji) as well as the extra kanji included in [WaniKani](https://www.wanikani.com).

In total the poster includes 2200 kanji. The script supports varies ways of sorting and coloring the kanji; in the screenshot above they are sorted according to the order they occur in [Remembering the Kanji](https://en.wikipedia.org/wiki/Remembering_the_Kanji_and_Remembering_the_Hanzi) by James Heisig and colored according to the log of their frequency in some common texts.

I've also checked in example versions of the poster with different fonts that you can download. Note that this is still a work in progress, I have not checked the poster for correctness.

- [IPAex Mincho](https://github.com/Mononofu/kanji_poster/blob/master/poster_mincho.pdf)
- [IPAex Gothic](https://github.com/Mononofu/kanji_poster/blob/master/poster_gothich.pdf)
- [Noto Sans](https://github.com/Mononofu/kanji_poster/blob/master/poster_noto_sans.pdf)
- [Noto Serif](https://github.com/Mononofu/kanji_poster/blob/master/poster_noto_serif.pdf)

## Usage

```bash
# Generate the LaTeX files.
python3 generate_tex.py

# Compile everything into a pdf.
lualatex main.tex
```

## Dependencies

The script uses [colour](https://pypi.org/project/colour/) to interpolate colors and [jaconv](https://pypi.org/project/jaconv/) to convert between hiragana and katakana for readings; you can install both from pip.

To compile the pdf, you'll need the LuaLaTeX package; on Ubuntu you can install this with:

```bash
sudo apt install texlive-luatex
```

Depending on the fonts you want to use, you might have to install some more packages:


```bash
# IPAexMincho and IPAexGothic
sudo apt install fonts-ipaexfont
```
