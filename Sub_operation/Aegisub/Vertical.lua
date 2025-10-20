-- MulticolorV_Position.lua
-- Dégradé vertical fluide basé sur position Y (haut -> bas)
-- Par GPT (2025)
-- Version : 1.0

script_name = "MulticolorV (Vertical par position)"
script_description = "Dégradé vertical fluide basé sur la position à l'écran"
script_author = "GPT"
script_version = "1.0"

-- Conversion hex → RGB
local function hex2rgb(hex)
    if type(hex) ~= "string" then return 255,255,255 end
    local r,g,b = hex:match("#(%x%x)(%x%x)(%x%x)")
    if r and g and b then
        return tonumber(r,16), tonumber(g,16), tonumber(b,16)
    end
    return 255,255,255
end

-- RGB → ASS (&HBBGGRR&)
local function rgb2ass(r,g,b)
    return string.format("&H%02X%02X%02X&", b,g,r)
end

-- interpolation linéaire
local function lerp(a,b,t) return a+(b-a)*t end

-- Cherche les bornes de hauteur globale (y min, y max)
local function find_global_bounds(subs, sel)
    local y_min, y_max = 1e9, -1e9
    for _, i in ipairs(sel) do
        local line = subs[i]
        local text = line.text or ""
        local px, py = text:match("\\pos%(([%d%.%-]+),%s*([%d%.%-]+)%)")
        if py then
            py = tonumber(py)
        else
            py = 540 -- milieu par défaut
        end
        y_min = math.min(y_min, py)
        y_max = math.max(y_max, py)
    end
    return y_min, y_max
end

function apply_gradient_vertical(subs, sel)
    -- boîte de dialogue
    local main_dialog = {
        {class="label", label="Tag à colorer :", x=0, y=0},
        {class="dropdown", name="tag", items={"\\c","\\2c","\\3c","\\4c"}, value="\\c", x=1, y=0},
        {class="label", label="Nombre de couleurs :", x=0, y=1},
        {class="intedit", name="ncolors", value=2, min=2, max=10, x=1, y=1}
    }
    local pressed, res = aegisub.dialog.display(main_dialog, {"Suivant", "Annuler"})
    if pressed ~= "Suivant" then return end

    local n = res.ncolors
    local color_dialog = {}
    for i=1,n do
        table.insert(color_dialog, {class="label", label="Couleur "..i..":", x=0, y=i-1})
        table.insert(color_dialog, {class="color", name="col"..i, x=1, y=i-1, value="#FFFFFF"})
    end
    local pressed2, cols = aegisub.dialog.display(color_dialog, {"Appliquer","Annuler"})
    if pressed2 ~= "Appliquer" then return end

    local colors = {}
    for i=1,n do
        table.insert(colors, cols["col"..i])
    end

    -- Déterminer plage verticale globale
    local y_min, y_max = find_global_bounds(subs, sel)
    local y_range = math.max(1, y_max - y_min)

    for _, i in ipairs(sel) do
        local line = subs[i]
        local text = line.text

        -- Récupération pos Y
        local px, py = text:match("\\pos%(([%d%.%-]+),%s*([%d%.%-]+)%)")
        if py then
            py = tonumber(py)
        else
            py = 540
        end

        -- Progression verticale (0 en haut → 1 en bas)
        local t = (py - y_min) / y_range
        if t < 0 then t = 0 elseif t > 1 then t = 1 end

        -- Trouve segment couleur
        local step = t * (n-1)
        local idx = math.floor(step) + 1
        local frac = step - math.floor(step)
        if idx >= n then idx = n-1; frac = 1 end

        -- Interpolation couleurs
        local r1,g1,b1 = hex2rgb(colors[idx])
        local r2,g2,b2 = hex2rgb(colors[idx+1])
        local r = math.floor(lerp(r1,r2,frac))
        local g = math.floor(lerp(g1,g2,frac))
        local b = math.floor(lerp(b1,b2,frac))
        local col = rgb2ass(r,g,b)

        -- Ajout du tag couleur (avant le texte principal)
        -- Supprime tags précédents du même type
        local clean = text:gsub(res.tag.."&H%x+&","")
        line.text = string.format("{%s%s}%s", res.tag, col, clean)
        subs[i] = line
    end
end

aegisub.register_macro(script_name, script_description, apply_gradient_vertical)
