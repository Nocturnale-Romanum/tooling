import os

cantici = os.listdir("cantici")
psalmi = os.listdir("psalmi")

def add_lettrine(text):
    ### objectif: écrire en tête de psaume \item \hspace{-15pt}\parbox[b]{\linewidth}{\lettrine{L}{}orem ipsum...} \item...
    ### autrement dit encapsuler le premier verset dans une parbox[b] qui permet de positionner correctement la lettrine.
    text = text.strip()
    text = text.split("\n")
    line = text[0]
    items = line.split("\\item ")
    item = items[1]
    item = "\\hspace{-\psalmverseindent}\\parbox[b]{\\linewidth}{\\lettrine{"+item[0]+"}{}"+item[1:]+"}"
    items[1] = item
    line = "\\item ".join(items)
    text[0] = line
    text = "\n".join(text)
    return text

for f in cantici:
    text = open("cantici/"+f, encoding="utf8").read()
    text = add_lettrine(text)
    ff = open("cantici_lettrine/"+f, "w", encoding="utf8")
    ff.write(text)
    ff.close()

for f in psalmi:
    text = open("psalmi/"+f, encoding="utf8").read()
    text = add_lettrine(text)
    ff = open("psalmi_lettrine/"+f, "w", encoding="utf8")
    ff.write(text)
    ff.close()

