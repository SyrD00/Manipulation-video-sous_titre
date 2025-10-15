-- Multicolor Vertical Gradient Everything style
script_name = "Multicolor Vertical Gradient"
script_description = "Dégradé vertical précis avec GUI"
script_author = "ChatGPT"
script_version = "1.1"

-- Helpers
local function hex2rgb(hex)
    hex = hex:gsub("#","")
    return tonumber(hex:sub(1,2),16), tonumber(hex:sub(3,4),16), tonumber(hex:sub(5,6),16)
end

local function rgb2ass(r,g,b)
    return string.format("&H%02X%02X%02X&",b,g,r)
end

local function interpolate(c1,c2,t)
    return {
        math.floor(c1[1] + (c2[1]-c1[1])*t + 0.5),
        math.floor(c1[2] + (c2[2]-c1[2])*t + 0.5),
        math.floor(c1[3] + (c2[3]-c1[3])*t + 0.5)
    }
end

local function line_copy(line)
    local t = {}
    for k,v in pairs(line) do t[k]=v end
    return t
end

local function remove_color_tags(text)
    return text:gsub("\\%d?c&H%x+&","")
end

-- MAIN
function apply_gradient_gui(subs, sel)
    if #sel==0 then
        aegisub.dialog.display({{class="label", label="Sélectionne au moins une ligne"}}, {"OK"})
        return
    end

    -- GUI étape 1 : choix nb couleurs et tag
    local dlg1 = {
        {class="label", label="Nombre de couleurs (2-10):", x=0, y=0},
        {class="intedit", name="nb_colors", value=3, min=2, max=10, x=1, y=0},
        {class="label", label="Tag couleur:", x=0, y=1},
        {class="dropdown", name="tag", items={"\\c","\\2c","\\3c","\\4c"}, value="\\c", x=1, y=1}
    }

    local btn1, res1 = aegisub.dialog.display(dlg1, {"Suivant","Annuler"})
    if btn1 ~= "Suivant" then return end

    local nb_colors = tonumber(res1.nb_colors) or 3
    local tag = res1.tag

    -- GUI étape 2 : choix couleurs
    local color_dlg = {}
    for i=1, nb_colors do
        table.insert(color_dlg, {class="label", label="Couleur "..i..":", x=0, y=i-1})
        table.insert(color_dlg, {class="color", name="col"..i, x=1, y=i-1, value="#FFFFFF"})
    end

    local btn2, res2 = aegisub.dialog.display(color_dlg, {"Appliquer","Annuler"})
    if btn2 ~= "Appliquer" then return end

    local colors = {}
    for i=1, nb_colors do
        local c = res2["col"..i] or "#FFFFFF"
        colors[i] = {hex2rgb(c)}
    end

    -- Appliquer le gradient
    for s=#sel,1,-1 do
        local idx = sel[s]
        local line = subs[idx]
        local base = remove_color_tags(line.text)
        subs.delete(idx)

        local total_slices = 30 -- tranches verticales
        local start_y = 200
        local end_y = 1032
        local posx, posy = 960, 1008

        for i=1,total_slices do
            local t = (i-1)/(total_slices-1)
            local segment = math.floor(t * (nb_colors-1)) + 1
            local segment_start = (segment-1) / (nb_colors-1)
            local segment_end = segment / (nb_colors-1)
            local local_t = (t - segment_start) / (segment_end - segment_start)
            local col = interpolate(colors[segment], colors[math.min(segment+1, nb_colors)], local_t)

            local newline = line_copy(line)
            local y1 = start_y + (i-1)*(end_y-start_y)/total_slices
            local y2 = start_y + i*(end_y-start_y)/total_slices
            newline.text = string.format("{\\clip(%d,%d,%d,%d)\\pos(%d,%d)%s%s}%s",
                                        0, y1, 1920, y2, posx, posy, tag, rgb2ass(col[1],col[2],col[3]), base)
            subs.append(newline)
        end
    end

    aegisub.set_undo_point(script_name)
end

aegisub.register_macro(script_name, script_description, apply_gradient_gui)