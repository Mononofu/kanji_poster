# -*- coding: utf-8
import collections
import json
import math
import re

import jaconv

class KanjiInfo(object):
  def __init__(self, meaning, onyomi, kunyomi, wanikani_level=None, grade=None):
    self.meaning = meaning
    self.onyomi = onyomi
    self.kunyomi = kunyomi
    self.wanikani_level = wanikani_level
    self.grade = grade
    self.frequency = None

_NUM_WANIKANI_LEVELS = 60

def read_wanikanji():
  kanji_info = {}

  for level in range(1, _NUM_WANIKANI_LEVELS + 1):
    with open('/home/mononofu/Dropbox/eBooks/languages/japanese/WaniKani/with_similar_kanji/%02d_kanji.csv' % level) as f:
      lines = f.read()
    for line in lines.strip().split('\n'):
      parts = line.split(';')
      kanji, meaning, onyomi, kunyomi = parts[2], parts[3], parts[5], parts[6]
      kanji_info[kanji] = KanjiInfo(meaning, onyomi, kunyomi, wanikani_level=int(level))

  return kanji_info

def strip_link(wiki_text):
  a, b = re.findall(r'style="font-size:2em"\|\[\[wikt:(\w+)\|(\w+)\]\]', wiki_text)[0]
  if a != b:
    raise ValueError("mismatch in: %s" % wiki_text)
  return a


# Some kanji are outside the basic character set, instead these replacement
# characters are used in practice (see
# https://en.wikipedia.org/wiki/List_of_jōyō_kanji#List_of_characters for
# details).
_KANJI_REPLACEMENTS = {
    '𠮟': '叱',
    '塡': '填',
    '剝': '剥',
    '頰': '頬',
}

def merge_with_joyo(kanji_info):
  with open('joyo_kanji.txt') as f:
    wiki_joyo = f.read()
  for line in wiki_joyo.strip().split('\n')[8:]:
    _, _, kanji, _, _, num_strokes, grade, _, meaning, readings = line.split('||')
    kanji = strip_link(kanji)
    kanji = _KANJI_REPLACEMENTS.get(kanji, kanji)
    grade = 7 if grade == 'S' else int(grade)

    if kanji in kanji_info:
      kanji_info[kanji].grade = grade
    else:
      # Readings are of the form: "ロウ、もてあそ-ぶ<br>rō, moteaso-bu"
      readings = readings.split('<br>')[0].split('、')  # Get japanese version.
      onyomi = [r for r in readings if r == jaconv.hira2kata(r)]
      kunyomi = [r for r in readings if r == jaconv.kata2hira(r)]

      kanji_info[kanji] = KanjiInfo(meaning,
                                    onyomi[0] if onyomi else None,
                                    kunyomi[0] if kunyomi else None,
                                    grade=grade)

def add_frequency(kanji_info):
  # Computed by counting the frequency of all kanji in a combination of several
  # sources:
  #  - Japanese Harry Potter from https://uk.shop.pottermore.com/collections/ebook/products/harry_potter_the_complete_collection_17_9781781106532
  #  - Stories from https://satorireader.com/
  #  - Articles from NHK Easy News: https://www3.nhk.or.jp/news/easy/
  with open('kanji_frequency.json') as f:
    kanji_frequency = json.load(f)
  unseen_kanji = []
  for kanji, info in kanji_info.items():
    if kanji in kanji_frequency:
      info.frequency = kanji_frequency[kanji]
    else:
      # Some Kanji never occur in any of the sources from above.
      info.frequency = 0
      unseen_kanji.append(kanji)
  if unseen_kanji:
    print('failed to find frequency info for: ', ', '.join(unseen_kanji))

# Some of the meanings are too long to fit in one line, so we replace them with
# a shorter version.
_MEANING_REPLACEMENTS = {
    '賀': 'congratulate',
    '醒': 'disillusioned',
    '餅': 'mochi',
    '麓': 'foothills',
    '壱': '1 (legal)',
    '弐': 'II, second',
    '翁': 'old man',
    '緻': 'fine',
    '箇': 'counters',
    '楷': 'printed style',
    '弟': 'little brother',
    '番': 'number (series)',
    '第': 'ordinal number',
    '様': 'Mr., Mrs.',
    '億': '100 million',
    '署': 'govt. office',
    '枚': 'counter: sheets',
    '墾': 'break ground',
}


def is_set(text):
  return text and text not in ['N/A', 'None']

def color(text, c):
  return r'\textcolor[HTML]{%s}{%s}' % (c, text)

def sort_key(kv):
  info = kv[1]
  return (1 - info.frequency, info.wanikani_level or 61, info.grade or 7)

def generate_poster_tex(kanji_info):
  cell_size = 2.05
  num_cols = 56

  tex = ""
  cum_freq = 0
  for i, (kanji, info) in enumerate(sorted(kanji_info.items(),
                                   key=sort_key)[0:5000]):
    cum_freq += info.frequency

    row = int(i / num_cols)
    x = cell_size * (i % num_cols) - 56.5
    y = 40 - cell_size * row
    tex += "\\node[Square] at (%f, %f) {};\n" % (x, y)
    tex += "\\node[Kanji] at (%f, %f) {%s};\n" % (x, y + 0.5, kanji)
    if is_set(info.onyomi):
      onyomi = jaconv.hira2kata(info.onyomi.split(',')[0])
      tex += "\\node[Onyomi] at (%f, %f) {%s};\n" % (x + 0.05, y + 0.1, onyomi)
    if is_set(info.kunyomi):
      tex += "\\node[Kunyomi] at (%f, %f) {%s};\n" % (x - 0.05, y + 0.1, info.kunyomi.split(',')[0])
    meaning = info.meaning.split(',')[0]
    if kanji in _MEANING_REPLACEMENTS:
      print('replaced', i, kanji, meaning, _MEANING_REPLACEMENTS[kanji])
      meaning = _MEANING_REPLACEMENTS[kanji]
    if len(meaning) > 14:
      print(i, kanji, meaning, )
    tex += "\\node[Meaning] at (%f, %f) {%s};\n" % (x, y + 1.75, meaning)
    # tex += "\\node[Meaning] at (%f, %f) {%.2f\\%%};\n" % (x, y + 1.75, cum_freq * 100)

    if (i + 1) % num_cols == 0 or (i + 1) == len(kanji_info):
      # If this is the last character in the row, record the cumulative
      # frequency reached.
      tex += "\\node[Meaning] at (%f, %f) {%.2f\\%%};\n" % (
        -58.5,
        38.8 - row * cell_size + 1.75,
        cum_freq * 100)

  for row in range(int(math.ceil(len(kanji_info) / num_cols))):
    tex += "\\node[Meaning] at (%f, %f) {%d - %d};\n" % (
      -58.5,
      39.4 - row * cell_size + 1.75,
      row * num_cols + 1, (row + 1) * num_cols)

  return tex


def main():
  kanji_info = read_wanikanji()
  merge_with_joyo(kanji_info)
  add_frequency(kanji_info)

  with open('footer.tex', 'w') as f:
    f.write('%d kanji covering %.2f\\%% of common Japanese text, ordered by frequency.' % (
      len(kanji_info),
      100 * sum(info.frequency for info in kanji_info.values())))

  with open('kanji_grid.tex', 'w') as f:
    f.write(generate_poster_tex(kanji_info))


if __name__ == '__main__':
  main()
