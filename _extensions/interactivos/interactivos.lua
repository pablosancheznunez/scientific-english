--[[
Interactivos para los libros: actividades de corrección inmediata escritas en
Markdown. En HTML se convierten en componentes accesibles (teclado y lector de
pantalla); en PDF y EPUB, en una versión para papel con su solución.

  ::: {.ordenar #id titulo="…"}            lista numerada en el orden correcto
  ::: {.clasificar #id titulo="…" categorias="A|B|C"}
      - elemento → categoría // explicación opcional
  ::: {.zonas #id titulo="…" imagen="figuras/x.svg" alt="…"}
      - [x, y, ancho, alto] Descripción de la zona | si | Explicación
        (coordenadas en % de la imagen; «si» marca las zonas que hay que elegir)
  ::: {.escenario #id titulo="…"}
      ### Paso {#id-paso}           primer paso = inicio
      Texto. - [Opción](#otro-paso)
      ### Final {#id-fin .final .bien}  (o .mal / .regular)

Los bloques que siguen a la lista (en ordenar, clasificar y zonas) son la
explicación general que aparece al resolver la actividad.
]]

local TIPOS = { ordenar = true, clasificar = true, zonas = true, escenario = true }

local function es_html()
  return quarto.doc.is_format("html") and not quarto.doc.is_format("epub")
end

local function html(blocks)
  if blocks == nil or #blocks == 0 then return "" end
  local s = pandoc.write(pandoc.Pandoc(blocks), "html")
  return (s:gsub("^%s+", ""):gsub("%s+$", ""))
end

local function md(blocks)
  return pandoc.write(pandoc.Pandoc(blocks), "markdown", { wrap_text = "none" })
end

local function desde_md(texto)
  return pandoc.read(texto, "markdown").blocks
end

local function html_md(texto)
  local h = html(desde_md(texto))
  -- un solo párrafo: sin <p> envolvente
  local unico = h:match("^<p>(.-)</p>$")
  if unico and not unico:find("<p>") then return unico end
  return h
end

local function trim(s) return (s:gsub("^%s+", ""):gsub("%s+$", "")) end

local function tipo_de(el)
  for _, c in ipairs(el.classes) do if TIPOS[c] then return c end end
  return nil
end

-- separa: bloques previos (enunciado), primera lista, bloques posteriores (explicación)
local function partir(el)
  local antes, lista, despues = {}, nil, {}
  for _, b in ipairs(el.content) do
    if lista == nil and (b.t == "BulletList" or b.t == "OrderedList") then
      lista = b
    elseif lista == nil then
      table.insert(antes, b)
    else
      table.insert(despues, b)
    end
  end
  return antes, lista, despues
end

local function json_script(datos)
  local j = quarto.json.encode(datos):gsub("</", "<\\/")
  return '<script type="application/json" class="ia-datos">' .. j .. '</script>'
end

local function contenedor(tipo, el, datos)
  quarto.doc.add_html_dependency({
    name = "interactivos", version = "1.0.0",
    scripts = { "interactivos.js" }, stylesheets = { "interactivos.css" },
  })
  local id = el.identifier ~= "" and el.identifier or ("ia-" .. tipo .. "-" .. tostring(math.random(1e6)))
  datos.tipo = tipo
  datos.titulo = el.attributes["titulo"] or ""
  return pandoc.RawBlock("html",
    '<div class="ia ia-' .. tipo .. '" id="' .. id .. '">' .. json_script(datos) ..
    '<p class="ia-sinjs">Esta actividad necesita JavaScript.</p></div>')
end

-- ---------------------------------------------------------------- versión para papel
local EN = false
local function tr(es, en) if EN then return en end return es end

local function caja(titulo, blocks, tipo)
  return quarto.Callout({ type = tipo or "note", title = titulo, content = pandoc.Blocks(blocks), collapse = false })
end

local function orden_estable(items)
  -- desordena de forma reproducible (por texto) para la versión impresa
  local copia = {}
  for i, v in ipairs(items) do copia[i] = { i = i, v = v, k = pandoc.utils.stringify(v) } end
  table.sort(copia, function(a, b) return a.k < b.k end)
  return copia
end

-- ---------------------------------------------------------------- ordenar
local function ordenar(el)
  local antes, lista, despues = partir(el)
  if not lista then return nil end
  local titulo = el.attributes["titulo"] or "Ordena"
  if es_html() then
    local items = {}
    for _, it in ipairs(lista.content) do table.insert(items, html_md(md(it))) end
    return contenedor("ordenar", el, { enunciado = html(antes), items = items, explicacion = html(despues) })
  end
  local mezcla = orden_estable(lista.content)
  local desorden = {}
  for _, x in ipairs(mezcla) do table.insert(desorden, x.v) end
  local blocks = {}
  for _, b in ipairs(antes) do table.insert(blocks, b) end
  table.insert(blocks, pandoc.BulletList(desorden))
  local sol = { pandoc.OrderedList(lista.content) }
  for _, b in ipairs(despues) do table.insert(sol, b) end
  return { caja(tr("Actividad: ", "Activity: ") .. titulo, blocks), caja(tr("Solución", "Solution"), sol, "tip") }
end

-- ---------------------------------------------------------------- clasificar
local function clasificar(el)
  local antes, lista, despues = partir(el)
  if not lista then return nil end
  local titulo = el.attributes["titulo"] or "Clasifica"
  local cats, vistos, items = {}, {}, {}
  if el.attributes["categorias"] then
    for c in (el.attributes["categorias"] .. "|"):gmatch("(.-)|") do
      c = trim(c); if c ~= "" and not vistos[c] then table.insert(cats, c); vistos[c] = true end
    end
  end
  for _, it in ipairs(lista.content) do
    local t = md(it)
    local izq, resto = t:match("^(.-)%s*→%s*(.*)$")
    if not izq then izq, resto = t, "" end
    local cat, expl = resto:match("^(.-)%s*//%s*(.*)$")
    if not cat then cat, expl = resto, "" end
    cat = trim(pandoc.utils.stringify(desde_md(cat)))
    if cat ~= "" and not vistos[cat] then table.insert(cats, cat); vistos[cat] = true end
    table.insert(items, { md = trim(izq), cat = cat, expl = trim(expl) })
  end
  if es_html() then
    local datos = { enunciado = html(antes), categorias = cats, items = {}, explicacion = html(despues) }
    for _, x in ipairs(items) do
      table.insert(datos.items, { texto = html_md(x.md), categoria = x.cat, explicacion = x.expl ~= "" and html_md(x.expl) or "" })
    end
    return contenedor("clasificar", el, datos)
  end
  local blocks = {}
  for _, b in ipairs(antes) do table.insert(blocks, b) end
  table.insert(blocks, pandoc.Para({ pandoc.Strong({ pandoc.Str("Categorías: ") }), pandoc.Str(table.concat(cats, " · ")) }))
  local lineas = {}
  for _, x in ipairs(items) do table.insert(lineas, desde_md(x.md)) end
  table.insert(blocks, pandoc.BulletList(lineas))
  local sol = {}
  for _, x in ipairs(items) do
    local linea = x.md .. " → **" .. x.cat .. "**" .. (x.expl ~= "" and (". " .. x.expl) or "")
    table.insert(sol, desde_md(linea))
  end
  local sb = { pandoc.BulletList(sol) }
  for _, b in ipairs(despues) do table.insert(sb, b) end
  return { caja(tr("Actividad: ", "Activity: ") .. titulo, blocks), caja(tr("Solución", "Solution"), sb, "tip") }
end

-- ---------------------------------------------------------------- zonas
local function zonas(el)
  local antes, lista, despues = partir(el)
  if not lista then return nil end
  local titulo = el.attributes["titulo"] or "Elige las zonas"
  local imagen, alt = el.attributes["imagen"] or "", el.attributes["alt"] or ""
  local zs = {}
  for _, it in ipairs(lista.content) do
    local t = md(it):gsub("\\%[", "["):gsub("\\%]", "]"):gsub("\\|", "|")
    local x, y, w, h, resto = t:match("^%s*%[%s*([%d%.]+)%s*,%s*([%d%.]+)%s*,%s*([%d%.]+)%s*,%s*([%d%.]+)%s*%]%s*(.*)$")
    if x then
      local desc, marca, expl = resto:match("^(.-)%s*|%s*(%a+)%s*|%s*(.*)$")
      if not desc then desc, marca, expl = resto, "no", "" end
      table.insert(zs, { x = tonumber(x), y = tonumber(y), w = tonumber(w), h = tonumber(h),
        md = trim(desc), correcta = (marca:lower() == "si" or marca:lower() == "sí"), expl = trim(expl) })
    end
  end
  if es_html() then
    local datos = { enunciado = html(antes), imagen = imagen, alt = alt, zonas = {}, explicacion = html(despues) }
    for _, z in ipairs(zs) do
      table.insert(datos.zonas, { x = z.x, y = z.y, w = z.w, h = z.h, descripcion = pandoc.utils.stringify(desde_md(z.md)),
        correcta = z.correcta, explicacion = z.expl ~= "" and html_md(z.expl) or "" })
    end
    return contenedor("zonas", el, datos)
  end
  local blocks = {}
  for _, b in ipairs(antes) do table.insert(blocks, b) end
  if imagen ~= "" then
    table.insert(blocks, pandoc.Para({ pandoc.Image({ pandoc.Str("") }, imagen, "", pandoc.Attr("", {}, { { "fig-alt", alt } })) }))
  end
  local opciones, sol = {}, {}
  for i, z in ipairs(zs) do
    table.insert(opciones, desde_md(z.md))
    table.insert(sol, desde_md(z.md .. ": " .. (z.correcta and "**sí**" or "no") .. (z.expl ~= "" and (". " .. z.expl) or "")))
  end
  table.insert(blocks, pandoc.OrderedList(opciones))
  local sb = { pandoc.OrderedList(sol) }
  for _, b in ipairs(despues) do table.insert(sb, b) end
  return { caja(tr("Actividad: ", "Activity: ") .. titulo, blocks), caja(tr("Solución", "Solution"), sb, "tip") }
end

-- ---------------------------------------------------------------- escenario
local function escenario(el)
  local titulo = el.attributes["titulo"] or "Escenario"
  local nodos, orden, actual, intro = {}, {}, nil, {}
  for _, b in ipairs(el.content) do
    if b.t == "Header" then
      actual = { id = b.identifier, titulo = pandoc.utils.stringify(b.content), bloques = {}, opciones = {},
        final = b.classes:includes("final"),
        valor = (b.classes:includes("bien") and "bien") or (b.classes:includes("mal") and "mal") or
                (b.classes:includes("regular") and "regular") or "" }
      nodos[actual.id] = actual; table.insert(orden, actual)
    elseif actual == nil then
      table.insert(intro, b)
    elseif b.t == "BulletList" then
      for _, it in ipairs(b.content) do
        local destino, texto = nil, nil
        pandoc.walk_block(pandoc.Div(it), { Link = function(l)
          if l.target:sub(1, 1) == "#" and not destino then destino = l.target:sub(2); texto = l.content end
        end })
        if destino then table.insert(actual.opciones, { destino = destino, texto = texto }) end
      end
    else
      table.insert(actual.bloques, b)
    end
  end
  if #orden == 0 then return nil end
  if es_html() then
    local datos = { enunciado = html(intro), inicio = orden[1].id, nodos = {} }
    for _, n in ipairs(orden) do
      local ops = {}
      for _, o in ipairs(n.opciones) do table.insert(ops, { destino = o.destino, texto = html({ pandoc.Plain(o.texto) }) }) end
      datos.nodos[n.id] = { titulo = n.titulo, texto = html(n.bloques), opciones = ops, final = n.final, valor = n.valor }
    end
    return contenedor("escenario", el, datos)
  end
  -- papel: pasos numerados con «ve al paso N»
  local num = {}
  for i, n in ipairs(orden) do num[n.id] = i end
  local blocks = {}
  for _, b in ipairs(intro) do table.insert(blocks, b) end
  for i, n in ipairs(orden) do
    local cab = { pandoc.Strong({ pandoc.Str(tostring(i) .. ". " .. n.titulo) }) }
    if n.final then
      local etiqueta = (EN and { bien = " (good ending)", mal = " (bad ending)", regular = " (could be better)" } or { bien = " (buen final)", mal = " (mal final)", regular = " (final mejorable)" })[n.valor] or ""
      table.insert(cab, pandoc.Emph({ pandoc.Str(etiqueta) }))
    end
    table.insert(blocks, pandoc.Para(cab))
    for _, b in ipairs(n.bloques) do table.insert(blocks, b) end
    local ops = {}
    for _, o in ipairs(n.opciones) do
      local linea = {}
      for _, x in ipairs(o.texto) do table.insert(linea, x) end
      table.insert(linea, pandoc.Str(tr(" → paso ", " → step ") .. tostring(num[o.destino] or "?")))
      table.insert(ops, { pandoc.Plain(linea) })
    end
    if #ops > 0 then table.insert(blocks, pandoc.BulletList(ops)) end
  end
  return caja(tr("Escenario: ", "Scenario: ") .. titulo, blocks)
end

local F = { ordenar = ordenar, clasificar = clasificar, zonas = zonas, escenario = escenario }

return {
  {
    Meta = function(m)
      local l = m.lang and pandoc.utils.stringify(m.lang) or ""
      EN = l:sub(1, 2) == "en"
    end,
  },
  {
    Div = function(el)
      local t = tipo_de(el)
      if t then return F[t](el) end
    end,
  },
}
