--[[
Script Name: Sélectionner par style (avancé)
Description: Sélectionne les lignes selon les styles choisis, avec options : Exact/Contient/Regex, Inclure/Exclure et liste des styles détectés.
Author: ChatGPT
Version: 4.0
--]]

script_name = "Sélectionner par style"
script_description = "Sélectionne ou exclut les lignes selon le style (Exact/Contient/Regex) + affichage des styles présents"
script_author = "ChatGPT"
script_version = "4.0"

------------------------------------------------------
-- 🔹 Fonction utilitaire : normalisation du nom
------------------------------------------------------
local function normalize(s)
    if not s then return "" end
    s = s:gsub("\194\160", " "):gsub("\227\128\128", " ")
    s = s:gsub("\t", " ")
    s = s:gsub("^%s+", ""):gsub("%s+$", "")
    s = s:gsub("%s+", " ")
    s = s:lower()
    return s
end

------------------------------------------------------
-- 🔹 Collecte des styles utilisés
------------------------------------------------------
local function collect_used_styles(subs)
    local counts = {}
    for i = 1, #subs do
        local line = subs[i]
        if line.class == "dialogue" and not line.comment then
            local key = normalize(line.style)
            counts[key] = (counts[key] or 0) + 1
        end
    end
    return counts
end

------------------------------------------------------
-- 🔹 Affiche la liste des styles détectés
------------------------------------------------------
local function show_style_list(subs)
    local counts = collect_used_styles(subs)
    local rows = {}
    for k, v in pairs(counts) do
        table.insert(rows, string.format("• %s  (%d)", k, v))
    end
    table.sort(rows)
    local msg
    if #rows == 0 then
        msg = "Aucun style trouvé dans les lignes de dialogue (non commentées)."
    else
        msg = "Styles détectés (normalisés) et nombre de lignes :\n\n" .. table.concat(rows, "\n")
    end
    aegisub.debug.out(msg .. "\n")
end

------------------------------------------------------
-- 🔹 Fonction principale
------------------------------------------------------
function select_by_style(subs, sel)
    local dlg = {
        {class="label", label="Entrez les styles (séparés par des virgules) :", x=0, y=0, width=3, height=1},
        {class="edit",  name="styles", value="", x=0, y=1, width=6, height=1},
        {class="label", label="Mode :", x=0, y=2, width=1, height=1},
        {class="dropdown", name="mode", items={"Exact","Contient","Regex"}, value="Exact", x=1, y=2, width=2, height=1},
        {class="label", label="Type de sélection :", x=3, y=2, width=2, height=1},
        {class="dropdown", name="type", items={"Inclure (garder ces styles)","Exclure (tout sauf ces styles)"}, value="Inclure (garder ces styles)", x=5, y=2, width=3, height=1},
        {class="checkbox", name="ignore_comments", label="Ignorer les commentaires", value=true, x=0, y=3, width=3, height=1},
    }

    local btn, res = aegisub.dialog.display(dlg, {"Sélectionner", "Lister styles présents", "Annuler"})
    if btn == "Annuler" then return end
    if btn == "Lister styles présents" then
        show_style_list(subs)
        btn, res = aegisub.dialog.display(dlg, {"Sélectionner", "Annuler"})
        if btn ~= "Sélectionner" then return end
    end

    ------------------------------------------------------
    -- Prépare la liste des styles recherchés
    ------------------------------------------------------
    local wanted = {}
    for raw in string.gmatch(res.styles or "", "([^,]+)") do
        local n = normalize(raw)
        if n ~= "" then table.insert(wanted, n) end
    end
    if #wanted == 0 then
        aegisub.debug.out("⚠️ Aucun style saisi.\n")
        return
    end

    local mode = res.mode or "Exact"
    local exclude = (res.type == "Exclure (tout sauf ces styles)")
    local new_sel = {}

    ------------------------------------------------------
    -- Parcours de toutes les lignes
    ------------------------------------------------------
    for i = 1, #subs do
        local line = subs[i]
        if line.class == "dialogue" and (not res.ignore_comments or not line.comment) then
            local ls = normalize(line.style)
            local match = false

            if mode == "Exact" then
                for _, w in ipairs(wanted) do
                    if ls == w then match = true break end
                end
            elseif mode == "Contient" then
                for _, w in ipairs(wanted) do
                    if ls:find(w, 1, true) then match = true break end
                end
            else -- Regex
                for _, w in ipairs(wanted) do
                    local ok = pcall(function()
                        if ls:match(w) then match = true end
                    end)
                    if match then break end
                end
            end

            -- Sélection logique : inclure ou exclure
            if (not exclude and match) or (exclude and not match) then
                table.insert(new_sel, i)
            end
        end
    end

    ------------------------------------------------------
    -- Résultat
    ------------------------------------------------------
    if #new_sel == 0 then
        local counts = collect_used_styles(subs)
        local hint = ""
        if next(counts) ~= nil then
            hint = "\n\nAide — styles détectés (normalisés) :\n"
            local tmp = {}
            for k, v in pairs(counts) do table.insert(tmp, string.format("  - %s (%d)", k, v)) end
            table.sort(tmp)
            hint = hint .. table.concat(tmp, "\n")
        else
            hint = "\n\nAucune ligne de dialogue non commentée trouvée."
        end
        aegisub.debug.out("Aucune ligne trouvée pour les styles donnés." .. hint .. "\n")
        aegisub.cancel()
        return
    end

    aegisub.set_undo_point("Sélection par style (avancé)")
    return new_sel
end

------------------------------------------------------
-- 🔹 Enregistrement du script
------------------------------------------------------
aegisub.register_macro(script_name, script_description, select_by_style)
