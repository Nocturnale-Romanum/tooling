-- Emplois de chaque glyphe dans les pièces NR (<code>_<auteur>.gabc), avec le vrai parseur de gregoriotex-nabc.lua.
-- usage : texlua nabc_occurrences.lua <gregoriotex-nabc.lua> <gregall_metrics.lua> <sortie.tsv> <gabc…>
-- Sortie : code, auteur, syllabe, fragment NABC, glyphes posés (noms gregall, séparés par des espaces),
-- résolution : pour chaque neume, « glyphe complet demandé=glyphe de la police+pp+su+lettres ajoutés »
-- (pp, su, lettres non vides : composés dynamiquement par gregoriotex-nabc.lua, à côté du glyphe).
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
-- instrumentation de gregoriotex-nabc.lua au chargement : glyphe complet demandé et glyphe retenu
local LOG = {}
NABC_LOG = function(full, r, pp, su, ls) LOG[#LOG + 1] = full .. "=" .. r .. "+" .. pp .. "+" .. su .. "+" .. ls end
local fh = io.open(nabclua, "rb"); local src = fh:read("*a"); fh:close()
local function patch(a, b)
  local i, j = src:find(a, 1, true)
  assert(i and not src:find(a, j + 1, true), "gregoriotex-nabc.lua : motif introuvable ou multiple")
  src = src:sub(1, i - 1) .. b .. src:sub(j + 1)
end
patch("    local ls5 = ''\n    lscount = 0",
      "    local NABC_ppo, NABC_suo, NABC_lso = pp, su, ''\n" ..
      "    do local k = 0; while ls[k] do NABC_lso = NABC_lso .. ls[k]; k = k + 1 end end\n" ..
      "    local ls5 = ''\n    lscount = 0")
patch("      if not r or (pp ~= '' and not gregalltab[kind][pp])",
      "      if NABC_LOG then\n" ..
      "        local rest = ''\n" ..
      "        for k = 0, lscount - 1 do if ls[k] and ls[k] ~= '' then rest = rest .. ls[k] end end\n" ..
      "        NABC_LOG(base .. NABC_ppo .. NABC_suo .. NABC_lso, r or 'ERR', pp, su, rest)\n" ..
      "      end\n" ..
      "      if not r or (pp ~= '' and not gregalltab[kind][pp])")
assert(load(src, "=gregoriotex-nabc.lua"))()
gregoriotex.init_nabc_font("gregall")
local o = io.open(outfile, "w")
o:write("code\tauteur\tsyllabe\tnabc\tglyphes\tresolution\n")
local n = 0
for i = 4, #arg do
  local fh = io.open(arg[i], "rb"); local s = fh:read("*a"); fh:close()
  local code, auteur = arg[i]:match("([^/\\]+)_([^_/\\]+)%.gabc$")
  code = code or arg[i]; auteur = auteur or ""
  local body = s:match("\n%%%%\r?\n(.*)$") or ""
  if s:match("nabc%-lines:%s*1") then
    for syl, grp in body:gmatch("([^%s%(%)]*)%(([^%)]*)%)") do
      local idx = 0
      syl = syl:gsub("<[^>]*>", ""):gsub("\t", " ")
      for seg in (grp .. "|"):gmatch("([^|]*)|") do
        if idx % 2 == 1 and seg ~= "" then
          LOG = {}
          local out = gregoriotex.parse_nabc(seg, "gregall", 1)
          local names = {}
          for c in out:gmatch("char(%d+)") do names[#names + 1] = code2name[tonumber(c)] or ("?" .. c) end
          o:write(code, "\t", auteur, "\t", syl, "\t", seg, "\t", table.concat(names, " "), "\t", table.concat(LOG, " "), "\n")
          n = n + 1
        end
        idx = idx + 1
      end
    end
  end
end
o:close()
print("fragments", n)
