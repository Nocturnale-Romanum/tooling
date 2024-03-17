### this parses use of \gscore with office part "R" (modifiable) to establish a list of unique (hcode, piece_index_name)

def make_index():
    os.chdir("G:\\Archives\\liturgie\\nocturnale_romanum\\liber-responsorialis")
    l = os.listdir(".")
    l = [x for x in l if x[-4:] == ".tex"]
    ll = []
    for x in l:
        ll+=open(x).readlines()
    ll = [x for x in ll if "gscore" in x]
    ll = [x for x in ll if "{R}" in x]
    ll = [x.split('{') for x in ll]
    l = [ (x[1], x[4]) for x in ll]
    l = [ (x[0].split('}')[0], x[1].split('}')[0]) for x in l]
    l = list(set(l))
    ll = l.sort(key=lambda x: x[1])
    s = "\n".join(["\t".join(x) for x in l])
    f=open("index.tsv", "w")
    f.write(s)
    f.close()
