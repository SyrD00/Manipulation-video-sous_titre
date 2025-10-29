-- =========================================================
-- 🎶 FAKE TRACKING via StyledText (espaces fins invisibles)
-- Compatible Resolve sans utf8
-- =========================================================

resolve = Resolve()
project = resolve:GetProjectManager():GetCurrentProject()
timeline = project:GetCurrentTimeline()
if not timeline then print("❌ Pas de timeline."); return end

local track3 = timeline:GetItemListInTrack("video", 3)
local total = 0

-- Espace fin Unicode (inséré directement dans le code)
-- Si besoin tu peux copier ce caractère manuellement → " "
local thinspace = " "  -- (U+200A)

-- Nettoie le texte de base
local function cleanText(t)
    if not t then return "" end
    t = t:gsub("🎶", ""):gsub("%s+", " "):gsub("^%s*(.-)%s*$", "%1")
    return t
end

-- Ajoute des espaces fins entre lettres
local function applyFakeTracking(text, factor)
    local chars = {}
    for c in text:gmatch(".") do table.insert(chars, c) end
    return table.concat(chars, thinspace:rep(factor))
end

-- Récupère texte dans comp
local function getTextFromComp(comp)
    local tools = comp:GetToolList(true)
    for _, tool in pairs(tools) do
        if tool.ID == "MacroOperator" and tool.Tools and tool.Tools.Template then
            local tpl = tool.Tools.Template
            if tpl.StyledText then
                return tpl, tpl.StyledText[fu.TIME_UNDEFINED] or ""
            end
        elseif tool.ID == "TextPlus" then
            return tool, tool.StyledText[fu.TIME_UNDEFINED] or ""
        end
    end
    return nil, ""
end

-- Applique texte avec fake tracking
local function applyToComp(comp, factor)
    local tpl, txt = getTextFromComp(comp)
    if not tpl or txt == "" then return false end

    local base = cleanText(txt)
    local spaced = applyFakeTracking(base, factor)
    tpl.StyledText = spaced
    return true, base
end

-- === Boucle principale ===
local factorBase = 1  -- augmente à 2, 3, etc. pour élargir visuellement
for _, clip in ipairs(track3) do
    if clip:GetFusionCompCount() > 0 then
        local comp = clip:GetFusionCompByIndex(1)
        local ok, base = applyToComp(comp, factorBase)
        if ok then
            print("🎵", base, "→ espacement visuel appliqué")
            total = total + 1
        else
            print("⚠️ Aucun texte trouvé pour", clip:GetName())
        end
    end
end

print("==========================================================")
print("✅ Fake tracking appliqué à " .. total .. " Text+ 🎶 🎶")
print("💡 Augmente 'factorBase' dans le script pour plus d'espacement.")
