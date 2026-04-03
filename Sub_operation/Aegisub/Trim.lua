--[[
Si tu veux connaitre chemin ffmpeg
where.xe ffmpeg

Trim.lua sert à :

✔ sélectionner un sous-titre
✔ récupérer son timing
✔ utiliser FFmpeg pour couper ce moment précis de la vidéo


🧠 Fonction principale

La fonction principale est : trim(sub,sel,act)
	
Elle fait ça :

1️⃣ Tu sélectionnes des lignes de sous-titres dans Aegisub
2️⃣ Le script lit :le temps de début,le temps de fin
3️⃣ Il utilise FFmpeg pour couper la vidéo ou l’audio exactement entre ces temps.
➡️ résultat : un clip vidéo court correspondant au sous-titre.

⚡ Comment il coupe la vidéo

Le script génère cette commande :
	ffmpeg -ss START -i video -t DURÉE paramètres sortie.mp4

	ffmpeg -ss 00:02:10 -i video.mkv -t 00:00:05 -vf "subtitles=trim_temp.ass,scale=-2:1080" -preset veryslow -crf 30 output.mp4
	Ex:
	ffmpeg -ss 00:02:10 -i video.mkv -t 00:00:05 output.mp4

-START est le timecode de début de la coupe
-DURÉE est la durée de la coupe (endt - start)
-video est le nom du fichier vidéo source
-paramètres sont les paramètres choisis dans le GUI 
-sortie.mp4 est le nom du fichier de sortie.


⚙️ Les modes possibles

Quand tu lances la macro, il propose plusieurs options :

🎧 1. Audio Only
Coupe seulement l’audio

fichier final :.m4a

🎬 2. Audio + Video

Coupe la vidéo et l’audio

fichier final :.mp4

🔄 3. Encode
Il peut aussi réencoder la vidéo pour que la coupe soit plus précise.

Paramètres utilisés par defaut:

-preset veryslow
-crf 30
-tune animation
scale=-2:720

4️⃣ Trim + Burn ASS

coupe la vidéo ET ajoute les sous-titres du .ass

-----------------------
1️⃣ -preset veryslow (très lent,meilleure compression))

➡️ Définit la vitesse de compression.

Les presets vont de :
	ultrafast
	superfast
	veryfast
	faster
	fast
	medium (défaut)
	slow
	slower
	veryslow


2️⃣ -crf 30

➡️ Définit la qualité vidéo (Constant Rate Factor).

Échelle :

0 = qualité parfaite (énorme fichier)
18 = très haute qualité
23 = qualité standard
28 = qualité basse
30+ = assez compressé

Donc : crf 30 =compression assez forte

 
📌 souvent utilisé pour clips temporaires ou preview.

3️⃣ -tune animation

➡️ Optimise l’encodage pour les dessins animés / anime.

Il adapte x264 pour :
-lignes nettes
-aplats de couleur
-moins de bruit

Donc c’est idéal pour les anime.

4️⃣ scale=-2:720

➡️ Redimensionne la vidéo.

largeur : -2
hauteur : 720

-2 signifie :
-FFmpeg calcule automatiquement la largeur
-garde le ratio original
-largeur multiple de 2 (nécessaire pour x264)

📌 Exemple :

vidéo originale :1920x1080

après :1280x720

Si tu veux une video 1080p, tu peux faire scale=-2:1080 et FFmpeg calculera 1920x1080 automatiquement.
🧾 Résumé


Ces paramètres veulent dire :

-preset veryslow   → meilleure compression mais très lent
-crf 30            → qualité moyenne
-tune animation    → optimisé pour anime
scale=-2:720       → convertir la vidéo en 720p

Donc ce script crée un clip 720p compressé optimisé pour anime.

]]

--[[ Trim + ASS Burn Version ]]

--[[ Trim + ASS Burn Version ]]

--[[
    Script: Trim & Hardsub
    Description: Découpe la vidéo/audio et permet l'incrustation (hardsub) des sous-titres ASS.
]]

script_name = "Trim & Hardsub"
script_description = "Trim video and optionally burn ASS subtitles"
script_author = "Sam1367, SSgumS & Gemini"
script_version = "1.2.0"

function trim(sub,sel,act)
    local ADD = aegisub.dialog.display
    local ADP = aegisub.decode_path
    local ak = aegisub.cancel
    
    local trimconfig = ADP("?user").."\\trim.conf"
    local scriptpath = ADP("?script").."\\"
    local vpath = ADP("?video").."\\"
    
    -- Récupération du fichier ASS actuel
    local ass_filename = aegisub.file_name()
    if ass_filename == "" then 
        t_error("Veuillez enregistrer votre fichier .ass avant de continuer.", true) 
    end
    local ass_path = scriptpath .. ass_filename
    
    local ms2fr = aegisub.frame_from_ms
    local videoname = nil
    local ffpath = "C:\\Program Files\\FFmpeg\\bin\\ffmpeg.exe"
    
    -- Charger la config existante si elle existe
    local file = io.open(trimconfig, "r")
    if file ~= nil then
        local konf = file:read("*all")
        io.close(file)
        ffpath = konf:match("ffpath:(.-)\n") or ffpath
    end
    
    -- Trouver le nom de la vidéo
    for i=1, #sub do
        if sub[i].class == "info" and sub[i].key == "Video File" then
            videoname = sub[i].value
            break
        end
    end
    
    if not videoname or videoname == "" then 
        videoname = aegisub.project_properties().video_file:gsub("^.*\\", "") 
    end
    
    if not videoname or videoname == "" then 
        t_error("Aucune vidéo détectée dans Aegisub.", true) 
    end
    
    local vid_base = videoname:gsub("%.[^%.]+$", ""):gsub("_?premux",""):gsub("_?workraw","")
    
    -- Interface Utilisateur
    local buttons = {"Trim (Audio Seul)", "Vidéo (Sans Sub)", "Vidéo + Hardsub (ASS)", "Annuler"}
    local GUI = {
        {x=0, y=0, class="label", label="Chemin FFmpeg :"},
        {x=1, y=0, width=30, class="edit", name="ffpath", value=ffpath},
        {x=0, y=1, class="label", label="Note : Enregistrez votre .ass avant le Hardsub."},
    }

    local pressed, res = ADD(GUI, buttons)
    if not pressed or pressed == "Annuler" then ak() end

    -- Sauvegarde du chemin FFmpeg
    local f = io.open(trimconfig, "w")
    f:write("ffpath:" .. res.ffpath .. "\n")
    f:close()

    -- Configuration des paramètres FFmpeg selon le bouton
    local ffconf = ""
    local extension = "mp4"
    
    if pressed == "Trim (Audio Seul)" then
        ffconf = "-vn -c:a aac -b:a 192k"
        extension = "m4a"
    elseif pressed == "Vidéo (Sans Sub)" then
        ffconf = "-c:v libx264 -crf 20 -preset fast -c:a aac -b:a 192k"
        extension = "mp4"
    elseif pressed == "Vidéo + Hardsub (ASS)" then
        -- FORMATAGE CRITIQUE POUR WINDOWS :
        -- FFmpeg veut des "/" et le ":" du lecteur doit être échappé (ex: C\:/chemin/file.ass)
        local escaped_ass = ass_path:gsub("\\", "/"):gsub(":", "\\:")
        ffconf = "-vf \"subtitles='" .. escaped_ass .. "'\" -c:v libx264 -crf 20 -preset fast -c:a aac -b:a 192k"
        extension = "mp4"
    end

    local vfull = vpath .. videoname

    -- Boucle sur la sélection
    for _, li in ipairs(sel) do
        local line = sub[li]
        local start_t = line.start_time
        local end_t = line.end_time
        local duration = end_t - start_t
        
        local sframe = ms2fr(start_t) or 0
        local eframe = ms2fr(end_t) or 0
        
        local out_name = string.format("%s_%d-%d.%s", vid_base, sframe, eframe, extension)
        local out_full = scriptpath .. out_name
        
        local t_start = time2string(start_t)
        local t_dur = time2string(duration)

        -- Construction de la commande (on place -ss APRES -i pour que le filtre subtitles s'aligne sur le temps du clip)
        local cmd = string.format("\"%s\" -i \"%s\" -ss %s -t %s %s -y \"%s\"", 
                    res.ffpath, vfull, t_start, t_dur, ffconf, out_full)
        
        -- Création et exécution du batch
        local batch_path = scriptpath .. "trim_exec.bat"
        local bf = io.open(batch_path, "w")
        bf:write("@echo off\n")
        bf:write("echo En cours d'encodage...\n")
        bf:write(cmd .. "\n")
        bf:write("if %errorlevel% neq 0 pause\n")
        bf:close()
        
        os.execute("\"" .. batch_path .. "\"")
    end
end

function time2string(num)
    local s = num / 1000
    local h = math.floor(s / 3600)
    local m = math.floor((s % 3600) / 60)
    local sec = s % 60
    return string.format("%02d:%02d:%05.2f", h, m, sec)
end

function t_error(message, cancel)
    aegisub.dialog.display({{class="label", label=message}}, {"OK"})
    if cancel then aegisub.cancel() end
end

aegisub.register_macro(script_name, script_description, trim)