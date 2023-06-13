from home.models import *
import shutil
gabcFolder = os.path.join("nocturnale", "static", "gabc")
cc = Chant.objects.all()
for c in cc:
  pp = c.proposals.all()
  authors = [p.submitter.username for p in pp]
  if 'marteo' in authors and c.status != "SELECTED":
    authors.remove('marteo')
    if 'sandhofe' in authors:
      authors.remove('sandhofe')
    if authors == []:
      p = c.proposals.get(submitter__username='marteo')
      fpath = p.filepath()
      new_fpath = os.path.join(gabcFolder, c.code + ".gabc")
      shutil.copyfile(fpath, new_fpath)
	  