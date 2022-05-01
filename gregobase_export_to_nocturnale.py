##### to be executed in a django shell of an instance of GregoAnalytics
##### a fresh grego.xml XML export of Gregobase is to be placed in the root directory of GregoAnalytics
##### hcode_to_gid.tsv should be placed in the same directory
##### this directory should have a subfolder "export" for the raw gabc files

from import_grego_db import *
flush_and_import()
l = open("gid2hcode.tsv").readlines()
del l[0]
l = [[x.strip() for x in y.split("\t")] for y in l]
l = [x for x in l if x[0]] # eliminate hcodes with no associated gid
for [gid, hcode, s, p] in l:
  c = Chant.objects.get(id=int(gid))
  out = open("export/"+hcode+".gabc", "w")
  mode = c.mode
  var = c.mode_var
  if mode == "NULL":
    mode = ""
  if var == "NULL":
    var = ""
  verses = c.gabc_verses
  if verses in ["NULL", None]:
    verses = ""
  out.write("mode:{}{};\n".format(mode, var))
  out.write("%%\n")
  try:
    out.write(eval(c.gabc)+verses+"\n")
  except:
    log=open("export.log", "wa")
    log.write(gid+"\n")
    log.close()
  finally:
    out.close()

#### to be executed in a django shell of an instance of Nocturnale
export_dir = "from_gregobase"
from home.models import *
import os
import time
files = os.listdir(export_dir)
u = User.objects.get(username="sandhofe")
for file_name in files:
  code = file_name.split(".gabc")[0]
  try:
    proposal = Proposal.objects.get(submitter=u, chant__code = code)
  except:
    log=open("new_files.log", "a")
    log.write(code+"\n")
    log.close()
    continue
  os.system("\\cp {}/{}.gabc nocturnale/static/gabc/{}_sandhofe.gabc".format(export_dir, code, code))
  proposal.makepng()
  time.sleep(40)


