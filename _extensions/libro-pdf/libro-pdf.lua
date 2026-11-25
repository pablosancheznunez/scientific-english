-- Adapta el libro a la versión impresa (PDF con Typst):
--  * celdas {webr}: muestra el código; oculta preparación y comprobación;
--    los ejercicios aparecen con su título y huecos.
--  * pistas y soluciones de los ejercicios: recuadros.
--  * soluciones de la autoevaluación: recuadro «Explicaciones».
--  * enlaces entre capítulos: anclas internas; descargas: URL de la web.

-- La web y el ancla de cada capítulo llegan en los metadatos «libro-pdf»
-- (los escribe herramientas/pdf.py).
local WEB = ""
local EN = false
local function tr(es, en) if EN then return en end return es end
local CAP = {}

local function leer_meta(meta)
  local m = meta["libro-pdf"]
  if not m then return nil end
  WEB = pandoc.utils.stringify(m.web or "")
  EN = (meta.lang and pandoc.utils.stringify(meta.lang) or ""):sub(1, 2) == "en"
  if m.capitulos then
    for k, v in pairs(m.capitulos) do CAP[k] = pandoc.utils.stringify(v) end
  end
  return nil
end

local function es_webr(el)
  for _, c in ipairs(el.classes) do
    if c == "webr" or c == "{webr}" then return true end
  end
  return false
end

local function callout(tipo, titulo, contenido)
  return quarto.Callout({ type = tipo, title = titulo, content = contenido, collapse = false })
end

function CodeBlock(el)
  for _, c in ipairs(el.classes) do
    if c == "ojs" or c == "{ojs}" then return {} end
  end
  if not es_webr(el) then return nil end
  local opts, code = {}, {}
  for line in (el.text .. "\n"):gmatch("(.-)\n") do
    if line:match("^#|") then table.insert(opts, line) else table.insert(code, line) end
  end
  local o = table.concat(opts, " ")
  if o:match("setup:%s*true") or o:match("check:%s*true") then return {} end
  if o:match("input:") then
    return callout("note", tr("Gráfica interactiva", "Interactive chart"), pandoc.Blocks({ pandoc.Para({ pandoc.Str(tr("Esta gráfica es interactiva en la versión web: ", "This chart is interactive in the web version: ")),
      pandoc.Link((WEB:gsub("^https?://", ""):gsub("/$", "")), WEB) }) }))
  end
  local texto = table.concat(code, "\n"):gsub("^%s*\n", ""):gsub("\n%s*$", "")
  local bloque = pandoc.CodeBlock(texto, pandoc.Attr("", { "r" }))
  if o:match("exercise:") then
    return callout("note", tr("Ejercicio: completa los huecos ______", "Exercise: fill in the blanks ______"), pandoc.Blocks({ bloque }))
  end
  return bloque
end

function Div(el)
  if el.classes:includes("hint") and el.attributes["exercise"] then
    return callout("note", tr("Pista", "Hint"), el.content)
  end
  if (el.classes:includes("solution") or el.classes:includes("solucion-ejercicio")) and el.attributes["exercise"] then
    return callout("tip", tr("Solución", "Solution"), el.content)
  end
  if el.classes:includes("laboratorio") then
    local c = pandoc.Blocks({})
    for _, b in ipairs(el.content) do
      if not (b.t == "Div" and b.classes:includes("laboratorio-etiqueta")) then c:insert(b) end
    end
    c:insert(pandoc.Para({ pandoc.Str(tr("Este laboratorio es interactivo en la versión web: ", "This lab is interactive in the web version: ")),
      pandoc.Link((WEB:gsub("^https?://", ""):gsub("/$", "")), WEB) }))
    return callout("note", tr("Laboratorio interactivo", "Interactive lab"), c)
  end
  if el.classes:includes("webex-solution") then
    return callout("tip", tr("Explicaciones", "Explanations"), el.content)
  end
end

function Link(el)
  local t = el.target
  if t:match("^https?://") or t:match("^mailto:") then return nil end
  local file, anchor = t:match("^([^#]*)#?(.*)$")
  if CAP[file] then
    local destino = anchor ~= "" and anchor or CAP[file]
    if destino ~= "" then el.target = "#" .. destino else el.target = WEB .. file:gsub("%.qmd$", ".html") end
    return el
  end
  if file:match("^plantillas/") or file:match("^datos/") then
    el.target = WEB .. file
    el.classes = {}
    el.attributes = {}
    return el
  end
end

return {
  { Meta = leer_meta },
  { CodeBlock = CodeBlock, Div = Div, Link = Link },
}
