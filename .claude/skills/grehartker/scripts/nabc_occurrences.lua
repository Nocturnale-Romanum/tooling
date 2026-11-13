-- Emplois de chaque glyphe dans les pièces NR, avec le vrai parseur de gregoriotex-nabc.lua.
-- usage : texlua nabc_occurrences.lua <gregoriotex-nabc.lua> <gregall_metrics.lua> <sortie.tsv> <gabc…>
-- Sortie : code, syllabe, fragment NABC, glyphes posés (noms gregall, séparés par des espaces).
-- Lu par hartker.occurrences() (sources_nr.py, retenir.py) ; à refaire quand les gabc changent.
local nabclua, metricsfile, outfile = arg[1], arg[2], arg[3]
luatexbase = { catcodetables = setmetatable({}, {__index=function() return 0 end}) }
gregoriotex = {}
tex = { sprint = function() end }
local m = dofile(metricsfile)
local unicodes, chars, code2name = {}, {}, {}
for _, g in ipairs(m) do
  unicodes[g[1]] = g[2]; chars[g[2]] = { width = g[3], height = g[4], depth = g[5] }; code2name[g[2]] = g[1]
end
font = { current = function() return 1 end,
         getfont = function() return { resources = { unicodes = unicodes }, characters = chars } end }
dofile(nabclua)
gregoriotex.init_nabc_font("gregall")
local o = io.open(outfile, "w")
o:write("code\tsyllabe\tnabc\tglyphes\n")
local n = 0
for i = 4, #arg do
  local fh = io.open(arg[i], "rb"); local s = fh:read("*a"); fh:close()
  local code = arg[i]:match("([^/\\]+)_marteo%.gabc$") or arg[i]
  local body = s:match("\n%%%%\r?\n(.*)$") or ""
  if s:match("nabc%-lines:%s*1") then
    for syl, grp in body:gmatch("([^%s%(%)]*)%(([^%)]*)%)") do
      local idx = 0
      syl = syl:gsub("<[^>]*>", ""):gsub("\t", " ")
      for seg in (grp .. "|"):gmatch("([^|]*)|") do
        if idx % 2 == 1 and seg ~= "" then
          local out = gregoriotex.parse_nabc(seg, "gregall", 1)
          local names = {}
          for c in out:gmatch("char(%d+)") do names[#names + 1] = code2name[tonumber(c)] or ("?" .. c) end
          o:write(code, "\t", syl, "\t", seg, "\t", table.concat(names, " "), "\n")
          n = n + 1
        end
        idx = idx + 1
      end
    end
  end
end
o:close()
print("fragments", n)
