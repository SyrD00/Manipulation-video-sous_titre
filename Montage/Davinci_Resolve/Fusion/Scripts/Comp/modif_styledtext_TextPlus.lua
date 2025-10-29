resolve = Resolve()
project = resolve:GetProjectManager():GetCurrentProject()
timeline = project:GetCurrentTimeline()

if not timeline then
    print("❌ Aucune timeline ouverte.")
    return
end

-- Prend le clip actuellement sélectionné
clip = timeline:GetCurrentVideoItem()
if not clip then
    print("❌ Aucun clip sélectionné.")
    return
end

if clip:GetFusionCompCount() == 0 then
    print("❌ Ce clip n’a pas de comp Fusion.")
    return
end

-- Récupère le comp
comp = clip:GetFusionCompByIndex(1)
tools = comp:GetToolList(false)

local modified = false

for _, tool in pairs(tools) do
    if tool.ID == "TextPlus" then
        print("🎯 TextPlus détecté :", tool.Name)
        tool.StyledText = "🎶 BRUTE FORCE TEST 🎶"
        print("✅ Texte modifié directement sur TextPlus.")
        modified = true
    elseif tool.ID == "MacroOperator" and tool.Tools and tool.Tools.Template then
        local inner = tool.Tools.Template
        if inner.ID == "TextPlus" then
            print("🎯 TextPlus interne détecté dans macro :", tool.Name)
            inner.StyledText = "🎶 BRUTE FORCE TEST 🎶"
            print("✅ Texte modifié directement à l’intérieur du macro.")
            modified = true
        end
    end
end

if not modified then
    print("⚠️ Aucun TextPlus trouvé dans ce clip.")
else
    print("✅ Test terminé, vérifie ton viewer.")
end
