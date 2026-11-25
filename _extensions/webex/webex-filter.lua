-- Filtro de webex: botón de las soluciones plegables y dependencias.
local function deps()
  quarto.doc.add_html_dependency({
    name = "webex",
    version = "1.2.0",
    stylesheets = {"resources/webex.css"},
    scripts = {{ path = "resources/webex.js", afterBody = true }}
  })
end

local function Div(el)
  if not quarto.doc.is_format("html") then return nil end
  if el.classes:includes("webex-solution") then
    deps()
    local label = el.attributes["boton"] or "Ver solución"
    el.attributes["boton"] = nil
    el.content:insert(1, pandoc.RawBlock("html", "<button>" .. label .. "</button>"))
    return el
  end
  if el.classes:includes("webex-check") then deps() end
end

return { { Div = Div } }
