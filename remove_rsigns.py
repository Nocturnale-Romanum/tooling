import os
from collections import deque

def remove_rsigns_string(s):
  ### this looks at each character in a string that should be GABC code (the body of a GABC file, without headers).
  ### it attemps to deduce if this character is a rhythmic sign or information related to rhythmic signs.
  ### if so, it drops it; if not, it keeps it for outputting.
  s = deque(s)
  between_pars = False
  between_brackets_in_pars = False
  out = ""
  while(s):
    cur_char = s.popleft()
    if cur_char == '(':
      if between_pars:
        raise ValueError("Excess opening parentheses")
      else:
        between_pars = True
        out += cur_char
    elif cur_char == ')':
      if not between_pars:
        raise ValueError("Excess closing parentheses")
      else:
        between_pars = False
        out += cur_char
    elif cur_char == '[':
      if between_pars:
        if between_brackets_in_pars:
          raise ValueError("Excess opening brackets in pars")
        else:
          between_brackets_in_pars = True
      else:
        out += cur_char
    elif cur_char == ']':
      if between_pars:
        if not between_brackets_in_pars:
          raise ValueError("Excess closing brackets in pars")
        else:
          between_brackets_in_pars = False
      else:
        out += cur_char
    elif between_brackets_in_pars:
      pass # we drop whatever is inside brackets themselves inside parentheses: those are rsigns positioning info.
      ## beware, however: /[3] is equivalent to /// and will be lost when executing this algorithm! 
    elif not between_pars:
      out += cur_char # we keep whatever is not inside parentheses
    elif cur_char == ',':
      out += cur_char 
      if s[0] == '_': # "(,_)" is an exceptional case where an underscore is not a rhythmic sign (in Solesmes sense)
        # so we keep it
        cur_char = s.popleft()
        out += cur_char
    elif cur_char in ["_", ".", "'"]: # then we want to drop not only the current char, but any numbers that come after it
      while s[0] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
        s.popleft()
    else:
      out += cur_char
  return out
  
os.chdir("nocturnale-romanum/gabc")

filelist = os.listdir(".")
filelist = [x for x in filelist if x[-5:]==".gabc"]

for filename in filelist:
  text = open(filename, encoding="utf-8").read()
  text = text.split("%%")
  gabc = text[-1]
  try:
    text[-1] = remove_rsigns_string(gabc)
  except Exception as e:
    print(filename+" : "+str(e))
    text[-1] = gabc
  text = "%%".join(text)
  f = open(filename, "w", encoding="utf-8")
  f.write(text)
  f.close()
input()