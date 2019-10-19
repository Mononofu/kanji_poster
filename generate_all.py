import argparse
import concurrent.futures
import multiprocessing
import os
import shutil
import subprocess
import tempfile

from tqdm import tqdm

_COLORS_TO_RENDER = [
    'Acton', 'agGrnYl', 'agSunset', 'Algae', 'Amp', 'Balance', 'Bamako',
    'Batlow', 'Berlin', 'Bilbao', 'BluGrn', 'BrwnYl', 'Buda', 'BuGn', 'BuPu',
    'Burg', 'BurgYl', 'Cork', 'Curl', 'DarkMint', 'Davos', 'Deep', 'Delta',
    'Dense', 'Devon', 'Earth', 'Emrld', 'Fall', 'Geyser', 'GnBu', 'GrayC',
    'Gray', 'Greens', 'Haline', 'Hawaii', 'Ice', 'Imola', 'Inferno', 'LaJolla',
    'LaPaz', 'LinearL', 'Lisbon', 'Magenta', 'Magma', 'Matter', 'Mint', 'Nuuk',
    'Oleron', 'Oranges', 'OrRd', 'OrYel', 'Oslo', 'Peach', 'PinkYl', 'Plasma',
    'PuBuGn', 'PuBu', 'PuRd', 'Purples', 'PurpOr', 'Purp', 'RdPu', 'RedOr',
    'Reds', 'Roma', 'Solar', 'Speed', 'SunsetDark', 'Sunset', 'TealGrn',
    'Teal', 'TealRose', 'Tempo', 'Temps', 'Thermal', 'Tofino', 'Tokyo',
    'Tropic', 'Turbid', 'Turku', 'Vik', 'Viridis', 'YlGnBu', 'YlGn', 'YlOrBr',
    'YlOrRd'
]


def render_latex(color, output_dir):
  with tempfile.TemporaryDirectory() as temp:
    # Make a temporary copy to run compilation in.
    working_dir = os.path.join(temp, 'copy')
    shutil.copytree(os.getcwd(), working_dir)

    python_cmd = [
        'python3', 'generate_tex.py', '--minimal', '--colormap', color
    ]
    latex_cmd = [
        'lualatex', 'main.tex', '-interaction=nonstopmode', '-halt-on-error',
        '-file-line-error'
    ]

    # Generate the tex sources.
    subprocess.check_call(python_cmd, cwd=working_dir)

    # Compile the pdf.
    p = subprocess.Popen(latex_cmd,
                         cwd=working_dir,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out, err = p.communicate()

    if p.returncode != 0:
      raise ValueError('failed to run %s: %s\n\n%s' % (latex_cmd, out, err))

    # Move the pdf to the output dir.
    os.rename(os.path.join(working_dir, 'main.pdf'),
              os.path.join(output_dir, '%s.pdf' % color))

  return color


def main():
  parser = argparse.ArgumentParser(
      description="Compile kanji poster pdfs in different colors.")
  parser.add_argument('--output_dir',
                      help='Where to write the compiled pdfs',
                      required=True)
  args = parser.parse_args()

  if not os.path.exists(args.output_dir):
    os.makedirs(args.output_dir)

  with concurrent.futures.ThreadPoolExecutor(
      max_workers=multiprocessing.cpu_count()) as pool:
    fs = [
        pool.submit(render_latex, c, args.output_dir)
        for c in _COLORS_TO_RENDER
    ]
    for color in tqdm(concurrent.futures.as_completed(fs), total=len(fs)):
      pass


if __name__ == '__main__':
  main()
