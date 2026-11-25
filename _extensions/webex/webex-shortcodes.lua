-- Preguntas autoevaluables con el marcado de webexercises (PsyTeachR),
-- generadas sin R para usarlas con engine: markdown.
--   {{< torf true >}}                         verdadero/falso
--   {{< mcq "*correcta" "otra" "otra" >}}      desplegable (el * marca la correcta)
--   {{< longmcq "*correcta" "otra" >}}         opciones en lista (botones de radio)
--   {{< fitb "respuesta" "alternativa" >}}     hueco (ignorecase=true, width=, tol=)
-- Bloques:
--   ::: {.webex-check .webex-box} ... :::      grupo con botón «Mostrar respuestas»
--   ::: {.webex-solution} ... :::              solución plegable

local counter = 0

local function deps()
  quarto.doc.add_html_dependency({
    name = "webex",
    version = "1.2.0",
    stylesheets = {"resources/webex.css"},
    scripts = {{ path = "resources/webex.js", afterBody = true }}
  })
end

local function esc(s)
  s = s:gsub("&", "&amp;"):gsub("<", "&lt;"):gsub(">", "&gt;"):gsub("'", "&apos;"):gsub('"', "&quot;")
  return s
end

local function str(x) return pandoc.utils.stringify(x) end

local function options(args)
  local opts = {}
  for _, a in ipairs(args) do
    local t = str(a)
    local correct = false
    if t:sub(1,1) == "*" then correct = true; t = t:sub(2) end
    table.insert(opts, { text = t, correct = correct })
  end
  return opts
end

local function es_html() return quarto.doc.is_format("html") end

local function raw(html)
  deps()
  return pandoc.RawInline("html", html)
end

local function texto(t) return pandoc.Inlines({ pandoc.Space(), pandoc.Emph(pandoc.Str(t)) }) end

local EN = false
local function fija_idioma(meta)
  EN = meta ~= nil and meta.lang ~= nil and pandoc.utils.stringify(meta.lang):sub(1, 2) == "en"
end
local function tr(es, en) if EN then return en end return es end

local function select_html(opts)
  local o = { "<select class='webex-select' aria-label='" .. tr("Elige una respuesta", "Choose an answer") .. "'><option value='blank'></option>" }
  for _, op in ipairs(opts) do
    table.insert(o, string.format("<option value='%s'>%s</option>", op.correct and "answer" or "x", esc(op.text)))
  end
  table.insert(o, "</select>")
  return table.concat(o)
end

local function torf(args, kwargs, meta)
  fija_idioma(meta)
  if not es_html() then return texto(tr("[ V / F ]", "[ T / F ]")) end
  local ans = str(args[1] or ""):lower()
  local v = (ans == "true" or ans == "verdadero" or ans == "v")
  return raw(select_html({ { text = tr("VERDADERO", "TRUE"), correct = v }, { text = tr("FALSO", "FALSE"), correct = not v } }))
end

local function mcq(args, kwargs, meta)
  fija_idioma(meta)
  local opts = options(args)
  if not es_html() then
    local t = {}
    for _, op in ipairs(opts) do table.insert(t, op.text) end
    return texto("[ " .. table.concat(t, " / ") .. " ]")
  end
  return raw(select_html(opts))
end

local function longmcq(args, kwargs, meta)
  fija_idioma(meta)
  if not es_html() then
    local t = {}
    for k, op in ipairs(options(args)) do table.insert(t, "(" .. string.char(96 + k) .. ") " .. op.text) end
    return texto(table.concat(t, "   "))
  end
  counter = counter + 1
  local qname = "radio_libro_" .. counter
  local o = { "<div class='webex-radiogroup' role='radiogroup' aria-label='" .. tr("Opciones de respuesta", "Answer options") .. "' id='" .. qname .. "'>" }
  for _, op in ipairs(options(args)) do
    table.insert(o, string.format('<label><input type="radio" autocomplete="off" name="%s" value="%s"></input> <span>%s</span></label>',
      qname, op.correct and "answer" or "x", esc(op.text)))
  end
  table.insert(o, "</div>")
  return raw(table.concat(o))
end

local function fitb(args, kwargs, meta)
  fija_idioma(meta)
  if not es_html() then return pandoc.Inlines({ pandoc.Space(), pandoc.Str("______________") }) end
  local answers, width = {}, 0
  for _, a in ipairs(args) do
    local t = str(a)
    table.insert(answers, '"' .. t:gsub('\\', '\\\\'):gsub('"', '\\"') .. '"')
    width = math.max(width, #t)
  end
  local cls = "webex-solveme nospaces"
  if str(kwargs["ignorecase"] or "") == "true" then cls = cls .. " ignorecase" end
  local w = str(kwargs["width"] or "")
  if w ~= "" then width = tonumber(w) end
  local tol = str(kwargs["tol"] or "")
  local tolattr = tol ~= "" and (" data-tol='" .. tol .. "'") or ""
  local json = "[" .. table.concat(answers, ",") .. "]"
  return raw(string.format("<input class='%s'%s size='%d' aria-label='" .. tr("Escribe tu respuesta", "Type your answer") .. "' data-answer='%s'/>", cls, tolattr, math.max(width, 3) + 2, json:gsub("'", "&apos;")))
end

return {
  ["torf"] = torf,
  ["mcq"] = mcq,
  ["longmcq"] = longmcq,
  ["fitb"] = fitb
}
