// ==UserScript==
// @name         TikTok Playlist Private Manager v2.7.6 (Debug Enabled)
// @namespace    https://tampermonkey.net/
// @version      2.7.6
// @description  Récupère les vidéos d'une playlist TikTok, les retrouve dans Studio et modifie leur visibilité avec vérification robuste, gestion exacte des visibilités (0=Public, 1=Privé, 2=Amis) et logs détaillés.
// @match        https://www.tiktok.com/*
// @run-at       document-start
// @sandbox      raw
// @grant        GM_setValue
// @grant        GM_getValue
// @grant        GM_deleteValue
// @grant        GM_setClipboard
// @grant        unsafeWindow
// @noframes
// ==/UserScript==

(function () {
    'use strict';

    console.log(
        '%c[TTPM v2.7.6] 🚀 UserScript injecté et en cours d\'initialisation...',
        'background: #111; color: #25F4EE; font-weight: bold; font-size: 13px; padding: 4px 8px; border-radius: 4px; border: 1px solid #25F4EE;'
    );

    const DB_KEY = 'TT_PRIVATE_MANAGER_V24';
    const PLAYLIST_PAGE_SIZE = 30;
    const PLAYLIST_MAX_PAGES = 100;
    const PLAYLIST_PAGE_DELAY = 500;
    const STUDIO_PAGE_SIZE = 30;
    const STUDIO_MAX_PAGES = 100;
    const STUDIO_PAGE_DELAY = 250;
    const EDIT_DELAY = 1500;
    const API_MAX_RETRIES = 3;
    const STUDIO_SCAN_VALID_MS = 10 * 60 * 1000;
    const PANEL_ID = 'tt-private-manager-v24';

    let debugMode = true;

    function log(type, tag, message, data = null) {
        if (!debugMode && type === 'info') return;
        const prefix = `%c[TTPM ${tag}]`;
        let style = 'color: #25F4EE; font-weight: bold;';

        if (type === 'success') style = 'color: #2ecc71; font-weight: bold;';
        if (type === 'warn') style = 'color: #f1c40f; font-weight: bold;';
        if (type === 'error') style = 'color: #e74c3c; font-weight: bold;';
        if (type === 'action') style = 'color: #9b59b6; font-weight: bold;';

        if (data !== null) {
            console.log(prefix, style, message, data);
        } else {
            console.log(prefix, style, message);
        }
    }

    const VISIBILITY = {
        PUBLIC_FOLLOWERS: 0,
        ONLY_ME: 1,
        FRIENDS: 2
    };

    const DEFAULT_VISIBILITY = VISIBILITY.ONLY_ME;

    const EMPTY_DB = {
        playlistId: '',
        playlistName: '',
        username: '',
        expectedCount: 0,
        videos: [],
        processed: [],
        alreadyPrivate: [],
        failed: [],
        studioMatches: [],
        lastScan: null,
        lastStudioScan: null,
        lastStudioRun: null,
        selectedVisibility: DEFAULT_VISIBILITY,
        processedByVisibility: { '0': [], '1': [], '2': [] },
        alreadyTargetByVisibility: { '0': [], '1': [], '2': [] },
        savedPlaylists: []
    };

    let db = loadDB();
    let busy = false;
    let stopRequested = false;

    let nativeEditTemplate = null;
    let nativeEditParamsTemplate = null;
    let internalEditRequest = false;

    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    function addUnique(array, value) {
        if (!Array.isArray(array)) return false;
        const normalized = String(value);
        if (array.some(item => String(item) === normalized)) return false;
        array.push(normalized);
        return true;
    }

    function escapeHTML(text) {
        return String(text ?? '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function showAlert(title, message) {
        log('warn', 'UI-Alert', `${title} - ${message}`);
        return new Promise((resolve) => {
            const overlay = document.createElement('div');
            overlay.style.cssText = `
                position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
                background: rgba(0, 0, 0, 0.75); z-index: 2147483647;
                display: flex; align-items: center; justify-content: center;
                font-family: Arial, sans-serif;
            `;
            const box = document.createElement('div');
            box.style.cssText = `
                background: #1a1a1a; border: 2px solid #25F4EE; border-radius: 12px;
                padding: 20px; max-width: 400px; width: 90%; color: #fff;
                box-shadow: 0 10px 25px rgba(0,0,0,0.8); text-align: center;
            `;
            box.innerHTML = `
                <h3 style="margin-top:0; color:#25F4EE; font-size:16px;">${escapeHTML(title)}</h3>
                <div style="font-size:13px; margin: 15px 0; white-space: pre-wrap; word-break: break-word; text-align: left; max-height: 250px; overflow-y: auto; line-height: 1.4;">${escapeHTML(message)}</div>
                <button id="ttpm-dialog-ok" style="background:#25F4EE; color:#000; border:none; padding:8px 20px; border-radius:6px; font-weight:bold; cursor:pointer; width:100%;">OK</button>
            `;
            overlay.appendChild(box);
            document.body.appendChild(overlay);

            box.querySelector('#ttpm-dialog-ok').onclick = () => {
                document.body.removeChild(overlay);
                resolve(true);
            };
        });
    }

    function showConfirm(title, message) {
        log('action', 'UI-Confirm', `${title} - ${message}`);
        return new Promise((resolve) => {
            const overlay = document.createElement('div');
            overlay.style.cssText = `
                position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
                background: rgba(0, 0, 0, 0.75); z-index: 2147483647;
                display: flex; align-items: center; justify-content: center;
                font-family: Arial, sans-serif;
            `;
            const box = document.createElement('div');
            box.style.cssText = `
                background: #1a1a1a; border: 2px solid #FE2C55; border-radius: 12px;
                padding: 20px; max-width: 400px; width: 90%; color: #fff;
                box-shadow: 0 10px 25px rgba(0,0,0,0.8); text-align: center;
            `;
            box.innerHTML = `
                <h3 style="margin-top:0; color:#FE2C55; font-size:16px;">${escapeHTML(title)}</h3>
                <div style="font-size:13px; margin: 15px 0; white-space: pre-wrap; word-break: break-word; text-align: left; max-height: 250px; overflow-y: auto; line-height: 1.4;">${escapeHTML(message)}</div>
                <div style="display:flex; gap:10px;">
                    <button id="ttpm-dialog-cancel" style="background:#444; color:#fff; border:none; padding:8px 15px; border-radius:6px; font-weight:bold; cursor:pointer; flex:1;">Annuler</button>
                    <button id="ttpm-dialog-confirm" style="background:#FE2C55; color:#fff; border:none; padding:8px 15px; border-radius:6px; font-weight:bold; cursor:pointer; flex:1;">Confirmer</button>
                </div>
            `;
            overlay.appendChild(box);
            document.body.appendChild(overlay);

            box.querySelector('#ttpm-dialog-cancel').onclick = () => {
                document.body.removeChild(overlay);
                resolve(false);
            };
            box.querySelector('#ttpm-dialog-confirm').onclick = () => {
                document.body.removeChild(overlay);
                resolve(true);
            };
        });
    }

    function getLanguage() {
        return (navigator.language || document.documentElement.lang || 'fr')
            .split('-')[0]
            .toLowerCase();
    }

    function normalizeVisibility(value) {
        let n = Number(value);
        if ([0, 1, 2].includes(n)) return n;
        return DEFAULT_VISIBILITY;
    }

    function getVisibilityLabel(visibility) {
        const v = normalizeVisibility(visibility);
        if (v === VISIBILITY.ONLY_ME) return 'Privé / Moi uniquement';
        if (v === VISIBILITY.PUBLIC_FOLLOWERS) return 'Public / Followers';
        return 'Amis';
    }

    function studioItemMatchesTarget(item, targetVisibility) {
        if (!item) return false;
        const target = normalizeVisibility(targetVisibility);
        const visibility = Number(item.visibility);
        return visibility === target;
    }

    function getStudioItemStateLabel(item) {
        if (!item) return 'Introuvable';
        const vis = Number(item.visibility);
        let label = `${vis} (Inconnu)`;
        if (vis === 0) label = '0 (Public/Followers)';
        else if (vis === 1) label = '1 (Privé/Moi uniquement)';
        else if (vis === 2) label = '2 (Amis)';

        return `visibilité=${label}, statut=${item.status ?? '?'}, modifiable=${Boolean(item.canChangePrivacy)}`;
    }

    function normalizeVisibilityMap(source) {
        const result = { '0': [], '1': [], '2': [] };
        if (!source || typeof source !== 'object' || Array.isArray(source)) return result;
        for (const key of ['0', '1', '2']) {
            if (Array.isArray(source[key])) {
                result[key] = Array.from(new Set(source[key].map(value => String(value))));
            }
        }
        return result;
    }

    function normalizeSavedPlaylist(playlist) {
        if (!playlist || typeof playlist !== 'object') return null;
        const playlistId = playlist.playlistId == null ? '' : String(playlist.playlistId);
        if (!playlistId) return null;
        const rawVideos = Array.isArray(playlist.videos) ? playlist.videos : [];
        const videos = rawVideos
            .filter(video => video && typeof video === 'object' && video.id)
            .map(video => ({
                id: String(video.id),
                desc: typeof video.desc === 'string' ? video.desc : '',
                createTime: Number(video.createTime || 0),
                authorUsername: typeof video.authorUsername === 'string' ? video.authorUsername : '',
                shareUrl: typeof video.shareUrl === 'string' ? video.shareUrl : ''
            }));

        return {
            playlistId,
            playlistName: typeof playlist.playlistName === 'string' ? playlist.playlistName : '',
            username: typeof playlist.username === 'string' ? playlist.username : '',
            expectedCount: Number(playlist.expectedCount || videos.length || 0),
            videos,
            lastScan: playlist.lastScan ? Number(playlist.lastScan) : null,
            scanComplete: Boolean(playlist.scanComplete),
            savedAt: playlist.savedAt ? Number(playlist.savedAt) : Date.now()
        };
    }

    function normalizeSavedPlaylists(source) {
        if (!Array.isArray(source)) return [];
        const result = [];
        const byId = new Map();
        for (const raw of source) {
            const playlist = normalizeSavedPlaylist(raw);
            if (playlist) byId.set(playlist.playlistId, playlist);
        }
        for (const playlist of byId.values()) {
            result.push(playlist);
        }
        return result;
    }

    function loadDB() {
        try {
            let raw = GM_getValue(DB_KEY, '');
            if (!raw) {
                log('info', 'DB-Load', 'Création d\'une base de données vierge.');
                return structuredClone(EMPTY_DB);
            }

            const loaded = { ...structuredClone(EMPTY_DB), ...(typeof raw === 'string' ? JSON.parse(raw) : raw) };
            loaded.videos = Array.isArray(loaded.videos) ? loaded.videos : [];
            loaded.processed = Array.isArray(loaded.processed) ? loaded.processed : [];
            loaded.alreadyPrivate = Array.isArray(loaded.alreadyPrivate) ? loaded.alreadyPrivate : [];
            loaded.failed = Array.isArray(loaded.failed) ? loaded.failed : [];
            loaded.studioMatches = Array.isArray(loaded.studioMatches) ? loaded.studioMatches : [];
            loaded.selectedVisibility = normalizeVisibility(loaded.selectedVisibility);

            loaded.processedByVisibility = normalizeVisibilityMap(loaded.processedByVisibility);
            loaded.alreadyTargetByVisibility = normalizeVisibilityMap(loaded.alreadyTargetByVisibility);
            loaded.savedPlaylists = normalizeSavedPlaylists(loaded.savedPlaylists);

            log('success', 'DB-Load', `Base chargée : ${loaded.videos.length} vidéos enregistrées.`, loaded);
            return loaded;
        } catch (error) {
            log('error', 'DB-Load', 'Erreur chargement DB :', error);
            return structuredClone(EMPTY_DB);
        }
    }

    function getProcessedList(visibility = db.selectedVisibility) {
        const key = String(normalizeVisibility(visibility));
        if (!db.processedByVisibility || typeof db.processedByVisibility !== 'object') {
            db.processedByVisibility = normalizeVisibilityMap(null);
        }
        if (!Array.isArray(db.processedByVisibility[key])) {
            db.processedByVisibility[key] = [];
        }
        return db.processedByVisibility[key];
    }

    function getAlreadyTargetList(visibility = db.selectedVisibility) {
        const key = String(normalizeVisibility(visibility));
        if (!db.alreadyTargetByVisibility || typeof db.alreadyTargetByVisibility !== 'object') {
            db.alreadyTargetByVisibility = normalizeVisibilityMap(null);
        }
        if (!Array.isArray(db.alreadyTargetByVisibility[key])) {
            db.alreadyTargetByVisibility[key] = [];
        }
        return db.alreadyTargetByVisibility[key];
    }

    function syncLegacyArrays() {
        const visibility = normalizeVisibility(db.selectedVisibility);
        db.selectedVisibility = visibility;
        db.processed = [...getProcessedList(visibility)];
        db.alreadyPrivate = [...getAlreadyTargetList(visibility)];
    }

    function saveDB() {
        syncLegacyArrays();
        db.savedPlaylists = normalizeSavedPlaylists(db.savedPlaylists);
        GM_setValue(DB_KEY, JSON.stringify(db));
        log('info', 'DB-Save', 'Base de données sauvegardée.');
    }

    function markProcessed(id, visibility = db.selectedVisibility) {
        addUnique(getProcessedList(visibility), String(id));
        syncLegacyArrays();
    }

    function markAlreadyTarget(id, visibility = db.selectedVisibility) {
        addUnique(getAlreadyTargetList(visibility), String(id));
        syncLegacyArrays();
    }

    function setAlreadyTargetList(ids, visibility = db.selectedVisibility) {
        const key = String(normalizeVisibility(visibility));
        db.alreadyTargetByVisibility[key] = Array.from(new Set((ids || []).map(id => String(id))));
        syncLegacyArrays();
    }

    function getSavedPlaylist(playlistId) {
        const id = String(playlistId);
        return (db.savedPlaylists || []).find(playlist => String(playlist.playlistId) === id) || null;
    }

    function getPlaylistIdFromURL() {
        const decoded = decodeURIComponent(location.pathname);
        let match = decoded.match(/playlist\/.*?-(\d{15,25})(?:\/)?$/i);
        if (match) return match[1];
        const fallback = location.href.match(/-(\d{15,25})(?:[/?#]|$)/);
        return fallback ? fallback[1] : '';
    }

    function getUsernameFromURL() {
        const match = location.pathname.match(/^\/@([^/]+)/);
        if (!match) return '';
        try {
            return decodeURIComponent(match[1]);
        } catch {
            return match[1];
        }
    }

    function isPlaylistPage() {
        return location.pathname.includes('/playlist/');
    }

    function isStudioPage() {
        return location.pathname.includes('/tiktokstudio/content');
    }

    function normalizeVideo(video) {
        if (!video || typeof video !== 'object') return null;

        const candidates = [
            video.id, video.itemId, video.item_id, video.videoId,
            video.video_id, video.awemeId, video.aweme_id,
            video.item?.id, video.item?.itemId, video.item?.item_id,
            video.video?.id, video.video?.videoId,
            video.aweme_info?.aweme_id, video.aweme_info?.id
        ];

        let id = '';
        for (const candidate of candidates) {
            if (candidate === undefined || candidate === null) continue;
            const value = String(candidate);
            if (/^\d{15,25}$/.test(value)) {
                id = value;
                break;
            }
        }

        if (!id) return null;

        const author = video.author || video.author_info || {};
        const authorUsername = author.uniqueId || author.unique_id || '';

        return {
            id,
            desc: typeof video.desc === 'string' ? video.desc : (typeof video.description === 'string' ? video.description : ''),
            createTime: Number(video.createTime || video.create_time || 0),
            authorUsername,
            shareUrl: authorUsername
                ? `https://www.tiktok.com/@${authorUsername}/video/${id}`
                : `https://www.tiktok.com/video/${id}`
        };
    }

    async function getPlaylistDetail(playlistId) {
        log('info', 'API-Playlist', `Appel Detail pour MixID : ${playlistId}`);
        const params = new URLSearchParams();
        params.set('mixId', playlistId);
        params.set('aid', '1988');
        params.set('language', getLanguage());

        const url = `${location.origin}/api/mix/detail/?${params.toString()}`;
        const response = await fetch(url, {
            method: 'GET',
            credentials: 'include',
            cache: 'no-store',
            headers: {
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': navigator.language || 'fr-FR'
            }
        });

        const text = await response.text();
        if (!response.ok) {
            const error = new Error(`HTTP ${response.status}`);
            error.status = response.status;
            throw error;
        }

        let data;
        try {
            data = JSON.parse(text);
        } catch {
            throw new Error('Réponse detail non JSON.');
        }

        const code = data.statusCode ?? data.status_code;
        if (code !== undefined && Number(code) !== 0) {
            throw new Error(`TikTok API ${code}: ${data.statusMsg || data.status_msg || 'Erreur inconnue'}`);
        }
        return data;
    }

    async function getPlaylistPage(playlistId, cursor) {
        log('info', 'API-Playlist', `Page items (Cursor: ${cursor})`);
        const params = new URLSearchParams();
        params.set('mixId', playlistId);
        params.set('count', String(PLAYLIST_PAGE_SIZE));
        params.set('cursor', String(cursor));
        params.set('aid', '1988');
        params.set('language', getLanguage());

        const url = `${location.origin}/api/mix/item_list/?${params.toString()}`;
        const response = await fetch(url, {
            method: 'GET',
            credentials: 'include',
            cache: 'no-store',
            headers: {
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': navigator.language || 'fr-FR'
            }
        });

        const text = await response.text();
        if (!response.ok) {
            const error = new Error(`HTTP ${response.status}`);
            error.status = response.status;
            throw error;
        }

        let json;
        try {
            json = JSON.parse(text);
        } catch {
            throw new Error('Réponse playlist non JSON.');
        }

        const code = json.statusCode ?? json.status_code;
        if (code !== undefined && Number(code) !== 0) {
            throw new Error(`TikTok API ${code}: ${json.statusMsg || json.status_msg || 'Erreur inconnue'}`);
        }
        return json;
    }

    function extractPlaylistItems(result) {
        const candidates = [
            result?.itemList, result?.item_list, result?.mixItemList, result?.mix_item_list,
            result?.items, result?.mix_items, result?.mixItems, result?.aweme_list,
            result?.data?.itemList, result?.data?.item_list, result?.data?.mixItemList, result?.data?.mix_item_list,
            result?.data?.items, result?.data?.mix_items, result?.data?.mixItems, result?.data?.aweme_list
        ];
        for (const candidate of candidates) {
            if (Array.isArray(candidate)) return candidate;
        }
        return [];
    }

    async function scanPlaylistAPI() {
        log('action', 'Scan-Playlist', 'Démarrage de la récupération de la playlist...');
        if (!isPlaylistPage()) {
            await showAlert('Attention', 'Ouvre d’abord ta playlist TikTok.');
            return;
        }

        const playlistId = getPlaylistIdFromURL();
        if (!playlistId) {
            await showAlert('Erreur', 'Playlist ID introuvable.');
            return;
        }

        log('info', 'Scan-Playlist', `Playlist ID extrait : ${playlistId}`);

        const selectedVisibility = normalizeVisibility(db.selectedVisibility);
        const existingSavedPlaylists = normalizeSavedPlaylists(db.savedPlaylists);

        db = {
            ...structuredClone(EMPTY_DB),
            playlistId,
            username: getUsernameFromURL(),
            selectedVisibility,
            savedPlaylists: existingSavedPlaylists
        };

        saveDB();
        updatePanel();
        setStatus('🔎 Lecture de la playlist...');

        let detail;
        try {
            detail = await getPlaylistDetail(playlistId);
        } catch (error) {
            log('error', 'Scan-Playlist', 'Erreur lors du detail :', error);
            await showAlert('Erreur Playlist', error.message);
            return;
        }

        const mixInfo = detail.mixInfo || detail.data?.mixInfo || {};
        db.playlistName = mixInfo.mixName || mixInfo.name || mixInfo.title || '';
        db.expectedCount = Number(mixInfo.videoCount || mixInfo.video_count || 0);

        saveDB();
        updatePanel();

        const videos = [];
        const seen = new Set();
        let cursor = 0;
        let page = 0;
        let hasMore = true;

        while (hasMore && page < PLAYLIST_MAX_PAGES) {
            page++;
            setStatus(`📥 Playlist ${page} — ${videos.length} / ${db.expectedCount || '?'}`);

            let result;
            try {
                result = await getPlaylistPage(playlistId, cursor);
            } catch (error) {
                log('error', 'Scan-Playlist', `Erreur page ${page} :`, error);
                break;
            }

            const items = extractPlaylistItems(result);
            if (items.length === 0 && page === 1) {
                log('warn', 'Scan-Playlist', 'Aucun élément extrait de la page 1. Structure brute de la réponse :', result);
            }

            for (const rawVideo of items) {
                const video = normalizeVideo(rawVideo);
                if (!video || seen.has(video.id)) continue;
                seen.add(video.id);
                videos.push(video);
            }

            hasMore = Boolean(result.hasMore ?? result.has_more ?? result.data?.hasMore ?? result.data?.has_more ?? false);
            const nextCursor = result.cursor ?? result.data?.cursor;

            if (!hasMore || nextCursor === undefined || nextCursor === null || String(nextCursor) === String(cursor)) {
                break;
            }
            cursor = nextCursor;
            if (db.expectedCount > 0 && videos.length >= db.expectedCount) {
                break;
            }
            await sleep(PLAYLIST_PAGE_DELAY);
        }

        if (videos.length === 0) {
            log('error', 'Scan-Playlist', 'Échec de la récupération : 0 vidéo extraite.');
            setStatus(`❌ Erreur : 0 / ${db.expectedCount || '?'} vidéo extraite`);
            await showAlert(
                '❌ AUCUNE VIDÉO RÉCUPÉRÉE',
                `Playlist : ${db.playlistName || db.playlistId}\nTrouvées : 0\nAttendues : ${db.expectedCount}\n\nCause possible : TikTok a modifié temporairement la structure de réponse d'API.\n\nSauvegarde annulée pour protéger vos données.`
            );
            return;
        }

        db.videos = videos;
        db.lastScan = Date.now();
        db.studioMatches = [];
        db.lastStudioScan = null;
        db.lastStudioRun = null;

        saveDB();
        updatePanel();
        saveCurrentPlaylistToLibrary();
        updatePanel();

        log('success', 'Scan-Playlist', `Total vidéos récupérées : ${videos.length}/${db.expectedCount || '?'}`);
        setStatus(`✅ Playlist : ${videos.length} / ${db.expectedCount || '?'}`);

        if (db.expectedCount > 0 && videos.length !== db.expectedCount) {
            await showAlert(
                '⚠️ PLAYLIST RÉCUPÉRÉE PARTIELLEMENT',
                `Playlist : ${db.playlistName || db.playlistId}\nTrouvées : ${videos.length}\nAttendues : ${db.expectedCount}\n\n(Si vous avez retiré une vidéo récemment, ce décalage est tout à fait normal).`
            );
        } else {
            await showAlert(
                '✅ PLAYLIST RÉCUPÉRÉE',
                `Playlist : ${db.playlistName || db.playlistId}\nID : ${db.playlistId}\nVidéos : ${videos.length}\n\n💾 Sauvegarde automatique effectuée.`
            );
        }
    }

    async function testAPI() {
        if (!isPlaylistPage()) {
            await showAlert('Attention', 'Va d’abord sur la playlist.');
            return;
        }

        const id = getPlaylistIdFromURL();
        if (!id) {
            await showAlert('Erreur', 'Playlist ID introuvable.');
            return;
        }

        try {
            const detail = await getPlaylistDetail(id);
            const mixInfo = detail.mixInfo || detail.data?.mixInfo || {};
            const page = await getPlaylistPage(id, 0);
            const items = extractPlaylistItems(page);

            await showAlert(
                '✅ TEST API RÉUSSI',
                `Playlist : ${mixInfo.name || mixInfo.mixName || '—'}\nVidéos : ${mixInfo.videoCount || '—'}\nPremière page : ${items.length}`
            );
        } catch (error) {
            await showAlert('❌ Test API échoué', error.message);
        }
    }

    function getCookieValue(name) {
        try {
            const cookies = document.cookie.split(';').map(part => part.trim());
            const prefix = `${name}=`;
            for (const cookie of cookies) {
                if (cookie.startsWith(prefix)) return decodeURIComponent(cookie.slice(prefix.length));
            }
        } catch {}
        return '';
    }

    function getTikTokCsrfToken() {
        const cookieNames = ['tt_csrf_token', 'tt-csrf-token'];
        for (const name of cookieNames) {
            const value = getCookieValue(name);
            if (value) return value;
        }

        try {
            const selectors = ['meta[name="tt-csrf-token"]', 'meta[name="csrf-token"]', 'meta[property="tt-csrf-token"]'];
            for (const selector of selectors) {
                const meta = document.querySelector(selector);
                if (meta?.content) return meta.content;
            }
        } catch {}
        return '';
    }

    function getStudioParams() {
        const params = new URLSearchParams();
        params.set('locale', getLanguage());
        params.set('aid', '1988');
        params.set('app_name', 'tiktok_creator_center');
        params.set('app_language', getLanguage());
        params.set('device_platform', 'web_pc');
        params.set('channel', 'tiktok_web');
        return params;
    }

    function getEditParams() {
        if (nativeEditParamsTemplate instanceof URLSearchParams && nativeEditParamsTemplate.toString()) {
            return new URLSearchParams(nativeEditParamsTemplate);
        }

        const params = getStudioParams();
        const browserVersion = (navigator.userAgent || '').match(/(?:Chrome|CriOS)\/([\d.]+)/i)?.[1] || '';

        const defaults = {
            locale: getLanguage(),
            aid: '1988',
            app_name: 'tiktok_creator_center',
            app_language: getLanguage(),
            device_platform: 'web_pc',
            channel: 'tiktok_web',
            browser_language: navigator.language || 'fr-FR',
            browser_platform: navigator.platform || 'Win32',
            browser_name: 'Mozilla',
            browser_version: browserVersion,
            browser_online: 'true',
            cookie_enabled: 'true',
            screen_width: String(screen.width || 1366),
            screen_height: String(screen.height || 768),
            os: /Mac/i.test(navigator.platform || '') ? 'mac' : 'win',
            user_is_login: 'true'
        };

        for (const [key, value] of Object.entries(defaults)) {
            params.set(key, String(value));
        }

        const msToken = getCookieValue('msToken');
        if (msToken) params.set('msToken', msToken);
        const deviceId = getCookieValue('device_id');
        if (deviceId) params.set('device_id', deviceId);

        params.set('priority_region', 'SN');
        params.set('region', 'FR');
        try {
            params.set('tz_name', Intl.DateTimeFormat().resolvedOptions().timeZone || 'Atlantic/Reykjavik');
        } catch {
            params.set('tz_name', 'Atlantic/Reykjavik');
        }
        return params;
    }

    async function getStudioPageSingleRequest(cursor, sortOrder) {
        log('info', 'API-Studio', `Recherche Studio (Cursor: ${cursor}, Sort: ${sortOrder})`);
        const params = getStudioParams();
        const url = `${location.origin}/tiktok/creator/manage/item_list/v1/?${params.toString()}`;
        const body = {
            cursor: Number(cursor),
            size: STUDIO_PAGE_SIZE,
            query: {
                conditions: [],
                sort_orders: [{ field_name: 'post_time', order: Number(sortOrder) }]
            }
        };

        const response = await fetch(url, {
            method: 'POST',
            credentials: 'include',
            cache: 'no-store',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json, text/plain, */*'
            },
            body: JSON.stringify(body)
        });

        const text = await response.text();
        if (response.status === 403) {
            const error = new Error('Studio HTTP 403');
            error.status = 403;
            error.is403 = true;
            throw error;
        }
        if (response.status === 429) {
            const error = new Error('Studio HTTP 429');
            error.status = 429;
            error.is429 = true;
            throw error;
        }
        if (!response.ok) {
            const error = new Error(`Studio HTTP ${response.status}`);
            error.status = response.status;
            throw error;
        }

        let json;
        try {
            json = JSON.parse(text);
        } catch {
            throw new Error('Réponse Studio non JSON.');
        }

        const code = json.status_code ?? json.statusCode;
        if (code !== undefined && Number(code) !== 0) {
            const error = new Error(`Studio API ${code}: ${json.status_msg || json.statusMsg || 'Erreur inconnue'}`);
            error.apiCode = Number(code);
            if (Number(code) === 1 && cursor >= 900) {
                error.isPaginationLimit = true;
            }
            throw error;
        }
        return json;
    }

    async function getStudioPage(cursor, sortOrder) {
        let lastError = null;
        for (let attempt = 1; attempt <= API_MAX_RETRIES; attempt++) {
            try {
                return await getStudioPageSingleRequest(cursor, sortOrder);
            } catch (error) {
                lastError = error;
                if (error.is403 || error.is429 || error.isPaginationLimit) throw error;
                log('warn', 'API-Studio', `Tentative Studio ${attempt}/${API_MAX_RETRIES} échouée: ${error.message}`);
                if (attempt < API_MAX_RETRIES) await sleep(1000 * attempt);
            }
        }
        throw lastError || new Error('Erreur réseau Studio répétée.');
    }

    function extractStudioItems(result) {
        const candidates = [
            result?.item_list, result?.itemList, result?.items,
            result?.data?.item_list, result?.data?.itemList, result?.data?.items
        ];
        for (const candidate of candidates) {
            if (Array.isArray(candidate)) return candidate;
        }
        return [];
    }

    function normalizeStudioItem(item) {
        if (!item || typeof item !== 'object') return null;
        const rawId = item.item_id ?? item.itemId ?? item.aweme_id ?? item.awemeId ?? item.id;
        if (rawId === undefined || rawId === null) return null;
        const id = String(rawId);
        if (!/^\d{15,25}$/.test(id)) return null;

        const permissions = item.permissions || {};
        const changePrivacy = permissions.can_change_privacy || permissions.canChangePrivacy || {};

        return {
            id,
            visibility: Number(item.visibility ?? 0),
            status: Number(item.status ?? 0),
            canChangePrivacy: Boolean(
                changePrivacy.reason === '' ||
                changePrivacy.show_type === 2 ||
                changePrivacy.showType === 2 ||
                item.changePrivacy?.reason === ''
            ),
            description: typeof item.desc === 'string' ? item.desc : '',
            raw: item
        };
    }

    async function scanStudioAPI(showAlerts = true) {
        log('action', 'Scan-Studio', 'Lancement de la recherche Studio...');
        if (!isStudioPage()) {
            if (showAlerts) await showAlert('Attention', 'Ouvre TikTok Studio > Contenu.');
            return null;
        }

        const targets = new Set(db.videos.map(video => String(video.id)));
        if (targets.size === 0) {
            if (showAlerts) await showAlert('Attention', 'Aucune vidéo playlist enregistrée.');
            return null;
        }

        const selectedVisibility = normalizeVisibility(db.selectedVisibility);
        setStatus(`🔎 Recherche de ${targets.size} vidéos — cible : ${getVisibilityLabel(selectedVisibility)}`);

        const studioMap = new Map();
        let scanError = null;

        for (const sortOrder of [2, 1]) {
            let cursor = 0;
            let page = 0;
            let hasMore = true;

            while (hasMore && page < STUDIO_MAX_PAGES) {
                page++;
                setStatus(`🔎 Studio — tri ${sortOrder} — page ${page} — ${studioMap.size}/${targets.size}`);

                let result;
                try {
                    result = await getStudioPage(cursor, sortOrder);
                } catch (error) {
                    scanError = error;
                    if (error.isPaginationLimit) {
                        log('warn', 'Scan-Studio', `Limite de pagination atteinte pour sort ${sortOrder} à cursor ${cursor}. Passage au tri suivant.`);
                        break;
                    }
                    log('error', 'Scan-Studio', 'Erreur scan :', error);
                    if (error.is403 || error.is429) throw error;
                    break;
                }

                const items = extractStudioItems(result);
                for (const rawItem of items) {
                    const item = normalizeStudioItem(rawItem);
                    if (!item) continue;
                    if (targets.has(item.id)) {
                        studioMap.set(item.id, item);
                    }
                }

                const nextCursor = result.cursor ?? result.data?.cursor;
                hasMore = Boolean(result.has_more ?? result.hasMore ?? result.data?.has_more ?? result.data?.hasMore ?? false);

                if (studioMap.size >= targets.size || !hasMore) break;
                if (nextCursor === undefined || nextCursor === null || String(nextCursor) === String(cursor)) break;

                cursor = nextCursor;
                await sleep(STUDIO_PAGE_DELAY);
            }
            if (studioMap.size >= targets.size) break;
        }

        const matches = Array.from(studioMap.values());
        db.studioMatches = matches.map(item => ({
            id: item.id,
            visibility: item.visibility,
            status: item.status,
            canChangePrivacy: item.canChangePrivacy,
            description: item.description
        }));

        const complete = matches.length === targets.size;
        db.lastStudioScan = complete ? Date.now() : null;

        const already = matches
            .filter(item => studioItemMatchesTarget(item, selectedVisibility))
            .map(item => item.id);

        setAlreadyTargetList(already, selectedVisibility);
        saveDB();
        updatePanel();

        log('success', 'Scan-Studio', `Scan Studio terminé : ${matches.length}/${targets.size} trouvées.`);

        const changed = matches.filter(item => !studioItemMatchesTarget(item, selectedVisibility)).length;
        const targetLabel = getVisibilityLabel(selectedVisibility);

        setStatus(complete ? `✅ Studio ${matches.length}/${targets.size} — ${targetLabel}` : `⚠️ Studio ${matches.length}/${targets.size}`);

        if (showAlerts) {
            if (complete) {
                await showAlert(
                    '✅ SCAN STUDIO TERMINÉ',
                    `Cibles playlist : ${targets.size}\nCorrespondances : ${matches.length}\nCible : ${targetLabel}\nDéjà dans la cible : ${already.length}\nÀ modifier : ${changed}\n\nAucune modification effectuée.`
                );
            } else {
                await showAlert(
                    '⚠️ SCAN STUDIO INCOMPLET',
                    `Cibles : ${targets.size}\nCorrespondances : ${matches.length}\nDernière erreur : ${scanError ? scanError.message : 'Certaines vidéos sont introuvables.'}\n\nAucune modification en masse effectuée.`
                );
            }
        }
        return matches;
    }

    function hasValidStudioScan() {
        if (!Array.isArray(db.studioMatches) || db.studioMatches.length !== db.videos.length || !db.lastStudioScan) {
            return false;
        }
        const playlistIds = new Set(db.videos.map(video => String(video.id)));
        const studioIds = new Set(db.studioMatches.map(item => String(item.id)));
        if (playlistIds.size !== studioIds.size) return false;
        for (const id of playlistIds) {
            if (!studioIds.has(id)) return false;
        }
        return Date.now() - Number(db.lastStudioScan) <= STUDIO_SCAN_VALID_MS;
    }

    async function setPrivate(awemeId) {
        const selectedVisibility = normalizeVisibility(db.selectedVisibility);
        log('action', 'Edit-Visibility', `Envoi modification visibilité pour ${awemeId} → Visibilité ${selectedVisibility}`);

        if (!/^\d{15,25}$/.test(String(awemeId))) {
            throw new Error(`ID vidéo invalide : ${awemeId}`);
        }

        const params = getEditParams();
        const url = `${location.origin}/tiktok/post/edit/v1/?${params.toString()}`;

        let payload = nativeEditTemplate && typeof nativeEditTemplate === 'object'
            ? structuredClone(nativeEditTemplate)
            : null;

        if (!payload || typeof payload !== 'object') {
            payload = {
                aweme_id: String(awemeId),
                scene: 1,
                visibility: { visibility: selectedVisibility }
            };
        } else {
            payload.aweme_id = String(awemeId);
            if (payload.scene === undefined) payload.scene = 1;
            if (!payload.visibility || typeof payload.visibility !== 'object') {
                payload.visibility = {};
            }
            payload.visibility.visibility = selectedVisibility;
        }

        const headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/plain, */*',
            'agw-js-conv': 'str'
        };

        const csrf = getTikTokCsrfToken();
        if (csrf) headers['tt-csrf-token'] = csrf;

        const pageWindow = (typeof unsafeWindow !== 'undefined' && unsafeWindow) ? unsafeWindow : window;
        const pageFetch = pageWindow.fetch;
        if (typeof pageFetch !== 'function') {
            throw new Error('window.fetch TikTok est introuvable.');
        }

        internalEditRequest = true;
        let response;
        try {
            response = await pageFetch.call(pageWindow, url, {
                method: 'POST',
                credentials: 'include',
                cache: 'no-store',
                referrer: location.href,
                referrerPolicy: 'strict-origin-when-cross-origin',
                headers,
                body: JSON.stringify(payload)
            });
        } catch (error) {
            log('error', 'Edit-Visibility', `Erreur fetch pour ${awemeId} :`, error);
            throw new Error(`Échec du fetch TikTok : ${error.message || error}`);
        } finally {
            internalEditRequest = false;
        }

        const text = await response.text();
        if (response.status === 403) {
            const error = new Error('HTTP 403 — TikTok a refusé la requête.');
            error.status = 403;
            error.is403 = true;
            throw error;
        }
        if (response.status === 429) {
            const error = new Error('HTTP 429 — TikTok a limité les requêtes.');
            error.status = 429;
            error.is429 = true;
            throw error;
        }
        if (!response.ok) {
            const error = new Error(`HTTP ${response.status}`);
            error.status = response.status;
            throw error;
        }

        let json = null;
        try {
            json = JSON.parse(text);
        } catch {}

        if (json) {
            const code = json.status_code ?? json.statusCode ?? json.code ?? json.data?.status_code ?? json.data?.statusCode;
            if (code !== undefined && code !== null && Number(code) !== 0) {
                const error = new Error(`TikTok edit ${code}: ${json.status_msg || json.statusMsg || json.message || 'Erreur inconnue'}`);
                error.apiCode = Number(code);
                throw error;
            }
        }

        log('success', 'Edit-Visibility', `Modification envoyée avec succès pour ${awemeId}`);
        return { ok: true, status: response.status, json, targetVisibility: selectedVisibility };
    }

    async function testOnePrivate() {
        if (!isStudioPage()) {
            await showAlert('Attention', 'Ouvre TikTok Studio > Contenu.');
            return;
        }
        if (db.videos.length === 0) {
            await showAlert('Attention', 'Aucune cible playlist enregistrée.');
            return;
        }

        const target = normalizeVisibility(db.selectedVisibility);
        const targetLabel = getVisibilityLabel(target);

        if (!hasValidStudioScan()) await scanStudioAPI(true);
        if (!hasValidStudioScan()) {
            await showAlert('Erreur', '❌ Le scan Studio n’est pas complet.\n\nTest bloqué.');
            return;
        }

        const candidate = db.studioMatches.find(item => !studioItemMatchesTarget(item, target));
        if (!candidate) {
            await showAlert('Information', `Toutes les vidéos de la playlist sont déjà configurées sur : ${targetLabel}.`);
            return;
        }

        const id = String(candidate.id);
        const confirmed = await showConfirm(
            'TEST D’UNE SEULE VIDÉO',
            `ID : ${id}\n\nÉtat Studio actuel : ${getStudioItemStateLabel(candidate)}\n\nNouvelle visibilité demandée : ${targetLabel}\n\nContinuer ?`
        );

        if (!confirmed) return;

        try {
            setStatus(`🔬 Test ${id} → ${targetLabel}`);
            await setPrivate(id);

            const localMatch = db.studioMatches.find(item => String(item.id) === id);
            if (localMatch) {
                localMatch.visibility = target;
            }

            markProcessed(id, target);
            markAlreadyTarget(id, target);
            db.lastStudioRun = Date.now();
            saveDB();
            updatePanel();

            const finalItem = {
                id,
                visibility: target,
                status: candidate.status,
                canChangePrivacy: candidate.canChangePrivacy
            };

            setStatus(`✅ Modification réussie → ${targetLabel}`);
            await showAlert(
                '✅ MODIFICATION RÉUSSIE & VÉRIFIÉE',
                `ID : ${id}\nCible : ${targetLabel}\n\nNouvel état : ${getStudioItemStateLabel(finalItem)}`
            );
        } catch (error) {
            log('error', 'Test-1', `Erreur test ${id} :`, error);
            setStatus(`❌ Test : ${error.message}`);
            await showAlert('❌ LE TEST A ÉCHOUÉ', error.message);
        }
    }

    async function processStudio() {
        if (busy) return;
        if (db.videos.length === 0) {
            await showAlert('Attention', 'Aucune cible playlist enregistrée.');
            return;
        }

        const target = normalizeVisibility(db.selectedVisibility);
        const targetLabel = getVisibilityLabel(target);

        if (!hasValidStudioScan()) {
            await scanStudioAPI(true);
            if (!hasValidStudioScan()) return;
        }

        const candidates = db.studioMatches.filter(item => !studioItemMatchesTarget(item, target));
        if (!candidates.length) {
            await showAlert('Information', `Aucune vidéo à modifier pour ${targetLabel}.`);
            return;
        }

        const confirmed = await showConfirm(
            'MODIFICATION EN MASSE',
            `Cible : ${targetLabel}\nVidéos à modifier : ${candidates.length}\n\nContinuer ?`
        );

        if (!confirmed) return;

        busy = true;
        stopRequested = false;
        let sent = 0;
        let requestErrors = 0;

        try {
            for (let i = 0; i < candidates.length; i++) {
                if (stopRequested) break;
                const id = String(candidates[i].id);
                setStatus(`🚀 ${i + 1}/${candidates.length} — ${id}`);

                try {
                    await setPrivate(id);
                    sent++;
                    const localMatch = db.studioMatches.find(item => String(item.id) === id);
                    if (localMatch) localMatch.visibility = target;
                    markProcessed(id, target);
                    markAlreadyTarget(id, target);
                } catch (error) {
                    requestErrors++;
                    db.failed.push({
                        id,
                        targetVisibility: target,
                        targetLabel,
                        reason: error.message,
                        time: Date.now()
                    });
                    saveDB();
                    if (error.status === 403 || error.status === 429) {
                        stopRequested = true;
                        break;
                    }
                }

                if (i < candidates.length - 1 && !stopRequested) {
                    await sleep(EDIT_DELAY);
                }
            }

            db.lastStudioRun = Date.now();
            saveDB();
            updatePanel();
            setStatus(`🏁 ${sent} vidéo(s) modifiée(s) avec succès`);

            await showAlert(
                '🏁 MODIFICATION TERMINÉE',
                `Cible : ${targetLabel}\nRequêtes acceptées : ${sent}\nErreurs : ${requestErrors}`
            );
        } finally {
            busy = false;
            updatePanel();
        }
    }

    function saveCurrentPlaylistToLibrary() {
        if (!db.playlistId || !Array.isArray(db.videos) || db.videos.length === 0) return false;

        const saved = {
            playlistId: String(db.playlistId),
            playlistName: db.playlistName || '',
            username: db.username || '',
            expectedCount: Number(db.expectedCount || db.videos.length),
            videos: db.videos.map(video => ({
                id: String(video.id),
                desc: typeof video.desc === 'string' ? video.desc : '',
                createTime: Number(video.createTime || 0),
                authorUsername: typeof video.authorUsername === 'string' ? video.authorUsername : '',
                shareUrl: typeof video.shareUrl === 'string' ? video.shareUrl : ''
            })),
            lastScan: db.lastScan || Date.now(),
            scanComplete: db.expectedCount ? db.videos.length === db.expectedCount : true,
            savedAt: Date.now()
        };

        const existingIndex = db.savedPlaylists.findIndex(playlist => String(playlist.playlistId) === saved.playlistId);
        if (existingIndex >= 0) db.savedPlaylists[existingIndex] = saved;
        else db.savedPlaylists.push(saved);

        db.savedPlaylists = normalizeSavedPlaylists(db.savedPlaylists);
        saveDB();
        updateSavedPlaylistSelector();
        return true;
    }

    async function restoreSavedPlaylist(playlistId) {
        const saved = getSavedPlaylist(playlistId);
        if (!saved) {
            await showAlert('Erreur', 'Playlist sauvegardée introuvable.');
            return;
        }

        db.playlistId = saved.playlistId;
        db.playlistName = saved.playlistName || '';
        db.username = saved.username || '';
        db.expectedCount = Number(saved.expectedCount || saved.videos.length);
        db.videos = saved.videos.map(video => ({ ...video, id: String(video.id) }));
        db.studioMatches = [];
        db.lastStudioScan = null;
        db.lastStudioRun = null;
        db.lastScan = saved.lastScan || null;

        saveDB();
        updatePanel();
        log('success', 'Library', `Playlist restaurée : ${db.playlistName} (${db.videos.length} vidéos)`);
        setStatus(`📂 Playlist restaurée : ${db.playlistName || db.playlistId} — ${db.videos.length} vidéos`);
    }

    async function deleteSavedPlaylist(playlistId) {
        const saved = getSavedPlaylist(playlistId);
        if (!saved) return;

        const confirmed = await showConfirm(
            'SUPPRIMER LA PLAYLIST',
            `Supprimer la playlist de la bibliothèque ?\n\nPlaylist : ${saved.playlistName || playlistId}`
        );

        if (!confirmed) return;

        db.savedPlaylists = db.savedPlaylists.filter(playlist => String(playlist.playlistId) !== String(playlistId));
        saveDB();
        updateSavedPlaylistSelector();
        setStatus('🗑 Playlist supprimée de la bibliothèque');
    }

    async function clearDB() {
        const confirmed = await showConfirm(
            'EFFACER TOUTES LES DONNÉES',
            'Supprimer toutes les données sauvegardées ?'
        );

        if (!confirmed) return;

        GM_deleteValue(DB_KEY);
        db = structuredClone(EMPTY_DB);
        saveDB();
        updatePanel();
        updateSavedPlaylistSelector();
        setStatus('🗑️ Données supprimées');
    }

    function createPanel() {
        if (document.getElementById(PANEL_ID)) return;

        log('info', 'UI', 'Injection de l\'interface utilisateur dans la page...');

        const panel = document.createElement('div');
        panel.id = PANEL_ID;
        panel.style.cssText = `
            position:fixed; top:20px; right:20px; width:420px;
            max-height:calc(100vh - 40px); overflow-y:auto; overflow-x:hidden;
            z-index:2147483647; background:rgba(20,20,20,.97);
            border:2px solid #25F4EE; border-radius:12px; padding:14px;
            color:white; font-family:Arial,sans-serif;
            box-shadow:0 8px 30px rgba(0,0,0,.65); box-sizing:border-box;
        `;

        panel.innerHTML = `
            <div id="ttpm23-header" style="color:#25F4EE; font-weight:bold; text-align:center; font-size:16px; padding-bottom:9px; border-bottom:1px solid #333; cursor:move;">
                🔒 TikTok Playlist Manager v2.7.5
            </div>

            <div style="margin-top:10px; background:#111; padding:10px; border-radius:7px;">
                <div style="font-weight:bold; font-size:12px; margin-bottom:7px;">📚 Playlists sauvegardées</div>
                <select id="ttpm23-playlist-library" style="width:100%; box-sizing:border-box; padding:9px; border-radius:6px; border:1px solid #555; background:#222; color:white; font-size:12px; margin-bottom:6px; cursor:pointer;">
                    <option value="">📚 Aucune playlist sauvegardée</option>
                </select>
                <div id="ttpm23-library-count" style="text-align:center; color:#999; font-size:11px; margin-bottom:7px;">0 playlist sauvegardée</div>
                <button id="ttpm23-restore-playlist" style="width:100%; padding:9px; border:0; border-radius:6px; background:#3498DB; color:white; font-weight:bold; cursor:pointer; margin-bottom:6px;">📂 Restaurer la playlist sélectionnée</button>
                <button id="ttpm23-save-playlist" style="width:100%; padding:9px; border:0; border-radius:6px; background:#27AE60; color:white; font-weight:bold; cursor:pointer; margin-bottom:6px;">💾 Sauvegarder la playlist actuelle</button>
                <button id="ttpm23-delete-playlist" style="width:100%; padding:8px; border:0; border-radius:6px; background:#555; color:#ddd; font-weight:bold; cursor:pointer;">🗑️ Supprimer la playlist sélectionnée</button>
            </div>

            <div style="margin-top:10px; background:#111; padding:10px; border-radius:7px;">
                <div style="font-weight:bold; font-size:12px; margin-bottom:7px;">🎯 Choisir la visibilité cible</div>
                <select id="ttpm23-visibility" style="width:100%; box-sizing:border-box; padding:9px; border-radius:6px; border:1px solid #555; background:#222; color:white; font-size:13px; font-weight:bold; cursor:pointer;">
                    <option value="1">🔒 1 — Privé / Moi uniquement</option>
                    <option value="0">🌍 0 — Public / Followers</option>
                    <option value="2">👥 2 — Amis</option>
                </select>
                <div id="ttpm23-target-label" style="margin-top:8px; text-align:center; color:#25F4EE; font-weight:bold; font-size:12px;"></div>
            </div>

            <div id="ttpm23-status" style="text-align:center; color:#bbb; font-size:12px; margin:10px 0; min-height:32px;">🟢 Prêt</div>
            <div id="ttpm23-info" style="background:#111; padding:10px; border-radius:7px; font-size:12px; line-height:1.7; margin-bottom:10px;"></div>

            <button id="ttpm23-test" style="width:100%; padding:9px; border:0; border-radius:6px; background:#666; color:white; font-weight:bold; cursor:pointer; margin-bottom:6px;">🧪 Tester l'API Playlist</button>
            <button id="ttpm23-scan" style="width:100%; padding:10px; border:0; border-radius:6px; background:#25F4EE; color:#000; font-weight:bold; cursor:pointer; margin-bottom:6px;">📥 Récupérer les vidéos</button>
            <button id="ttpm23-studio-scan" style="width:100%; padding:10px; border:0; border-radius:6px; background:#9B59B6; color:white; font-weight:bold; cursor:pointer; margin-bottom:6px;">🔎 Analyser Studio</button>
            <button id="ttpm23-test-private" style="width:100%; padding:10px; border:0; border-radius:6px; background:#E67E22; color:white; font-weight:bold; cursor:pointer; margin-bottom:6px;">🔬 Tester 1 vidéo</button>
            <button id="ttpm23-private" style="width:100%; padding:11px; border:0; border-radius:6px; background:#FE2C55; color:white; font-weight:bold; cursor:pointer; margin-bottom:6px;">🚀 Appliquer aux correspondances</button>

            <button id="ttpm23-toggle-debug" style="width:100%; padding:8px; border:0; border-radius:6px; background:#444; color:#25F4EE; font-weight:bold; cursor:pointer; margin-top:6px;">🐞 Mode Debug Console : ON</button>
            <button id="ttpm23-clear" style="width:100%; padding:7px; border:0; border-radius:6px; background:#333; color:#aaa; font-weight:bold; cursor:pointer; margin-top:8px;">🗑 Effacer toutes les données</button>
        `;

        document.body.appendChild(panel);

        document.getElementById('ttpm23-test').onclick = testAPI;
        document.getElementById('ttpm23-scan').onclick = scanPlaylistAPI;
        document.getElementById('ttpm23-studio-scan').onclick = async () => {
            try {
                await scanStudioAPI(true);
            } catch (error) {
                log('error', 'UI', 'Erreur lors du Scan Studio :', error);
            }
        };
        document.getElementById('ttpm23-test-private').onclick = testOnePrivate;
        document.getElementById('ttpm23-private').onclick = processStudio;
        document.getElementById('ttpm23-clear').onclick = clearDB;

        const debugBtn = document.getElementById('ttpm23-toggle-debug');
        debugBtn.onclick = () => {
            debugMode = !debugMode;
            debugBtn.textContent = `🐞 Mode Debug Console : ${debugMode ? 'ON' : 'OFF'}`;
            debugBtn.style.color = debugMode ? '#25F4EE' : '#888';
            log('info', 'UI', `Mode debug console basculé sur : ${debugMode}`);
        };

        document.getElementById('ttpm23-visibility').addEventListener('change', event => {
            const visibility = normalizeVisibility(event.target.value);
            db.selectedVisibility = visibility;
            saveDB();
            updatePanel();
            setStatus(`🎯 Cible : ${getVisibilityLabel(visibility)}`);
        });

        document.getElementById('ttpm23-restore-playlist').onclick = async () => {
            const select = document.getElementById('ttpm23-playlist-library');
            if (!select || !select.value) {
                await showAlert('Attention', 'Sélectionne une playlist sauvegardée.');
                return;
            }
            restoreSavedPlaylist(select.value);
        };

        document.getElementById('ttpm23-save-playlist').onclick = () => {
            if (saveCurrentPlaylistToLibrary()) {
                showAlert('✅ PLAYLIST SAUVEGARDÉE', `Playlist : ${db.playlistName || db.playlistId}`);
            } else {
                showAlert('Attention', 'Aucune playlist chargée.');
            }
        };

        document.getElementById('ttpm23-delete-playlist').onclick = async () => {
            const select = document.getElementById('ttpm23-playlist-library');
            if (!select || !select.value) {
                await showAlert('Attention', 'Sélectionne une playlist sauvegardée.');
                return;
            }
            deleteSavedPlaylist(select.value);
        };

        makeDraggable(panel);
        updatePanel();
        updateVisibilityControls();
        updateSavedPlaylistSelector();
        log('success', 'UI', 'Interface utilisateur injectée avec succès.');
    }

    function updateVisibilityControls() {
        const select = document.getElementById('ttpm23-visibility');
        const testButton = document.getElementById('ttpm23-test-private');
        const processButton = document.getElementById('ttpm23-private');
        const title = document.getElementById('ttpm23-target-label');

        const visibility = normalizeVisibility(db.selectedVisibility);
        const label = getVisibilityLabel(visibility);

        if (select) select.value = String(visibility);
        if (title) title.textContent = `🎯 Cible : ${label}`;
        if (testButton) testButton.textContent = `🔬 Tester 1 vidéo → ${label}`;
        if (processButton) processButton.textContent = `🚀 Appliquer aux correspondances → ${label}`;
    }

    function updateSavedPlaylistSelector() {
        const select = document.getElementById('ttpm23-playlist-library');
        const countLabel = document.getElementById('ttpm23-library-count');
        if (!select) return;

        const playlists = normalizeSavedPlaylists(db.savedPlaylists);
        db.savedPlaylists = playlists;
        const previous = select.value;

        select.innerHTML = '';
        const empty = document.createElement('option');
        empty.value = '';
        empty.textContent = playlists.length ? '📚 Choisir une playlist sauvegardée' : '📚 Aucune playlist sauvegardée';
        select.appendChild(empty);

        for (const playlist of playlists) {
            const option = document.createElement('option');
            option.value = String(playlist.playlistId);
            option.textContent = `${playlist.scanComplete ? '✅' : '⚠️'} ${playlist.playlistName || playlist.playlistId} — ${playlist.videos.length} vidéos`;
            select.appendChild(option);
        }

        if (previous && playlists.some(p => String(p.playlistId) === String(previous))) {
            select.value = previous;
        } else if (db.playlistId && playlists.some(p => String(p.playlistId) === String(db.playlistId))) {
            select.value = String(db.playlistId);
        }

        if (countLabel) {
            countLabel.textContent = `${playlists.length} playlist${playlists.length > 1 ? 's' : ''} sauvegardée${playlists.length > 1 ? 's' : ''}`;
        }
    }

    function updatePanel() {
        const info = document.getElementById('ttpm23-info');
        if (!info) return;

        const visibility = normalizeVisibility(db.selectedVisibility);
        const targetLabel = getVisibilityLabel(visibility);
        const targets = db.videos.length;
        const matches = db.studioMatches.length;
        const processed = getProcessedList(visibility).length;
        const alreadyTarget = getAlreadyTargetList(visibility).length;
        const errors = db.failed.length;
        const saved = db.savedPlaylists.length;

        info.innerHTML = `
            <div>🎯 Cible : <b>${escapeHTML(targetLabel)}</b></div>
            <div>📂 Playlist : <b>${escapeHTML(db.playlistName || '—')}</b></div>
            <div>🆔 ID : <b>${escapeHTML(db.playlistId || '—')}</b></div>
            <div>🎞️ Cibles : <b>${targets}${db.expectedCount ? ` / ${db.expectedCount}` : ''}</b></div>
            <div>🔎 Studio : <b>${matches}${hasValidStudioScan() ? ' ✅' : ' ⚠️'}</b></div>
            <div>📚 Playlists sauvegardées : <b>${saved}</b></div>
            <div>✅ Traitées (Cible actuelle) : <b>${processed}</b></div>
            <div>🎯 Déjà dans la cible : <b>${alreadyTarget}</b></div>
            <div>❌ Erreurs : <b>${errors}</b></div>
        `;
        updateVisibilityControls();
    }

    function setStatus(msg) {
        const el = document.getElementById('ttpm23-status');
        if (el) el.textContent = msg;
    }

    function makeDraggable(el) {
        const header = document.getElementById('ttpm23-header');
        if (!header) return;

        let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
        header.onmousedown = dragMouseDown;

        function dragMouseDown(e) {
            e = e || window.event;
            e.preventDefault();
            pos3 = e.clientX;
            pos4 = e.clientY;
            document.onmouseup = closeDragElement;
            document.onmousemove = elementDrag;
        }

        function elementDrag(e) {
            e = e || window.event;
            e.preventDefault();
            pos1 = pos3 - e.clientX;
            pos2 = pos4 - e.clientY;
            pos3 = e.clientX;
            pos4 = e.clientY;
            el.style.top = (el.offsetTop - pos2) + "px";
            el.style.left = (el.offsetLeft - pos1) + "px";
            el.style.right = 'auto';
        }

        function closeDragElement() {
            document.onmouseup = null;
            document.onmousemove = null;
        }
    }

    function init() {
        log('info', 'Init', `URL actuelle : ${location.href}`);
        if (document.body) {
            createPanel();
        } else {
            window.addEventListener('DOMContentLoaded', () => {
                log('info', 'Init', 'Événement DOMContentLoaded déclenché.');
                createPanel();
            });
        }
    }

    init();
})();