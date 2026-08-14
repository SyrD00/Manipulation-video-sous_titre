-- MulticolorHV_degrade_equitable.lua
-- Dégradé multicolore équitablement réparti (chaque segment = même nombre de caractères)


--[[
MulticolorHV (Dégradé équitable) - Documentation

Ce script Aegisub applique un dégradé multicolore horizontal ou vertical sur les sous-titres,
avec une répartition parfaitement équitable des couleurs choisies par l'utilisateur.

PRINCIPE :
- Le texte est divisé en segments égaux (autant que le nombre de transitions entre couleurs).
- Chaque segment applique un dégradé entre deux couleurs consécutives, sur un nombre de caractères identique.
- Les balises ASS ({...}), espaces et caractères spéciaux ne sont pas colorés.
- Seuls les caractères "visibles" sont colorés.

FONCTIONNALITÉS :
- Interface utilisateur pour choisir le nombre de couleurs (2 à 10) et leurs valeurs.
- Choix du tag de couleur à appliquer (\c, \2c, \3c, \4c).
- Gestion automatique des balises et espaces.
- Mémorisation des derniers paramètres utilisés.
- Compatible Aegisub Automation 4 Lua.

UTILISATION :
1. Sélectionnez une ou plusieurs lignes de sous-titres dans Aegisub.
2. Lancez le script via le menu Automation.
3. Choisissez le type de dégradé, le tag de couleur, le nombre de couleurs et leurs valeurs.
4. Validez : le dégradé sera appliqué de façon parfaitement équilibrée sur les caractères visibles.

ALGORITHME :
- Les caractères visibles sont identifiés (hors balises et espaces).
- Le texte est découpé en (n-1) segments pour n couleurs.
- Chaque segment reçoit un dégradé Lab entre deux couleurs, sur un nombre de caractères aussi égal que possible.
- Les transitions sont douces et chaque couleur "domine" une portion équivalente du texte.

AUTEUR :
- GPT (2024)
- Version : 3.0

]]


-- MulticolorHV_degrade_equitable_glow.lua

script_name = "MulticolorHV "
script_description = "Dégradé qui force les couleurs choisies même sur texte court"
script_author = "GPT"
script_version = "8.2 FIX \\N"

--------------------------------------------------
-- UTF8 split
--------------------------------------------------
local function utf8_to_table(str)
    local t = {}
    for c in str:gmatch("[%z\1-\127\194-\244][\128-\191]*") do
        table.insert(t, c)
    end
    return t
end

--------------------------------------------------
-- HEX → RGB
--------------------------------------------------
local function hex2rgb(hex)
    if type(hex) ~= "string" then
        return 255,255,255
    end
    local r,g,b = hex:match("#(%x%x)(%x%x)(%x%x)")
    if r and g and b then
        return tonumber(r,16), tonumber(g,16), tonumber(b,16)
    end
    return 255,255,255
end

--------------------------------------------------
-- RGB → ASS
--------------------------------------------------
local function rgb2ass(r,g,b)
    return string.format("&H%02X%02X%02X&", b,g,r)
end

--------------------------------------------------
-- interpolation
--------------------------------------------------
local function lerp(a,b,t)
    return a + (b-a)*t
end

--------------------------------------------------
-- RGB → Lab
--------------------------------------------------
local function rgb2lab(r,g,b)
    r,g,b = r/255,g/255,b/255
    local function invgamma(u)
        return (u>0.04045) and ((u+0.055)/1.055)^2.4 or u/12.92
    end
    r,g,b = invgamma(r),invgamma(g),invgamma(b)
    local x = (r*0.4124 + g*0.3576 + b*0.1805) / 0.95047
    local y = (r*0.2126 + g*0.7152 + b*0.0722) / 1.00000
    local z = (r*0.0193 + g*0.1192 + b*0.9505) / 1.08883
    local function f(t)
        return (t>0.008856) and t^(1/3) or (7.787*t + 16/116)
    end
    local L = 116*f(y) - 16
    local A = 500*(f(x)-f(y))
    local B = 200*(f(y)-f(z))
    return L,A,B
end

--------------------------------------------------
-- Lab → RGB
--------------------------------------------------
local function lab2rgb(L,A,B)
    local y = (L+16)/116
    local x = A/500 + y
    local z = y - B/200
    local function f(t)
        return (t^3 > 0.008856) and t^3 or (t-16/116)/7.787
    end
    x,y,z = f(x)*0.95047, f(y)*1.00000, f(z)*1.08883
    local r = x* 3.2406 + y*-1.5372 + z*-0.4986
    local g = x*-0.9689 + y* 1.8758 + z* 0.0415
    local b = x* 0.0557 + y*-0.2040 + z* 1.0570
    local function gamma(u)
        return (u>0.0031308) and (1.055*u^(1/2.4)-0.055) or 12.92*u
    end
    r,g,b = gamma(r),gamma(g),gamma(b)
    r = math.max(0, math.min(255, r*255))
    g = math.max(0, math.min(255, g*255))
    b = math.max(0, math.min(255, b*255))
    return math.floor(r),math.floor(g),math.floor(b)
end

--------------------------------------------------
-- CONFIG
--------------------------------------------------
local config_path = aegisub.decode_path("?data/MulticolorHV_glow_config.lua")
local config = {
    mode = "Horizontal",
    tag = "\\3c",
    ncolors = 2,
    blur = 6,
    glow = true,
    colors = {"#FFFFFF","#FFFFFF"}
}

local f = io.open(config_path,"r")
if f then
    f:close()
    local ok,loaded = pcall(dofile,config_path)
    if ok and loaded then config = loaded end
end

--------------------------------------------------
-- SCRIPT
--------------------------------------------------
function apply_gradient_equitable(subs, sel)

    local main_dialog = {
        {class="label",label="Type de dégradé",x=0,y=0},
        {class="dropdown", name="mode", items={"Horizontal","Vertical"}, value=config.mode, x=1,y=0},
        {class="label",label="Tag à colorer",x=0,y=1},
        {class="dropdown", name="tag", items={"\\c","\\2c","\\3c","\\4c"}, value=config.tag, x=1,y=1},
        {class="label",label="Nombre de couleurs",x=0,y=2},
        {class="intedit", name="ncolors", value=config.ncolors, min=1, max=10, x=1,y=2},
        {class="checkbox", name="glow", label="Activer glow", value=config.glow, x=0,y=3},
        {class="label",label="Glow blur",x=0,y=4},
        {class="floatedit", name="blur", value=config.blur, min=0, max=20, x=1,y=4}
    }

    local pressed,res = aegisub.dialog.display(main_dialog,{"Suivant","Annuler"})
    if pressed ~= "Suivant" then return end

    local n = res.ncolors

    local color_dialog = {}
    for i=1,n do
        table.insert(color_dialog, {class="label",label="Couleur "..i,x=0,y=i-1})
        table.insert(color_dialog, {class="color", name="col"..i, x=1, y=i-1, value=config.colors[i] or "#FFFFFF"})
    end

    local pressed2,cols = aegisub.dialog.display(color_dialog,{"Appliquer","Annuler"})
    if pressed2 ~= "Appliquer" then return end

    local colors = {}
    for i=1,n do table.insert(colors,cols["col"..i]) end

    config.mode = res.mode
    config.tag = res.tag
    config.ncolors = n
    config.blur = res.blur
    config.glow = res.glow
    config.colors = colors

    local f = io.open(config_path,"w")
    if f then
        f:write("return {\n")
        f:write(string.format("mode=%q,\n",config.mode))
        f:write(string.format("tag=%q,\n",config.tag))
        f:write(string.format("ncolors=%d,\n",config.ncolors))
        f:write(string.format("blur=%d,\n",config.blur))
        f:write(string.format("glow=%s,\n",tostring(config.glow)))
        f:write("colors={")
        for i,v in ipairs(config.colors) do
            f:write(string.format("%q",v))
            if i<#config.colors then f:write(",") end
        end
        f:write("}\n}")
        f:close()
    end

    local glow_tag = ""
    if res.glow and res.blur > 0 then
        glow_tag = "\\blur"..res.blur
    end

    for _,i in ipairs(sel) do
        local line = subs[i]
        local text = line.text
        local chars = utf8_to_table(text)

        local visibles = {}
        local in_tag = false

        for idx,c in ipairs(chars) do
            if c=="{" then in_tag=true end
            if not in_tag and c:match("%S") and c~="\\" then
                table.insert(visibles,idx)
            end
            if c=="}" then in_tag=false end
        end

        local len = #visibles

        if n == 1 then
            local r,g,b = hex2rgb(colors[1])
            local col = rgb2ass(r,g,b)

            local newtext = ""
            local in_tag_1 = false
            local idx = 1

            while idx <= #chars do
                local c = chars[idx]

                if c == "\\" and chars[idx+1] == "N" then
                    newtext = newtext .. "\\N"
                    idx = idx + 2

                elseif c=="{" then
                    in_tag_1=true
                    newtext = newtext .. c
                    idx = idx + 1

                elseif c=="}" then
                    in_tag_1=false
                    newtext = newtext .. c
                    idx = idx + 1

                elseif in_tag_1 then
                    newtext = newtext .. c
                    idx = idx + 1

                elseif c:match("%S") and c~="\\" then
                    newtext = newtext .. string.format("{%s%s%s}%s", res.tag, col, glow_tag, c)
                    idx = idx + 1

                else
                    newtext = newtext .. c
                    idx = idx + 1
                end
            end

            line.text = newtext
            subs[i] = line
            goto continue
        end

        if len < 2 then goto continue end

        -- MODE FORCE PALETTE :
        -- Au lieu de couper en segments fixes qui peuvent faire disparaitre la derniere couleur,
        -- on etire toutes les couleurs choisies sur l'ensemble des caracteres visibles.
        -- Exemple avec 5 couleurs et "BOOM!!" (6 caracteres visibles) :
        -- debut violet, bleu, rose, vert, fin jaune bien present.
        local newtext = ""
        local visible_ptr = 1
        in_tag = false
        local idx = 1

        while idx <= #chars do
            local c = chars[idx]

            if c == "\\" and chars[idx+1] == "N" then
                newtext = newtext .. "\\N"
                idx = idx + 2

            elseif c=="{" then
                in_tag=true
                newtext = newtext .. c
                idx = idx + 1

            elseif c=="}" then
                in_tag=false
                newtext = newtext .. c
                idx = idx + 1

            elseif in_tag then
                newtext = newtext .. c
                idx = idx + 1

            elseif c:match("%S") and c~="\\" then
                local col

                -- TEXTES COURTS : on respecte les couleurs choisies sans les melanger.
                -- Exemple BOOM!! avec 5 couleurs et 6 caracteres :
                -- B = couleur 1, O = couleur 2, O = couleur 3, M = couleur 4, ! = couleur 5, ! = couleur 5.
                -- Cela evite les couleurs sales/marron creees par les melanges Lab sur trop peu de lettres.
                if len <= n + 3 then
                    local color_idx = math.ceil(visible_ptr * n / len)
                    if color_idx < 1 then color_idx = 1 end
                    if color_idx > n then color_idx = n end

                    local r,g,b = hex2rgb(colors[color_idx])
                    col = rgb2ass(r,g,b)

                else
                    -- TEXTES LONGS : vrai degrade continu sur toute la palette.
                    local global_t = (visible_ptr - 1) / (len - 1)
                    local palette_pos = 1 + global_t * (n - 1)
                    local seg_idx = math.floor(palette_pos)
                    if seg_idx < 1 then seg_idx = 1 end
                    if seg_idx > n - 1 then seg_idx = n - 1 end

                    local t = palette_pos - seg_idx

                    local r1,g1,b1 = hex2rgb(colors[seg_idx])
                    local r2,g2,b2 = hex2rgb(colors[seg_idx+1])
                    local L1,a1,b1_lab = rgb2lab(r1,g1,b1)
                    local L2,a2,b2_lab = rgb2lab(r2,g2,b2)

                    local L = lerp(L1,L2,t)
                    local A = lerp(a1,a2,t)
                    local B = lerp(b1_lab,b2_lab,t)

                    local r,g,b = lab2rgb(L,A,B)
                    col = rgb2ass(r,g,b)
                end

                newtext = newtext .. string.format("{%s%s%s}%s", res.tag, col, glow_tag, c)

                visible_ptr = visible_ptr + 1
                idx = idx + 1

            else
                newtext = newtext .. c
                idx = idx + 1
            end
        end

        line.text = newtext
        subs[i] = line

        ::continue::
    end
end

aegisub.register_macro(script_name, script_description, apply_gradient_equitable)

--[[ 
Le code la fait pareil mais est tres legerement moins fluide que l'autre c-a d on passe plus 
rapidement d'une couleur a une autre


-- MulticolorHV.lua
-- Applique un dégradé multicolore (horizontal ou vertical) sur le texte sélectionné
-- Compatible Aegisub Automation 4 Lua

script_name = "MulticolorHV"
script_description = "Dégradé multicolore horizontal ou vertical"
script_author = "GPT"
script_version = "1.3"

local tr = aegisub.gettext

-- Fonction pour découper une chaîne UTF-8 en caractères
local function utf8_to_table(str)
    local t = {}
    for c in str:gmatch("[%z\1-\127\194-\244][\128-\191]*") do
        table.insert(t, c)
    end
    return t
end

-- Convertir couleur hex → RGB
local function hex2rgb(hex)
    if type(hex) ~= "string" then return 255,255,255 end
    local r,g,b = hex:match("#(%x%x)(%x%x)(%x%x)")
    if r and g and b then
        return tonumber(r,16), tonumber(g,16), tonumber(b,16)
    end
    return 255,255,255
end

-- Convertir RGB → couleur ASS (&HBBGGRR&)
local function rgb2ass(r,g,b)
    return string.format("&H%02X%02X%02X&", b,g,r)
end


-- Interpolation linéaire
local function lerp(a,b,t) return a+(b-a)*t end




function apply_gradient(subs, sel)
    -- Étape 1 : boîte de dialogue principale
    local main_dialog = {
        {class="label", label="Type de dégradé :", x=0, y=0},
        {class="dropdown", name="mode", items={"Horizontal","Vertical"}, value="Horizontal", x=1, y=0},
        {class="label", label="Tag à colorer :", x=0, y=2},
        {class="dropdown", name="tag", items={"\\c","\\2c","\\3c","\\4c"}, value="\\c", x=1, y=2},

        {class="label", label="Nombre de couleurs :", x=0, y=1},
        {class="intedit", name="ncolors", value=2, min=2, max=10, x=1, y=1},
    }
    local btns = {"Suivant", "Annuler"}
    local pressed, res = aegisub.dialog.display(main_dialog, btns)
    if pressed ~= "Suivant" then return end

    local n = res.ncolors
    local mode = res.mode

    -- Étape 2 : boîte de dialogue pour sélectionner les couleurs
    local color_dialog = {}
    for i=1,n do
        table.insert(color_dialog, {class="label", label="Couleur "..i..":", x=0, y=i-1})
        table.insert(color_dialog, {class="color", name="col"..i, x=1, y=i-1, value="#FFFFFF"})
    end
    local btns2 = {"Appliquer", "Annuler"}
    local pressed2, cols = aegisub.dialog.display(color_dialog, btns2)
    if pressed2 ~= "Appliquer" then return end

    -- Extraire les couleurs choisies
    local colors = {}
    for i=1,n do
        table.insert(colors, cols["col"..i])
    end

    -- Étape 3 : appliquer le dégradé
    for _, i in ipairs(sel) do
        local line = subs[i]
        local text = line.text:gsub("{[^}]-}", "") -- texte sans tags

        local chars = utf8_to_table(text)
        local len = #chars
        local newtext = ""

        local j = 1
        while j <= len do
            local char = chars[j]

            -- Gestion des espaces normaux
            if char == " " or char == "\t" or char == "\r" then
                newtext = newtext .. char

            -- Gestion des séquences spéciales \N et \h
            elseif char == "\\" then
                local nextchar = chars[j+1]
                if nextchar == "N" or nextchar == "n" then
                    newtext = newtext .. "\\N"
                    j = j + 1
                elseif nextchar == "h" then
                    newtext = newtext .. "\\h"
                    j = j + 1
                else
                    newtext = newtext .. "\\"
                end

            -- Caractère normal : appliquer le dégradé
            else
                -- interpolation adoucie (ralentit le début, accélère à la fin)
                local function ease_in_out(t)
                    return t*t*(3-2*t)
                end

                -- Progression (0 → 1)
                --local t = (j-1)/(len-1)
            
                local t = ease_in_out((j-1)/(len-1))

           



                -- Trouver l’intervalle de couleurs
                local step = t * (n-1)
                local idx = math.floor(step) + 1
                local frac = step - math.floor(step)

                if idx >= n then
                    idx = n-1
                    frac = 1
                end

                -- Interpolation couleurs
                local r1,g1,b1 = hex2rgb(colors[idx])
                local r2,g2,b2 = hex2rgb(colors[idx+1])
                -- interpolation RGB.
                    local r = math.floor(lerp(r1,r2,frac))
                    local g = math.floor(lerp(g1,g2,frac))
                    local b = math.floor(lerp(b1,b2,frac))
                
                
              


                local col = rgb2ass(r,g,b)
                newtext = newtext .. string.format("{%s%s}%s",res.tag, col, char)
            end

            j = j + 1
        end

        line.text = newtext
        subs[i] = line
    end
end

aegisub.register_macro(script_name, script_description, apply_gradient)






]]