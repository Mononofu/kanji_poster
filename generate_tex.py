# -*- coding: utf-8
import abc
import argparse
import csv
import json
import math
import re

import colour
import jaconv


class KanjiInfo(object):
  def __init__(self, meaning, onyomi, kunyomi, wanikani_level=None,
               grade=None):
    self.meaning = meaning
    self.onyomi = onyomi
    self.kunyomi = kunyomi
    self.wanikani_level = wanikani_level
    self.grade = grade
    self.frequency = None
    self.jlpt_level = None
    self.indices = {}


def read_wanikanji():
  kanji_info = {}

  def get_readings(reading):
    if not reading or reading in ['None', 'N/A']:
      return []
    return reading.split(',')

  with open('data/wanikani.csv') as f:
    lines = f.read()
  for line in lines.strip().split('\n'):
    level, kanji, meaning, onyomi, kunyomi = line.split(';')
    kanji_info[kanji] = KanjiInfo(meaning,
                                  get_readings(onyomi),
                                  get_readings(kunyomi),
                                  wanikani_level=int(level))

  return kanji_info


def strip_link(wiki_text):
  a, b = re.findall(r'style="font-size:2em"\|\[\[wikt:(\w+)\|(\w+)\]\]',
                    wiki_text)[0]
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
  # Dumped from https://en.wikipedia.org/wiki/List_of_jōyō_kanji.
  with open('data/joyo_kanji.txt') as f:
    wiki_joyo = f.read()
  for line in wiki_joyo.strip().split('\n')[8:]:
    _, _, kanji, _, _, num_strokes, grade, _, meaning, readings = line.split(
        '||')
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

      kanji_info[kanji] = KanjiInfo(meaning, onyomi, kunyomi, grade=grade)


def add_frequency(kanji_info):
  # Computed by counting the frequency of all kanji in a combination of several
  # sources:
  #  - Japanese Harry Potter from https://uk.shop.pottermore.com/collections/ebook/products/harry_potter_the_complete_collection_17_9781781106532
  #  - Stories from https://satorireader.com/
  #  - Articles from NHK Easy News: https://www3.nhk.or.jp/news/easy/
  with open('data/kanji_frequency.json') as f:
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


_SORT_INDICES = {
    'heisig': 'Heisig RTK Index',
    'rtk2': 'RTK2 Index',
    '2k1K0': '2k1KO Index',
    'opt_vocab_sort': 'Opt Vocab Sort Index',
    'kanji_leaner_course': 'Kanji Learner Course Index',
    'frequency': 'Freq.',
    'stroke_count': 'stroke count',
}


def add_sort_orders(kanji_info):
  # From https://docs.google.com/spreadsheets/d/19zorQpMJi00-b6abuvE5uBAIsMMqWVrbeHD-bIrkggQ/
  with open('data/kanken_heisig.csv') as f:
    reader = csv.DictReader(f)
    kanji_to_row = {row['Kanji']: row for row in reader}

  for kanji, info in kanji_info.items():
    if kanji in kanji_to_row:
      row = kanji_to_row[kanji]
      for label, column in _SORT_INDICES.items():
        if row[column]:
          info.indices[label] = int(row[column])


def add_radicals(kanji_info):
  # Load radical data.
  with open('data/radicals.txt') as f:
    lines = [l for l in f.read().strip().split('\n') if not l.startswith('#')]
  kanji_to_radicals = {}
  for line in lines:
    kanji, radicals = line.split(' : ')
    kanji_to_radicals[kanji] = radicals.split()

  unseen_kanji = []
  for kanji, info in kanji_info.items():
    if kanji in kanji_to_radicals:
      info.radicals = kanji_to_radicals[kanji]
    else:
      info.radicals = []
      unseen_kanji.append(kanji)

  if unseen_kanji:
    print('failed to find radicals for: ', ', '.join(unseen_kanji))


def add_jlpt_level(kanji_info):
  # Data from https://www.nihongo-pro.com/kanji-pal/list/jlpt
  with open('data/jlpt.json') as f:
    jlpt = json.load(f)
  for level, kanji_list in jlpt.items():
    level = int(level)
    for kanji in kanji_list:
      if kanji in kanji_info:
        kanji_info[kanji].jlpt_level = level


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


class Colorizer(abc.ABC):
  """Interface for different ways of coloring kanji."""
  @abc.abstractmethod
  def choose_color(self, kanji, info):
    pass


class FrequencyColorizer(Colorizer):
  """Colors kanji by the log of their frequency."""
  def __init__(self, kanji_info, color_frequent, color_rare):
    # Gradient from a very dark color for infrequent characters to a very light
    # color for the most frequent ones.
    self._n_steps = 20
    self._colors = [
        c.hex_l[1:] for c in colour.Color(color_rare).range_to(
            colour.Color(color_frequent), self._n_steps)
    ]
    freqs = [self._log_freq(i) for i in kanji_info.values()]
    self._min, self._max = min(freqs), max(freqs)

  def _log_freq(self, info):
    min_freq = -6
    if info.frequency > 0:
      return max(min_freq, math.log10(info.frequency))
    return min_freq

  def choose_color(self, kanji, info):
    # Map the frequency to a log scale before indexing the color gradient.
    index = int((self._log_freq(info) - self._min) / (self._max - self._min) *
                (self._n_steps - 1))
    return self._colors[index]


_COLORING_METHODS = {
    'frequency': FrequencyColorizer,
}


def format_readings(readings, convert, max_chars=6):
  candidates = []
  for reading in readings:
    reading = reading.strip().replace('-', '.')
    if sum(len(c) for c in candidates) + len(reading) >= max_chars:
      break
    candidates.append(reading)
  return '・'.join(convert(c) for c in candidates)


def color(text, c):
  return r'\textcolor[HTML]{%s}{%s}' % (c, text)


def tikz_node(kind, x, y, text=''):
  return "\\node[%s] at (%f, %f) {%s};" % (kind, x, y, text)


def render_kanji(kanji, info, x, y, colorizer, minimal):
  """Renders a kanji and related information at the specified xy position."""
  nodes = []

  def add_node(kind, dx, dy, text=''):
    """Adds a tikz node with the specified offset from the center."""
    nodes.append(tikz_node(kind, x + dx, y + dy, text))

  add_node('Kanji', 0, 0.5, color(kanji, colorizer.choose_color(kanji, info)))

  if not minimal:
    add_node('Square', 0, 0)

    if info.onyomi:
      onyomi = format_readings(info.onyomi, jaconv.hira2kata)
      add_node('Onyomi', 0.05, 0.1, '\\hbox{\\tate %s}' % onyomi)

    if info.kunyomi:
      kunyomi = format_readings(info.kunyomi, jaconv.kata2hira)
      add_node('Kunyomi', -0.05, 0.1, '\\hbox{\\tate %s}' % kunyomi)

    meaning = info.meaning.split(',')[0]
    if kanji in _MEANING_REPLACEMENTS:
      meaning = _MEANING_REPLACEMENTS[kanji]
    add_node('Meaning', 0, 1.75, meaning)

  return nodes


def generate_poster_tex(kanji_info,
                        sort_by,
                        colorizer,
                        minimal=False,
                        first_n=None):
  """Generates Tex to render all kanji in kanji_info in a big poster."""
  sorted_info = sorted(kanji_info.items(), key=lambda kv: sort_by(kv[1]))
  if first_n:
    sorted_info = sorted_info[:first_n]

  # The center of the poster is at (0, 0). Since we are using an A0 landscape
  # poster, the total width is 118.9 and the height 84.1, so the top left corner
  # is at roughly x=59.4 and y=42.
  # TODO: We could derive cell sizes and column/row count automatically based on
  # the number of Kanji we want to show.
  cell_size = 2.05  # Must match \Size in main.tex.
  num_cols = 56

  def x(col):
    return cell_size * col - 56

  def y(row):
    return 40 - cell_size * row

  nodes = []
  cum_freq = 0
  for i, (kanji, info) in enumerate(sorted_info):
    cum_freq += info.frequency

    row = int(i / num_cols)
    col = i % num_cols

    nodes.extend(render_kanji(kanji, info, x(col), y(row), colorizer, minimal))

    if (i + 1) % num_cols == 0 or (i + 1) == len(kanji_info):
      # If this is the last character in the row, record the cumulative
      # frequency reached.
      nodes.append(
          tikz_node('Meaning', x(-1),
                    y(row) + 0.6, '%.2f\\%%' % (cum_freq * 100)))

  # Indicate the numbers of the kanji in each row.
  for row in range(int(math.ceil(len(kanji_info) / num_cols))):
    nodes.append(
        tikz_node('Meaning', x(-1),
                  y(row) + 1.2,
                  '%d - %d' % (row * num_cols + 1, (row + 1) * num_cols)))

  return '\n'.join(nodes)


def make_sort_function(index):
  def get_key(info):
    if index == 'wanikani':
      key = info.wanikani_level or 61
    if index == 'jlpt':
      key = 5 - (info.jlpt_level or 0)
    else:
      key = info.indices.get(index, 100000)
    return (key, 1 - info.frequency)

  return get_key


def main():
  parser = argparse.ArgumentParser(
      description="Generate kanji poster LaTeX source")
  parser.add_argument('--sort_by',
                      choices=['wanikani', 'jlpt'] +
                      list(_SORT_INDICES.keys()),
                      default='heisig',
                      help='How to sort Kanji on the poster, default=heisig')
  parser.add_argument(
      '--color_by',
      choices=list(_COLORING_METHODS.keys()),
      default='frequency',
      help='How to color Kanji on the poster, default=frequency')
  parser.add_argument(
      '--color_rare',
      default='#0e254c',
      help='Color for the rare end of the kanji color gradient.')
  parser.add_argument(
      '--color_frequent',
      default='#6fa3fb',
      help='Color for the frequent end of the  kanji color gradient.')
  parser.add_argument('--minimal', default='minimal', action='store_true')
  parser.set_defaults(minimal=False)

  args = parser.parse_args()

  kanji_info = read_wanikanji()
  merge_with_joyo(kanji_info)
  add_frequency(kanji_info)
  add_jlpt_level(kanji_info)

  # We don't use radical data at the moment, but it could be useful to
  # sort/group Kanji.
  add_radicals(kanji_info)

  add_sort_orders(kanji_info)

  colorizer = _COLORING_METHODS[args.color_by](kanji_info, args.color_frequent,
                                               args.color_rare)

  with open('tex/footer.tex', 'w') as f:
    f.write('%d kanji covering %.2f\\%% of common Japanese text.' %
            (len(kanji_info), 100 * sum(info.frequency
                                        for info in kanji_info.values())))

  with open('tex/kanji_grid.tex', 'w') as f:
    f.write(
        generate_poster_tex(kanji_info,
                            make_sort_function(args.sort_by),
                            colorizer,
                            minimal=args.minimal))


if __name__ == '__main__':
  main()
