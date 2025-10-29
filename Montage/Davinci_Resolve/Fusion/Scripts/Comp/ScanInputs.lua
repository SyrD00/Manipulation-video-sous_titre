-- Diagnostic minimal pour TextPlus / MacroOperator : détecte le bon champ de tracking
resolve = Resolve()
project = resolve:GetProjectManager():GetCurrentProject()
timeline = project:GetCurrentTimeline()
if not timeline then
    print("❌ Aucune timeline ouverte.")
    return
end

local clip = timeline:GetCurrentVideoItem()
if not clip then
    print("❌ Aucun clip sélectionné.")
    return
end

if clip:GetFusionCompCount() == 0 then
    print("❌ Ce clip n’a pas de comp Fusion.")
    return
end

local comp = clip:GetFusionCompByIndex(1)
local tools = comp:GetToolList(false)

-- fonction pour trouver le TextPlus même dans une macro
local function findTextPlus(tool)
    if tool.ID == "TextPlus" then return tool end
    if tool.ID == "MacroOperator" and tool.Tools then
        for _, st in pairs(tool.Tools) do
            local t = findTextPlus(st)
            if t then return t end
        end
    end
    return nil
end

local targetTP = nil
for _, tool in pairs(tools) do
    targetTP = findTextPlus(tool)
    if targetTP then break end
end

if not targetTP then
    print("⚠️ Aucun TextPlus trouvé (même interne).")
    return
end

print("🎯 TextPlus trouvé :", targetTP.Name or "(sans nom)")
print("Type Inputs :", type(targetTP.Inputs))

-- 🧩 Noms possibles à tester
local names = {
    "CharacterSpacing",
    "CharacterSpacingClone",
    "Tracking",
    "Spacing",
    "CharSpacing",
    "Character Spacing",
    "Character_Spacing",
    "CharacterSpacing1"
}

local found = false
for _, n in ipairs(names) do
    local ok, val = pcall(function() return targetTP.Inputs and targetTP.Inputs[n] end)
    if ok and val ~= nil then
        print("✅ Champ détecté :", n, "(type:", type(val), ")")
        found = true
    end
end

if not found then
    print("❌ Aucun champ CharacterSpacing trouvé dans ce TextPlus.")
end
