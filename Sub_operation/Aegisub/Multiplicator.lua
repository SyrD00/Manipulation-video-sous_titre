-- Multiplier lignes avec position
-- Compatible Aegisub Automation 4 Lua

script_name = "Multiplier lignes"
script_description = "Multiplie les lignes sélectionnées et ajoute un tag \\pos si nécessaire"
script_author = "GPT"
script_version = "1.0"

local tr = aegisub.gettext

-- Vérifie si le texte a déjà un \pos
local function has_pos(text)
    return text:match("\\pos%(")
end

-- Ajoute ou remplace le tag \pos
local function set_pos(text, x, y)
    if has_pos(text) then
        -- Remplacer la position existante
        return text:gsub("\\pos%([^%)]+%)", string.format("\\pos(%d,%d)", x, y))
    else
        -- Ajouter \pos au début des tags
        return text:gsub("^{", string.format("{\\pos(%d,%d)", x, y), 1)
               :gsub("^", string.format("{\\pos(%d,%d)}", x, y), 1)
    end
end

function multiply_lines(subs, sel)
    -- GUI pour le nombre de duplications et coordonnées
    local main_dialog = {
        {class="label", label="Nombre de duplications :", x=0, y=0},
        {class="intedit", name="n", value=2, min=1, x=1, y=0},
        {class="label", label="Coordonnée X :", x=0, y=1},
        {class="intedit", name="x", value=100, x=1, y=1},
        {class="label", label="Coordonnée Y :", x=0, y=2},
        {class="intedit", name="y", value=100, x=1, y=2},
    }
    local buttons = {"OK","Annuler"}
    local pressed, res = aegisub.dialog.display(main_dialog, buttons)
    if pressed ~= "OK" then return end

    local n = res.n
    local x = res.x
    local y = res.y

    local new_lines = {}
    for _, i in ipairs(sel) do
        local line = subs[i]
        -- Ajouter \pos si nécessaire
        local text = line.text
        if not has_pos(text) then
            text = string.format("{\\pos(%d,%d)}%s", x, y, text)
        end

        -- Créer n copies
        for j=1,n do
            local new_line = table.deepcopy(line) -- copier la ligne entière
            new_line.text = text
            table.insert(new_lines, new_line)
        end
    end

    -- Insérer les nouvelles lignes après les originales
    local offset = 0
    for _, line in ipairs(new_lines) do
        subs.insert(sel[#sel]+offset+1, line)
        offset = offset + 1
    end
end

aegisub.register_macro(script_name, script_description, multiply_lines)
