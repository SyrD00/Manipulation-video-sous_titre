
-- XY Bounding Box + Text Extents (compatible Aegisub 2.1.7)
-- Affiche (x1,y1,x2,y2), largeur, hauteur, marges et coordonnées réelles
-- Auteur : Star + ChatGPT
-- Version : 2.3 (spéciale Aegisub 2.1.7)

script_name = "XY Bounding Box (Aegisub 2.x)"
script_description = "Affiche les coordonnées réelles (x,y,x1,y1,x2,y2) du texte selon marges et alignement"
script_author = "Star + ChatGPT"
script_version = "2.3"

function xy_bbox_21(subs, sel)
    if #sel == 0 then
        aegisub.dialog.display({{class="label", label="Sélectionne au moins une ligne !"}}, {"OK"})
        return
    end

    local index = sel[1]
    local line = subs[index]

    -- Valeurs par défaut
    local playresx, playresy = 1920, 1080

    -- Essai : lire la résolution depuis [Script Info]
    for i = 1, #subs do
        if subs[i].class == "info" then
            if subs[i].key == "PlayResX" then playresx = tonumber(subs[i].value) or playresx end
            if subs[i].key == "PlayResY" then playresy = tonumber(subs[i].value) or playresy end
        end
    end

    -- Trouver le style
    local style = nil
    for i = 1, #subs do
        if subs[i].class == "style" and subs[i].name == line.style then
            style = subs[i]
            break
        end
    end
    if not style then
        aegisub.dialog.display({{class="label", label="Aucun style trouvé pour cette ligne."}}, {"OK"})
        return
    end

    -- Nettoyage du texte
    local raw_text = line.text or ""
    local clean_text = raw_text:gsub("{[^}]-}", ""):gsub("\\N","\\n")

    -- Marges du style
    local ml = tonumber(style.margin_l) or 0
    local mr = tonumber(style.margin_r) or 0
    local mv = tonumber(style.margin_v) or 20

    -- Alignement
    local override_an = raw_text:match("\\an(%d+)")
    local align = tonumber(override_an) or tonumber(style.alignment) or 2

    -- \pos() prioritaire
    local px, py = raw_text:match("\\pos%(([%d%.%-]+),%s*([%d%.%-]+)%)")
    local x, y
    if px and py then
        x = tonumber(px)
        y = tonumber(py)
    else
        -- Calcul par alignement
        if align % 3 == 1 then
            x = ml                               -- gauche
        elseif align % 3 == 2 then
            x = playresx / 2                     -- centre
        else
            x = playresx - mr                    -- droite
        end

        if align <= 3 then
            y = playresy - mv                    -- bas
        elseif align <= 6 then
            y = playresy / 2                     -- milieu
        else
            y = mv                               -- haut
        end
    end

    -- Mesure du texte
    local ok, w, h, descent, extlead = pcall(aegisub.text_extents, style, clean_text)
    if not ok then
        aegisub.dialog.display({{class="label", label="Erreur text_extents(): "..tostring(w)}}, {"OK"})
        return
    end

    -- Calcul du rectangle selon alignement
    local x1, y1, x2, y2
    local horz = align % 3
    if horz == 1 then
        x1 = x; x2 = x + w
    elseif horz == 2 then
        x1 = x - w/2; x2 = x + w/2
    else
        x1 = x - w; x2 = x
    end

    if align <= 3 then
        y2 = y; y1 = y - h          -- bas
    elseif align <= 6 then
        y1 = y - h/2; y2 = y + h/2  -- milieu
    else
        y1 = y; y2 = y + h          -- haut
    end

    -- Affichage complet
    local msg = string.format(
        "Texte : %s\nFont : %s %.1f\nAlignement = %d\nMargeL = %d  MargeR = %d  MargeV = %d\nRésolution = %dx%d\nx = %.1f  y = %.1f\nLargeur = %.1f  Hauteur = %.1f\nDescent = %.1f  ExtLead = %.1f\nx1 = %.1f  y1 = %.1f\nx2 = %.1f  y2 = %.1f",
        clean_text, style.fontname, style.fontsize,
        align, ml, mr, mv, playresx, playresy,
        x, y, w, h, descent or 0, extlead or 0,
        x1, y1, x2, y2
    )

    aegisub.log(msg.."\n")
    aegisub.dialog.display({{class="label", label=msg}}, {"OK"})
end

aegisub.register_macro(script_name, script_description, xy_bbox_21)
