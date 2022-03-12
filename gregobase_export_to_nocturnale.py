##### to be executed in a django shell of an instance of GregoAnalytics
##### a fresh grego.xml XML export of Gregobase is to be placed in the root directory of GregoAnalytics
##### hcode_to_gid.tsv should be placed in the same directory
##### this directory should have a subfolder "export" for the raw gabc files

from import_grego_db import *
flush_and_import()
l = open("hcode_to_gid.tsv").readlines()
del l[0]
l = [x.strip().split("\t") for x in l]
l = [x for x in l if len(x) == 2] # eliminate hcodes with no associated gid
for [gid, hcode] in l:
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

