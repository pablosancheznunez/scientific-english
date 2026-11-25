-- Glosario emergente: enlaza la primera aparición de cada término del glosario
-- en cada capítulo y muestra su definición al pasar el ratón o al enfocar con el teclado.
local terminos = nil
local usados = {}

local function quitar_tildes(s)
  local m = {["á"]="a",["é"]="e",["í"]="i",["ó"]="o",["ú"]="u",["ü"]="u",["ñ"]="n",["Á"]="a",["É"]="e",["Í"]="i",["Ó"]="o",["Ú"]="u",["Ñ"]="n"}
  for k, v in pairs(m) do s = s:gsub(k, v) end
  return s
end
local function norm(s) return quitar_tildes(pandoc.text.lower(s)) end

local function cargar()
  terminos = {}
  local dir = (quarto.project and quarto.project.directory) or "."
  local f = io.open(dir .. "/92-glosario.qmd", "r")
  if not f then return end
  local lineas = {}
  for l in f:lines() do lineas[#lineas + 1] = l end
  f:close()
  for i, l in ipairs(lineas) do
    local tit, id = l:match("^###%s+(.-)%s*{#(gl%-[%w%-]+)}")
    if tit and lineas[i + 1] then
      local def = lineas[i + 1]:gsub("%s*→.*$", ""):gsub("%*", ""):gsub("%[([^%]]*)%]%b()", "%1")
      -- variantes: el título completo y, si lleva paréntesis o barra, cada parte
      local variantes = {}
      local base = tit:gsub("%s*%b()", "")
      variantes[#variantes + 1] = base
      for parte in tit:gmatch("%(([^%)]+)%)") do variantes[#variantes + 1] = parte end
      local antes_y = base:match("^(.-) y ")
      if antes_y and #antes_y >= 4 then variantes[#variantes + 1] = antes_y end
      if base:find(" y ") == nil and base:find("/") then
        for parte in base:gmatch("[^/]+") do variantes[#variantes + 1] = parte:gsub("^%s+", ""):gsub("%s+$", "") end
      end
      for _, v in ipairs(variantes) do
        local palabras = {}
        for w in v:gmatch("%S+") do palabras[#palabras + 1] = norm(w) end
        if #palabras > 0 and #v >= 4 then
          terminos[#terminos + 1] = {palabras = palabras, id = id, def = def, titulo = tit}
        end
      end
    end
  end
  table.sort(terminos, function(a, b) return #a.palabras > #b.palabras end)
end

local PUNTC = "[%.,;:!%?%)»”\"']+"
local PUNT = PUNTC .. "$"

local function procesar(inlines)
  local out = pandoc.Inlines{}
  local i = 1
  while i <= #inlines do
    local el = inlines[i]
    local hecho = false
    if el.t == "Str" then
      for _, t in ipairs(terminos) do
        if not usados[t.id] then
          -- intentar casar t.palabras desde i
          local j, k, ultimo = i, 1, nil
          local ok = true
          while k <= #t.palabras do
            local e = inlines[j]
            if not e or e.t ~= "Str" then ok = false break end
            local txt = e.text
            local tiene_prefijo = txt:match("^[«“\"%(¿¡]") ~= nil
            local tiene_punt = txt:match(PUNT) ~= nil
            if k > 1 and tiene_prefijo then ok = false break end
            if k < #t.palabras and tiene_punt then ok = false break end
            local limpio = txt:gsub(PUNT, "")
            limpio = limpio:gsub("^[«“\"%(¿¡]+", "")
            local w, q = norm(limpio), t.palabras[k]
            if w ~= q and w ~= q .. "s" and w ~= q .. "es" then ok = false break end
            ultimo = j
            k = k + 1
            if k <= #t.palabras then
              local s = inlines[j + 1]
              if not s or (s.t ~= "Space" and s.t ~= "SoftBreak") then ok = false break end
              j = j + 2
            end
          end
          if ok and ultimo then
            usados[t.id] = true
            local prefijo = inlines[i].text:match("^([«“\"%(¿¡]*)") or ""
            local sufijo = inlines[ultimo].text:match("(" .. PUNTC .. ")$") or ""
            local contenido = pandoc.Inlines{}
            for m = i, ultimo do contenido:insert(inlines[m]:clone()) end
            contenido[1].text = contenido[1].text:sub(#prefijo + 1)
            if #sufijo > 0 then contenido[#contenido].text = contenido[#contenido].text:sub(1, -#sufijo - 1) end
            if #prefijo > 0 then out:insert(pandoc.Str(prefijo)) end
            out:insert(pandoc.Link(contenido, "92-glosario.html#" .. t.id, "", pandoc.Attr("", {"glos"}, {{"data-def", t.def}})))
            if #sufijo > 0 then out:insert(pandoc.Str(sufijo)) end
            i = ultimo + 1
            hecho = true
            break
          end
        end
      end
    end
    if not hecho and (el.t == "Strong" or el.t == "Emph") then
      local txt = norm((pandoc.utils.stringify(el):gsub(PUNT, "")))
      for _, t in ipairs(terminos) do
        local plural = {}
        for n, q in ipairs(t.palabras) do plural[n] = q end
        local sing = table.concat(t.palabras, " ")
        if not usados[t.id] and (txt == sing or txt == sing .. "s" or txt == sing .. "es" or txt:gsub("^(%S+)s ", "%1 ", 1) == sing) then
          usados[t.id] = true
          out:insert(pandoc.Link({el}, "92-glosario.html#" .. t.id, "", pandoc.Attr("", {"glos"}, {{"data-def", t.def}})))
          i = i + 1
          hecho = true
          break
        end
      end
    end
    if not hecho then out:insert(el); i = i + 1 end
  end
  return out
end

local SCRIPT = [[
<style>a.glos{text-decoration:underline dotted;text-underline-offset:3px;color:inherit}a.glos:hover,a.glos:focus{color:var(--bs-link-color)}</style>
]]

return {
  {
    Pandoc = function(doc)
      if not quarto.doc.is_format("html") then return nil end
      local entrada = quarto.doc.input_file or ""
      if entrada:match("92%-glosario%.qmd$") or entrada:match("index%.qmd$") then return nil end
      cargar()
      if #terminos == 0 then return nil end
      doc.blocks = doc.blocks:walk({
        Para = function(p) p.content = procesar(p.content) return p end,
        Plain = function(p) p.content = procesar(p.content) return p end,
        Header = function(h) return h end,
      })
      quarto.doc.include_text("after-body", SCRIPT)
      return doc
    end
  }
}
