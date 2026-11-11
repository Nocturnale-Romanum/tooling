-- usage: texlua nabc_usage.lua <gregoriotex-nabc.lua> <metrics.lua> <out.tsv> <gabc files...>
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
local count, errs, files, snippets = {}, {}, 0, 0
for i = 4, #arg do
  local fh = io.open(arg[i], "rb"); local s = fh:read("*a"); fh:close()
  local body = s:match("\n%%%%\r?\n(.*)$") or ""
  if s:match("nabc%-lines:%s*1") then
    files = files + 1
    for grp in body:gmatch("%(([^%)]*)%)") do
      local idx = 0
      for seg in (grp .. "|"):gmatch("([^|]*)|") do
        if idx % 2 == 1 and seg ~= "" then
          snippets = snippets + 1
          local out = gregoriotex.parse_nabc(seg, "gregall", 1)
          if out:find("ERR") then errs[seg] = (errs[seg] or 0) + 1 end
          for c in out:gmatch("char(%d+)") do
            local n = code2name[tonumber(c)] or ("?" .. c)
            count[n] = (count[n] or 0) + 1
          end
        end
        idx = idx + 1
      end
    end
  end
end
local o = io.open(outfile, "w")
o:write("glyphname\tuses\n")
local names = {}
for n in pairs(count) do names[#names+1] = n end
table.sort(names, function(a,b) return count[a] > count[b] end)
for _, n in ipairs(names) do o:write(n, "\t", count[n], "\n") end
o:close()
local e = io.open(outfile .. ".errors", "w")
for k, v in pairs(errs) do e:write(k, "\t", v, "\n") end
e:close()
print("files", files, "snippets", snippets, "distinct glyphs used", #names)
