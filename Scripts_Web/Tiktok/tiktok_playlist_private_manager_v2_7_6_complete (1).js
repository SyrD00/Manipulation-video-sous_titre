// ==UserScript==
// @name         TikTok Playlist Private Manager v3.4
// @namespace    https://tampermonkey.net/
// @version      3.4
// @description  Récupère toutes les vidéos d’une playlist TikTok, les retrouve dans Studio, détecte rigoureusement les droits d'auteur/DMCA et modérations, ignore les vidéos restreintes/supprimées et modifie uniquement les vidéos saines.
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
        '%c[TTPM v3.4] 🚀 UserScript injecté et en cours d\'initialisation...',
        'background: #111; color: #25F4EE; font-weight: bold; font-size: 13px; padding: 4px 8px; border-radius: 4px; border: 1px solid #25F4EE;'
    );

    // ============================================================
    // CONFIGURATION
    // ============================================================

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

    // Version de la logique de classification (Incrémentée à 4).
    // Force l'invalidation des anciens scans réalisés avec une logique incomplète.
    const STUDIO_CLASSIFICATION_VERSION = 4;

    const PANEL_ID = 'tt-private-manager-v24';

    let debugMode = true;
    let busy = false;
    let stopRequested = false;

    // ============================================================
    // VISIBILITÉS
    // ============================================================

    const VISIBILITY = {
        PUBLIC_FOLLOWERS: 0,
        ONLY_ME: 1,
        FRIENDS: 2
    };

    const DEFAULT_VISIBILITY = VISIBILITY.ONLY_ME;

    // ============================================================
    // BASE DE DONNÉES
    // ============================================================

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

        processedByVisibility: {
            '0': [],
            '1': [],
            '2': []
        },

        alreadyTargetByVisibility: {
            '0': [],
            '1': [],
            '2': []
        },

        savedPlaylists: [],

        missingFromStudio: [],

        studioScanComplete: false,

        studioClassificationVersion:
            STUDIO_CLASSIFICATION_VERSION
    };

    let db;

    // ============================================================
    // MODÈLE DE REQUÊTE D'ÉDITION NATIF
    // ============================================================

    let nativeEditTemplate = null;
    let nativeEditParamsTemplate = null;
    let internalEditRequest = false;

    // ============================================================
    // LOGGING
    // ============================================================

    function log(type, tag, message, data = null) {
        if (!debugMode && type === 'info') {
            return;
        }

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

    // ============================================================
    // INITIALISATION DB
    // ============================================================

    function cloneEmptyDB() {
        return JSON.parse(JSON.stringify(EMPTY_DB));
    }

    function normalizeVisibility(value) {
        const n = Number(value);
        if ([0, 1, 2].includes(n)) return n;
        return DEFAULT_VISIBILITY;
    }

    function getVisibilityLabel(value) {
        const v = normalizeVisibility(value);
        if (v === VISIBILITY.PUBLIC_FOLLOWERS) return 'Public / Followers';
        if (v === VISIBILITY.ONLY_ME) return 'Privé / Moi uniquement';
        return 'Amis';
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
        const byId = new Map();
        for (const raw of source) {
            const playlist = normalizeSavedPlaylist(raw);
            if (playlist) byId.set(playlist.playlistId, playlist);
        }
        return Array.from(byId.values());
    }

    function loadDB() {
        try {
            const raw = GM_getValue(DB_KEY, '');
            if (!raw) return cloneEmptyDB();

            let parsed = typeof raw === 'string' ? JSON.parse(raw) : raw;
            const loaded = { ...cloneEmptyDB(), ...parsed };

            loaded.videos = Array.isArray(loaded.videos) ? loaded.videos : [];
            loaded.processed = Array.isArray(loaded.processed) ? loaded.processed : [];
            loaded.alreadyPrivate = Array.isArray(loaded.alreadyPrivate) ? loaded.alreadyPrivate : [];
            loaded.failed = Array.isArray(loaded.failed) ? loaded.failed : [];
            loaded.studioMatches = Array.isArray(loaded.studioMatches) ? loaded.studioMatches : [];
            loaded.selectedVisibility = normalizeVisibility(loaded.selectedVisibility);
            loaded.processedByVisibility = normalizeVisibilityMap(loaded.processedByVisibility);
            loaded.alreadyTargetByVisibility = normalizeVisibilityMap(loaded.alreadyTargetByVisibility);
            loaded.savedPlaylists = normalizeSavedPlaylists(loaded.savedPlaylists);
            loaded.missingFromStudio = Array.isArray(loaded.missingFromStudio)
                ? Array.from(new Set(loaded.missingFromStudio.map(id => String(id))))
                : [];
            loaded.studioScanComplete = Boolean(loaded.studioScanComplete);

            // IMPORTANT : Rénitialisation si la version a changé (passage à la v4)
            if (Number(loaded.studioClassificationVersion) !== STUDIO_CLASSIFICATION_VERSION) {
                loaded.studioMatches = [];
                loaded.lastStudioScan = null;
                loaded.lastStudioRun = null;
                loaded.missingFromStudio = [];
                loaded.studioScanComplete = false;
                loaded.studioClassificationVersion = STUDIO_CLASSIFICATION_VERSION;
            }

            log('success', 'DB-Load', `Base chargée : ${loaded.videos.length} vidéo(s).`, loaded);
            return loaded;
        } catch (error) {
            log('error', 'DB-Load', 'Erreur chargement DB.', error);
            return cloneEmptyDB();
        }
    }

    db = loadDB();

    // ============================================================
    // OUTILS GÉNÉRAUX
    // ============================================================

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

    function getLanguage() {
        return (navigator.language || document.documentElement.lang || 'fr').split('-')[0].toLowerCase();
    }

    function showAlert(title, message) {
        return new Promise(resolve => {
            const overlay = document.createElement('div');
            overlay.style.cssText = `
                position:fixed; inset:0; background:rgba(0,0,0,.75); z-index:2147483647;
                display:flex; align-items:center; justify-content:center; font-family:Arial,sans-serif;
            `;

            const box = document.createElement('div');
            box.style.cssText = `
                background:#1a1a1a; border:2px solid #25F4EE; border-radius:12px;
                padding:20px; max-width:450px; width:90%; color:white; box-shadow:0 10px 30px rgba(0,0,0,.8);
            `;

            box.innerHTML = `
                <h3 style="margin:0 0 15px; color:#25F4EE; font-size:17px;">${escapeHTML(title)}</h3>
                <div style="font-size:13px; line-height:1.5; white-space:pre-wrap; word-break:break-word; max-height:350px; overflow-y:auto; margin-bottom:16px;">
                    ${escapeHTML(message)}
                </div>
                <button id="ttpm-alert-ok" style="width:100%; padding:9px; background:#25F4EE; color:#000; border:0; border-radius:6px; font-weight:bold; cursor:pointer;">OK</button>
            `;

            overlay.appendChild(box);
            document.body.appendChild(overlay);
            box.querySelector('#ttpm-alert-ok').onclick = () => { overlay.remove(); resolve(true); };
        });
    }

    function showConfirm(title, message) {
        return new Promise(resolve => {
            const overlay = document.createElement('div');
            overlay.style.cssText = `
                position:fixed; inset:0; background:rgba(0,0,0,.75); z-index:2147483647;
                display:flex; align-items:center; justify-content:center; font-family:Arial,sans-serif;
            `;

            const box = document.createElement('div');
            box.style.cssText = `
                background:#1a1a1a; border:2px solid #FE2C55; border-radius:12px;
                padding:20px; max-width:450px; width:90%; color:white; box-shadow:0 10px 30px rgba(0,0,0,.8);
            `;

            box.innerHTML = `
                <h3 style="margin:0 0 15px; color:#FE2C55; font-size:17px;">${escapeHTML(title)}</h3>
                <div style="font-size:13px; line-height:1.5; white-space:pre-wrap; word-break:break-word; max-height:350px; overflow-y:auto; margin-bottom:16px;">
                    ${escapeHTML(message)}
                </div>
                <div style="display:flex; gap:10px;">
                    <button id="ttpm-confirm-no" style="flex:1; padding:9px; background:#444; color:white; border:0; border-radius:6px; font-weight:bold; cursor:pointer;">Annuler</button>
                    <button id="ttpm-confirm-yes" style="flex:1; padding:9px; background:#FE2C55; color:white; border:0; border-radius:6px; font-weight:bold; cursor:pointer;">Confirmer</button>
                </div>
            `;

            overlay.appendChild(box);
            document.body.appendChild(overlay);

            box.querySelector('#ttpm-confirm-no').onclick = () => { overlay.remove(); resolve(false); };
            box.querySelector('#ttpm-confirm-yes').onclick = () => { overlay.remove(); resolve(true); };
        });
    }

    // ============================================================
    // PROCESSED / ALREADY TARGET
    // ============================================================

    function getProcessedList(visibility = db.selectedVisibility) {
        const key = String(normalizeVisibility(visibility));
        if (!db.processedByVisibility || typeof db.processedByVisibility !== 'object') {
            db.processedByVisibility = normalizeVisibilityMap(null);
        }
        if (!Array.isArray(db.processedByVisibility[key])) db.processedByVisibility[key] = [];
        return db.processedByVisibility[key];
    }

    function getAlreadyTargetList(visibility = db.selectedVisibility) {
        const key = String(normalizeVisibility(visibility));
        if (!db.alreadyTargetByVisibility || typeof db.alreadyTargetByVisibility !== 'object') {
            db.alreadyTargetByVisibility = normalizeVisibilityMap(null);
        }
        if (!Array.isArray(db.alreadyTargetByVisibility[key])) db.alreadyTargetByVisibility[key] = [];
        return db.alreadyTargetByVisibility[key];
    }

    function syncLegacyArrays() {
        const visibility = normalizeVisibility(db.selectedVisibility);
        db.selectedVisibility = visibility;
        db.processed = Array.from(getProcessedList(visibility));
        db.alreadyPrivate = Array.from(getAlreadyTargetList(visibility));
    }

    function saveDB() {
        syncLegacyArrays();
        db.savedPlaylists = normalizeSavedPlaylists(db.savedPlaylists);
        GM_setValue(DB_KEY, JSON.stringify(db));
    }

    function markProcessed(id, visibility = db.selectedVisibility) {
        addUnique(getProcessedList(visibility), String(id));
        syncLegacyArrays();
    }

    function setAlreadyTargetList(ids, visibility = db.selectedVisibility) {
        const key = String(normalizeVisibility(visibility));
        db.alreadyTargetByVisibility[key] = Array.from(new Set((ids || []).map(id => String(id))));
        syncLegacyArrays();
    }

    // ============================================================
    // PLAYLIST / URL
    // ============================================================

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
        try { return decodeURIComponent(match[1]); } catch { return match[1]; }
    }

    function isPlaylistPage() {
        return location.pathname.includes('/playlist/');
    }

    function isStudioPage() {
        return location.pathname.includes('/tiktokstudio/content') || location.pathname.includes('/tiktokstudio');
    }

    function normalizeVideo(video) {
        if (!video || typeof video !== 'object') return null;

        const candidates = [
            video.id, video.itemId, video.item_id, video.videoId, video.video_id, video.awemeId, video.aweme_id,
            video.item?.id, video.item?.itemId, video.item?.item_id,
            video.video?.id, video.video?.videoId,
            video.aweme_info?.aweme_id, video.aweme_info?.id
        ];

        let id = '';
        for (const candidate of candidates) {
            if (candidate === undefined || candidate === null) continue;
            const value = String(candidate);
            if (/^\d{15,25}$/.test(value)) { id = value; break; }
        }

        if (!id) return null;

        const author = video.author || video.author_info || {};
        const authorUsername = author.uniqueId || author.unique_id || '';

        return {
            id,
            desc: typeof video.desc === 'string' ? video.desc : '',
            createTime: Number(video.createTime || video.create_time || 0),
            authorUsername,
            shareUrl: authorUsername ? `https://www.tiktok.com/@${authorUsername}/video/${id}` : `https://www.tiktok.com/video/${id}`
        };
    }

    // ============================================================
    // PLAYLIST API
    // ============================================================

    async function getPlaylistDetail(playlistId) {
        const params = new URLSearchParams();
        params.set('mixId', String(playlistId));
        params.set('aid', '1988');
        params.set('language', getLanguage());
        const url = `${location.origin}/api/mix/detail/?${params.toString()}`;

        const response = await fetch(url, {
            method: 'GET', credentials: 'include', cache: 'no-store',
            headers: {
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': navigator.language || 'fr-FR'
            }
        });

        const text = await response.text();
        let data = null;
        try { data = JSON.parse(text); } catch {}

        if (!response.ok) {
            const code = data?.statusCode ?? data?.status_code;
            const msg = data?.statusMsg || data?.status_msg || '';
            throw new Error(`HTTP ${response.status}${code !== undefined ? ` — TikTok ${code}` : ''}${msg ? `: ${msg}` : ''}`);
        }

        const code = data?.statusCode ?? data?.status_code;
        if (code !== undefined && Number(code) !== 0) {
            throw new Error(`TikTok API ${code}: ${data.statusMsg || data.status_msg || 'Erreur inconnue'}`);
        }

        return data;
    }

    async function getPlaylistPage(playlistId, cursor) {
        const params = new URLSearchParams();
        params.set('mixId', String(playlistId));
        params.set('count', String(PLAYLIST_PAGE_SIZE));
        params.set('cursor', String(cursor));
        params.set('aid', '1988');
        params.set('language', getLanguage());
        const url = `${location.origin}/api/mix/item_list/?${params.toString()}`;

        const response = await fetch(url, {
            method: 'GET', credentials: 'include', cache: 'no-store',
            headers: {
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': navigator.language || 'fr-FR'
            }
        });

        const text = await response.text();
        let json = null;
        try { json = JSON.parse(text); } catch {}

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}${json?.statusCode || json?.status_code ? ` — TikTok ${json.statusCode ?? json.status_code}` : ''}${json?.statusMsg || json?.status_msg ? `: ${json.statusMsg || json.status_msg}` : ''}`);
        }

        const code = json?.statusCode ?? json?.status_code;
        if (code !== undefined && Number(code) !== 0) {
            throw new Error(`TikTok API ${code}: ${json.statusMsg || json.status_msg || 'Erreur inconnue'}`);
        }

        return json;
    }

    function extractPlaylistItems(result) {
        const candidates = [
            result?.itemList, result?.item_list, result?.mixItemList, result?.mix_item_list, result?.items, result?.mix_items, result?.mixItems, result?.aweme_list,
            result?.data?.itemList, result?.data?.item_list, result?.data?.mixItemList, result?.data?.mix_item_list, result?.data?.items, result?.data?.mix_items, result?.data?.mixItems, result?.data?.aweme_list
        ];

        for (const candidate of candidates) {
            if (Array.isArray(candidate)) return candidate;
        }
        return [];
    }

    async function scanPlaylistAPI() {
        log('action', 'Playlist', 'Début scan playlist.');

        if (!isPlaylistPage()) {
            await showAlert('Attention', 'Ouvre d’abord la page de la playlist TikTok.');
            return;
        }

        const playlistId = getPlaylistIdFromURL();
        if (!playlistId) {
            await showAlert('Erreur', 'Impossible de trouver l’ID de la playlist dans l’URL.');
            return;
        }

        const previousPlaylistId = String(db.playlistId || '');
        const samePlaylist = previousPlaylistId === String(playlistId);
        const savedPlaylists = normalizeSavedPlaylists(db.savedPlaylists);
        const selectedVisibility = normalizeVisibility(db.selectedVisibility);

        db.playlistId = String(playlistId);
        db.username = getUsernameFromURL();
        db.selectedVisibility = selectedVisibility;
        db.savedPlaylists = savedPlaylists;

        if (!samePlaylist) {
            db.processedByVisibility = { '0': [], '1': [], '2': [] };
            db.alreadyTargetByVisibility = { '0': [], '1': [], '2': [] };
            db.processed = []; db.alreadyPrivate = []; db.failed = [];
        }

        db.studioMatches = [];
        db.lastStudioScan = null;
        db.lastStudioRun = null;
        db.missingFromStudio = [];
        db.studioScanComplete = false;
        db.studioClassificationVersion = STUDIO_CLASSIFICATION_VERSION;

        saveDB();
        updatePanel();
        setStatus('🔎 Lecture de la playlist...');

        let detail;
        try {
            detail = await getPlaylistDetail(playlistId);
        } catch (error) {
            log('error', 'Playlist', 'Erreur Detail API.', error);
            await showAlert('❌ Erreur API Playlist', error.message);
            return;
        }

        const mixInfo = detail?.mixInfo || detail?.mix_info || detail?.data?.mixInfo || detail?.data?.mix_info || {};
        db.playlistName = mixInfo.mixName || mixInfo.mix_name || mixInfo.name || mixInfo.title || '';
        db.expectedCount = Number(mixInfo.videoCount || mixInfo.video_count || 0);

        const videos = [];
        const seen = new Set();
        let cursor = 0;
        let hasMore = true;
        let page = 0;

        while (hasMore && page < PLAYLIST_MAX_PAGES) {
            page++;
            setStatus(`📥 Playlist — page ${page} — ${videos.length} / ${db.expectedCount || '?'}`);

            let result;
            try {
                result = await getPlaylistPage(playlistId, cursor);
            } catch (error) {
                log('error', 'Playlist', `Erreur page ${page}.`, error);
                break;
            }

            const items = extractPlaylistItems(result);
            for (const rawItem of items) {
                const video = normalizeVideo(rawItem);
                if (!video || seen.has(video.id)) continue;
                seen.add(video.id);
                videos.push(video);
            }

            hasMore = Boolean(result?.hasMore ?? result?.has_more ?? result?.data?.hasMore ?? result?.data?.has_more ?? false);
            const nextCursor = result?.cursor ?? result?.data?.cursor;

            if (!hasMore || nextCursor === undefined || nextCursor === null || String(nextCursor) === String(cursor)) break;
            cursor = nextCursor;

            if (db.expectedCount > 0 && videos.length >= db.expectedCount) break;
            await sleep(PLAYLIST_PAGE_DELAY);
        }

        if (videos.length === 0) {
            await showAlert('❌ Aucune vidéo trouvée', `Playlist :\n${db.playlistName || db.playlistId}\n\nAttendues :\n${db.expectedCount || '?'}\n\nAucune modification effectuée.`);
            return;
        }

        db.videos = videos;
        db.lastScan = Date.now();
        db.studioMatches = [];
        db.lastStudioScan = null;
        db.lastStudioRun = null;
        db.missingFromStudio = [];
        db.studioScanComplete = false;

        saveDB();
        saveCurrentPlaylistToLibrary();
        updatePanel();

        setStatus(`✅ Playlist récupérée : ${videos.length} / ${db.expectedCount || '?'}`);

        if (db.expectedCount > 0 && videos.length !== db.expectedCount) {
            await showAlert('⚠️ Playlist partielle', `Trouvées :\n${videos.length}\n\nAttendues :\n${db.expectedCount}\n\nLe scan s’arrête ici afin de ne pas inventer d’IDs.`);
        } else {
            await showAlert('✅ Playlist récupérée', `Playlist :\n${db.playlistName || db.playlistId}\n\nVidéos :\n${videos.length}\n\n💾 Sauvegarde automatique effectuée.`);
        }
    }

    async function testAPI() {
        if (!isPlaylistPage()) {
            await showAlert('Attention', 'Ouvre d’abord la playlist.');
            return;
        }
        const playlistId = getPlaylistIdFromURL();
        if (!playlistId) {
            await showAlert('Erreur', 'ID playlist introuvable.');
            return;
        }

        try {
            const detail = await getPlaylistDetail(playlistId);
            const page = await getPlaylistPage(playlistId, 0);
            const items = extractPlaylistItems(page);
            const mixInfo = detail?.mixInfo || detail?.data?.mixInfo || {};
            await showAlert('✅ TEST API RÉUSSI', `Playlist :\n${mixInfo.name || mixInfo.mixName || mixInfo.title || '—'}\n\nNombre indiqué par TikTok :\n${mixInfo.videoCount || mixInfo.video_count || '—'}\n\nPremière page :\n${items.length}`);
        } catch (error) {
            await showAlert('❌ TEST API ÉCHOUÉ', error.message);
        }
    }

    // ============================================================
    // COOKIE / PARAMÈTRES STUDIO
    // ============================================================

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
        const names = ['tt_csrf_token', 'tt-csrf-token'];
        for (const name of names) {
            const value = getCookieValue(name);
            if (value) return value;
        }
        try {
            const metaNames = ['tt-csrf-token', 'csrf-token'];
            for (const name of metaNames) {
                const meta = document.querySelector(`meta[name="${name}"]`);
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
            browser_language: navigator.language || 'fr-FR',
            browser_platform: navigator.platform || 'Win32',
            browser_name: 'Mozilla',
            browser_version: browserVersion,
            browser_online: 'true',
            cookie_enabled: 'true',
            screen_width: String(screen.width || 1366),
            screen_height: String(screen.height || 768),
            os: /Mac/i.test(navigator.platform || '') ? 'mac' : 'win',
            user_is_login: 'true',
            priority_region: 'SN',
            region: 'FR'
        };

        for (const [key, value] of Object.entries(defaults)) {
            params.set(key, String(value));
        }

        const msToken = getCookieValue('msToken');
        if (msToken) params.set('msToken', msToken);
        const deviceId = getCookieValue('device_id');
        if (deviceId) params.set('device_id', deviceId);

        try { params.set('tz_name', Intl.DateTimeFormat().resolvedOptions().timeZone || 'Atlantic/Reykjavik'); }
        catch { params.set('tz_name', 'Atlantic/Reykjavik'); }

        return params;
    }

    // ============================================================
    // STUDIO API
    // ============================================================

    async function getStudioPageSingleRequest(cursor, sortOrder) {
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
            method: 'POST', credentials: 'include', cache: 'no-store',
            headers: { 'Content-Type': 'application/json', 'Accept': 'application/json, text/plain, */*' },
            body: JSON.stringify(body)
        });

        const text = await response.text();

        if (response.status === 403) {
            const error = new Error('Studio HTTP 403');
            error.status = 403; error.is403 = true; throw error;
        }
        if (response.status === 429) {
            const error = new Error('Studio HTTP 429');
            error.status = 429; error.is429 = true; throw error;
        }
        if (!response.ok) {
            const error = new Error(`Studio HTTP ${response.status}`);
            error.status = response.status; throw error;
        }

        let json;
        try { json = JSON.parse(text); } catch { throw new Error('Réponse Studio non JSON.'); }

        const code = json.status_code ?? json.statusCode;
        if (code !== undefined && Number(code) !== 0) {
            const error = new Error(`Studio API ${code}: ${json.status_msg || json.statusMsg || 'Erreur inconnue'}`);
            error.apiCode = Number(code);
            if (Number(code) === 1 && Number(cursor) >= 900) error.isPaginationLimit = true;
            throw error;
        }

        return json;
    }

    async function getStudioPage(cursor, sortOrder) {
        let lastError = null;
        for (let attempt = 1; attempt <= API_MAX_RETRIES; attempt++) {
            try { return await getStudioPageSingleRequest(cursor, sortOrder); }
            catch (error) {
                lastError = error;
                if (error.is403 || error.is429 || error.isPaginationLimit) throw error;
                log('warn', 'Studio', `Tentative ${attempt}/${API_MAX_RETRIES} échouée : ${error.message}`);
                if (attempt < API_MAX_RETRIES) await sleep(1000 * attempt);
            }
        }
        throw (lastError || new Error('Erreur réseau Studio répétée.'));
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

    // ============================================================
    // VISIBILITÉ : OPTIONS ET PERMISSIONS
    // ============================================================

    function getVisibilityOptionKeys(targetVisibility) {
        const target = normalizeVisibility(targetVisibility);
        if (target === VISIBILITY.ONLY_ME) return ['visibility_only_you', 'visibility_only_me'];
        if (target === VISIBILITY.FRIENDS) return ['visibility_friends'];
        return ['visibility_everyone', 'visibility_followers'];
    }

    function getTargetVisibilityOption(item, targetVisibility) {
        const permissions = item?.permissions || {};
        const changePrivacy = permissions.can_change_privacy ?? permissions.canChangePrivacy ?? item?.changePrivacy;
        const options = changePrivacy?.visibility_options || changePrivacy?.visibilityOptions || {};
        const keys = getVisibilityOptionKeys(targetVisibility);
        const entries = [];

        for (const key of keys) {
            const entry = options?.[key];
            if (entry && typeof entry === 'object') entries.push({ key, entry });
        }
        return entries;
    }

    function inspectPrivacyPermission(item, targetVisibility) {
        const permissions = item?.permissions || {};
        const raw = permissions.can_change_privacy ?? permissions.canChangePrivacy ?? item?.changePrivacy;

        if (raw === false) return { canChange: false, reason: 'TikTok indique can_change_privacy=false.' };
        if (raw && typeof raw === 'object') {
            if (raw.can_change === false || raw.canChange === false) return { canChange: false, reason: 'TikTok interdit explicitement le changement de confidentialité.' };
            if (typeof raw.reason === 'string' && raw.reason.trim() !== '') return { canChange: false, reason: raw.reason.trim() };
        }

        const entries = getTargetVisibilityOption(item, targetVisibility);
        if (entries.length > 0) {
            let available = false;
            let blocked = false;

            for (const { entry } of entries) {
                const status = Number(entry.visibility_status ?? entry.visibilityStatus);
                if (status === 1) available = true;
                if (status === 0) blocked = true;
                if (typeof entry.reason === 'string' && entry.reason.trim() !== '') return { canChange: false, reason: entry.reason.trim() };
            }

            if (!available && blocked) return { canChange: false, reason: `Option ${getVisibilityLabel(targetVisibility)} verrouillée par TikTok.` };
        }

        return { canChange: true, reason: '' };
    }

    // ============================================================
    // CLASSIFICATION STUDIO
    // ============================================================

    function normalizeStudioItem(item, pageContext = {}) {
        if (!item || typeof item !== 'object') return null;

        const rawId = item.item_id ?? item.itemId ?? item.aweme_id ?? item.awemeId ?? item.id;
        if (rawId === undefined || rawId === null) return null;
        const id = String(rawId);
        if (!/^\d{15,25}$/.test(id)) return null;

        const status = Number(item.status ?? 0);
        const visibility = Number(item.visibility ?? 0);

        // --------------------------------------------------------
        // SUPPRIMÉE
        // --------------------------------------------------------
        const isDeleted = Boolean(item.is_deleted ?? item.isDeleted) || status === 3 || status === 4;

        // --------------------------------------------------------
        // COPYRIGHT / DMCA / MUTED EXPLICITE
        // --------------------------------------------------------
        const copyrightInfo = item.copyright_info || item.copyrightInfo || {};
        const musicInfo = item.music_info || item.musicInfo || {};
        let rawJsonStr = '';
        try { rawJsonStr = JSON.stringify(item).toLowerCase(); } catch (e) {}

        // Détection ultra stricte des signaux Sony Music / DMCA / Audio coupé
        const explicitCopyright = Boolean(
            copyrightInfo.is_copyright_restricted ||
            copyrightInfo.isCopyrightRestricted ||
            copyrightInfo.is_copyright_violation ||
            copyrightInfo.isCopyrightViolation ||
            item.is_copyright_restricted ||
            item.isCopyrightRestricted ||
            item.is_copyright_violation ||
            item.isCopyrightViolation ||
            Number(item.audio_copyright_status ?? item.audioCopyrightStatus) === 1 ||
            Number(item.music_copyright_status ?? item.musicCopyrightStatus) === 1 ||
            item.audio_muted === true || item.audioMuted === true ||
            item.is_muted === true || item.isMuted === true ||
            item.sound_muted === true || item.soundMuted === true ||
            musicInfo.is_copyright_violation === true ||
            rawJsonStr.includes('"dmca"') ||
            rawJsonStr.includes('"takedown"') ||
            rawJsonStr.includes('"take_down"')
        );

        // --------------------------------------------------------
        // MODÉRATION / RESTRICTION
        // --------------------------------------------------------
        const itemLimited = item.is_limited === true || item.isLimited === true;
        const pageLimited = Boolean(pageContext.pageIsLimited === true) && Number(pageContext.itemCount) === 1;
        const status141 = status === 141;

        // Tout statut anormal (ex: 133, 148, 150) indique souvent un blocage
        const abnormalStatus = status > 50 && status !== 141;
        const inReview = item.in_review === true || item.inReview === true;

        // Détection des violations génériques (règles communautaires)
        const hasViolation = Boolean(
            item.has_violation || item.hasViolation ||
            item.violation_info || item.violationInfo ||
            item.punish_info || item.punishInfo ||
            item.policy_notice || item.policyNotice ||
            item.appeal_status !== undefined ||
            item.punish_status !== undefined
        );

        const explicitModeration = item.is_under_review === true ||
            item.isUnderReview === true ||
            item.is_under_moderation === true ||
            item.isUnderModeration === true ||
            item.under_review === true ||
            item.underReview === true ||
            item.moderation_pending === true ||
            item.moderationPending === true ||
            hasViolation;

        const reviewStatus = item.review_status ?? item.reviewStatus ?? item.audit_status ?? item.auditStatus;
        const reviewText = typeof reviewStatus === 'string' ? reviewStatus.trim().toLowerCase() : '';
        const pendingReviewText = Boolean(reviewText && /under[ _-]?review|in[ _-]?review|pending|auditing|audit[ _-]?pending|moderation[ _-]?pending/i.test(reviewText));

        const moderationSignals = [];
        if (status141) moderationSignals.push('status=141');
        if (abnormalStatus) moderationSignals.push(`status=${status}`);
        if (itemLimited) moderationSignals.push('item.is_limited=true');
        if (pageLimited) moderationSignals.push('response.is_limited=true + item unique');
        if (inReview) moderationSignals.push('in_review=true');
        if (explicitModeration) moderationSignals.push('flag violation/modération explicite');
        if (explicitCopyright) moderationSignals.push('signal copyright/dmca/audio mute');
        if (pendingReviewText) moderationSignals.push(`review/audit=${reviewStatus}`);

        const isUnderModeration = status141 || abnormalStatus || itemLimited || pageLimited || inReview || explicitModeration || pendingReviewText;

        // --------------------------------------------------------
        // CATÉGORIE
        // --------------------------------------------------------
        let category = 'SAINE';
        let categoryReason = '';

        if (isDeleted) {
            category = 'SUPPRIMEE';
            categoryReason = 'Vidéo supprimée / statut TikTok 3 ou 4.';
        } else if (explicitCopyright) {
            category = 'COPYRIGHT';
            categoryReason = 'Restriction pour droits d\'auteur, DMCA ou audio coupé.';
        } else if (isUnderModeration) {
            category = 'RESTRICTION';
            categoryReason = `Vidéo restreinte ou sous modération${moderationSignals.length ? ` (${moderationSignals.join(', ')})` : ''}.`;
        }

        // --------------------------------------------------------
        // PERMISSIONS PAR VISIBILITÉ
        // --------------------------------------------------------
        const canChangeByVisibility = { '0': false, '1': false, '2': false };
        const lockReasonByVisibility = { '0': '', '1': '', '2': '' };

        for (const v of [0, 1, 2]) {
            const permission = inspectPrivacyPermission(item, v);
            canChangeByVisibility[String(v)] = permission.canChange;
            lockReasonByVisibility[String(v)] = permission.reason || '';
        }

        const selectedVisibility = normalizeVisibility(db.selectedVisibility);
        const selectedKey = String(selectedVisibility);

        return {
            id, visibility, status, category, categoryReason, moderationSignals,
            isLimited: itemLimited || pageLimited,
            itemLimited, pageLimitedSingleItem: pageLimited,
            status141, abnormalStatus, hasViolation, inReview, underReview: explicitModeration,
            reviewStatusPending: pendingReviewText, isUnderModeration, isDeleted, explicitCopyright,
            canChangeByVisibility, lockReasonByVisibility,
            canChangePrivacy: Boolean(canChangeByVisibility[selectedKey]),
            lockReason: category !== 'SAINE' ? categoryReason : (lockReasonByVisibility[selectedKey] || ''),
            description: typeof item.desc === 'string' ? item.desc : '',
            raw: item
        };
    }

    function refreshStudioItemTargetPermission(item) {
        if (!item) return item;
        const target = normalizeVisibility(db.selectedVisibility);
        const key = String(target);

        if (!item.canChangeByVisibility || typeof item.canChangeByVisibility !== 'object') {
            item.canChangeByVisibility = { '0': false, '1': false, '2': false };
        }
        if (!item.lockReasonByVisibility || typeof item.lockReasonByVisibility !== 'object') {
            item.lockReasonByVisibility = { '0': '', '1': '', '2': '' };
        }

        if (item.raw) {
            const permission = inspectPrivacyPermission(item.raw, target);
            item.canChangeByVisibility[key] = permission.canChange;
            item.lockReasonByVisibility[key] = permission.reason || '';
            item.canChangePrivacy = permission.canChange;
        }

        if (item.category !== 'SAINE') {
            item.lockReason = item.categoryReason || '';
        } else {
            item.lockReason = item.lockReasonByVisibility[key] || '';
        }
        return item;
    }

    function isHealthyEditableCandidate(item, targetVisibility) {
        if (!item) return false;
        refreshStudioItemTargetPermission(item);
        const target = normalizeVisibility(targetVisibility);
        const processed = getProcessedList(target);

        return (
            item.category === 'SAINE' &&
            item.canChangePrivacy === true &&
            Number(item.visibility) !== target &&
            !processed.some(id => String(id) === String(item.id))
        );
    }

    // ============================================================
    // STATISTIQUES
    // ============================================================

    function getStudioStats(targetVisibility = db.selectedVisibility) {
        const target = normalizeVisibility(targetVisibility);
        const matches = Array.isArray(db.studioMatches) ? db.studioMatches : [];

        const healthy = matches.filter(item => item.category === 'SAINE');
        const alreadyTarget = healthy.filter(item => Number(item.visibility) === target);
        const eligible = healthy.filter(item => isHealthyEditableCandidate(item, target));

        const processedSet = new Set(getProcessedList(target).map(id => String(id)));
        const processed = healthy.filter(item => processedSet.has(String(item.id)));

        const restricted = matches.filter(item => item.category === 'RESTRICTION');
        const copyright = matches.filter(item => item.category === 'COPYRIGHT');
        const deleted = matches.filter(item => item.category === 'SUPPRIMEE');
        const lockedHealthy = healthy.filter(item => !item.canChangePrivacy);

        return {
            total: matches.length, healthy: healthy.length, alreadyTarget: alreadyTarget.length, eligible: eligible.length,
            processed: processed.length, restricted: restricted.length, copyright: copyright.length, deleted: deleted.length,
            lockedHealthy: lockedHealthy.length,
            status141: matches.filter(item => item.status141 === true || Number(item.status) === 141).length,
            abnormalStatus: matches.filter(item => item.abnormalStatus === true).length,
            hasViolation: matches.filter(item => item.hasViolation === true).length
        };
    }

    // ============================================================
    // SCAN STUDIO
    // ============================================================

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

        const targetVisibility = normalizeVisibility(db.selectedVisibility);
        setStatus(`🔎 Recherche de ${targets.size} vidéos — cible : ${getVisibilityLabel(targetVisibility)}`);

        const studioMap = new Map();
        const missing = new Set();
        let scanComplete = true;
        let allFound = false;
        let lastError = null;

        for (const sortOrder of [2, 1]) {
            let cursor = 0; let page = 0; let hasMore = true;
            while (hasMore && page < STUDIO_MAX_PAGES) {
                page++;
                setStatus(`🔎 Studio — tri ${sortOrder} — page ${page} — ${studioMap.size}/${targets.size}`);

                let result;
                try {
                    result = await getStudioPage(cursor, sortOrder);
                } catch (error) {
                    lastError = error;
                    scanComplete = false;
                    if (error.isPaginationLimit) break;
                    if (error.is403 || error.is429) throw error;
                    log('error', 'Scan-Studio', 'Erreur pagination Studio.', error);
                    break;
                }

                const items = extractStudioItems(result);
                const pageIsLimited = Boolean(result?.is_limited === true || result?.data?.is_limited === true);

                for (const rawItem of items) {
                    const item = normalizeStudioItem(rawItem, { pageIsLimited, itemCount: items.length });
                    if (!item) continue;
                    if (targets.has(item.id)) studioMap.set(item.id, item);
                }

                const nextCursor = result?.cursor ?? result?.data?.cursor;
                hasMore = Boolean(result?.has_more ?? result?.hasMore ?? result?.data?.has_more ?? result?.data?.hasMore ?? false);

                if (studioMap.size >= targets.size) { allFound = true; break; }
                if (!hasMore) break;
                if (nextCursor === undefined || nextCursor === null || String(nextCursor) === String(cursor)) { scanComplete = false; break; }

                cursor = nextCursor;
                await sleep(STUDIO_PAGE_DELAY);
            }
            if (allFound) break;
            if (page >= STUDIO_MAX_PAGES && hasMore) scanComplete = false;
        }

        const matches = Array.from(studioMap.values());
        const matchIds = new Set(matches.map(item => String(item.id)));
        for (const targetId of targets) {
            if (!matchIds.has(String(targetId))) missing.add(String(targetId));
        }

        db.studioMatches = matches.map(item => {
            refreshStudioItemTargetPermission(item);
            return {
                id: item.id, visibility: item.visibility, status: item.status, category: item.category,
                categoryReason: item.categoryReason, moderationSignals: item.moderationSignals,
                isLimited: item.isLimited, itemLimited: item.itemLimited, pageLimitedSingleItem: item.pageLimitedSingleItem,
                status141: item.status141, abnormalStatus: item.abnormalStatus, hasViolation: item.hasViolation,
                inReview: item.inReview, underReview: item.underReview, reviewStatusPending: item.reviewStatusPending,
                isUnderModeration: item.isUnderModeration, isDeleted: item.isDeleted, explicitCopyright: item.explicitCopyright,
                canChangeByVisibility: item.canChangeByVisibility, lockReasonByVisibility: item.lockReasonByVisibility,
                canChangePrivacy: item.canChangePrivacy, lockReason: item.lockReason, description: item.description
            };
        });

        db.missingFromStudio = Array.from(missing);
        db.studioScanComplete = Boolean(scanComplete || allFound);
        db.lastStudioScan = db.studioScanComplete ? Date.now() : null;
        db.studioClassificationVersion = STUDIO_CLASSIFICATION_VERSION;

        const alreadyTargetIds = matches.filter(item => item.category === 'SAINE' && Number(item.visibility) === targetVisibility).map(item => String(item.id));
        setAlreadyTargetList(alreadyTargetIds, targetVisibility);

        saveDB();
        updatePanel();
        const stats = getStudioStats(targetVisibility);

        log('success', 'Scan-Studio', 'Scan Studio terminé.', { matches: matches.length, missing: missing.size, healthy: stats.healthy, alreadyTarget: stats.alreadyTarget, eligible: stats.eligible, restricted: stats.restricted, copyright: stats.copyright });
        setStatus(`✅ Studio : ${matches.length}/${targets.size} — ${getVisibilityLabel(targetVisibility)}`);

        if (showAlerts) {
            const text = `Playlist des vidéos : ${targets.size}

Correspondances : ${matches.length}

Absentes de Studio : ${missing.size}

Cible : ${getVisibilityLabel(targetVisibility)}

Vidéos saines : ${stats.healthy}

Déjà dans la cible (SAINES uniquement) : ${stats.alreadyTarget}

À modifier (SAINES + modifiables) : ${stats.eligible}

Restreintes / sous modération : ${stats.restricted}
  └─ Status 141 (Verrouillées) : ${stats.status141}
  └─ Autres violations TikTok : ${stats.hasViolation}
  └─ Statut anomal (>50) : ${stats.abnormalStatus}

Copyright / DMCA / Audio Coupé : ${stats.copyright}

Supprimées : ${stats.deleted}

Saines mais verrouillées : ${stats.lockedHealthy}

Aucune modification effectuée.`;

            await showAlert(db.studioScanComplete ? '✅ ANALYSE STUDIO TERMINÉE' : '⚠️ ANALYSE STUDIO INCOMPLÈTE', text);
        }
        return matches;
    }

    function hasValidStudioScan() {
        if (!Array.isArray(db.studioMatches) || !db.lastStudioScan || !db.studioScanComplete) return false;
        if (Number(db.studioClassificationVersion) !== STUDIO_CLASSIFICATION_VERSION) return false;
        return (Date.now() - Number(db.lastStudioScan) <= STUDIO_SCAN_VALID_MS);
    }

    // ============================================================
    // EDITION VISIBILITÉ
    // ============================================================

    async function setPrivate(awemeId) {
        const target = normalizeVisibility(db.selectedVisibility);
        const params = getEditParams();
        const url = `${location.origin}/tiktok/post/edit/v1/?${params.toString()}`;

        let payload = null;
        if (nativeEditTemplate && typeof nativeEditTemplate === 'object') {
            try { payload = JSON.parse(JSON.stringify(nativeEditTemplate)); } catch { payload = null; }
        }

        if (!payload || typeof payload !== 'object') {
            payload = { aweme_id: String(awemeId), scene: 1, visibility: { visibility: target } };
        } else {
            payload.aweme_id = String(awemeId);
            if (payload.scene === undefined) payload.scene = 1;
            if (!payload.visibility || typeof payload.visibility !== 'object') payload.visibility = {};
            payload.visibility.visibility = target;
        }

        const headers = { 'Content-Type': 'application/json', 'Accept': 'application/json, text/plain, */*', 'agw-js-conv': 'str' };
        const csrf = getTikTokCsrfToken();
        if (csrf) headers['tt-csrf-token'] = csrf;

        const pageWindow = (typeof unsafeWindow !== 'undefined' && unsafeWindow) ? unsafeWindow : window;
        const pageFetch = pageWindow.fetch;
        if (typeof pageFetch !== 'function') throw new Error('window.fetch TikTok introuvable.');

        internalEditRequest = true;
        let response;
        try {
            response = await pageFetch.call(pageWindow, url, {
                method: 'POST', credentials: 'include', cache: 'no-store', referrer: location.href,
                referrerPolicy: 'strict-origin-when-cross-origin', headers, body: JSON.stringify(payload)
            });
        } finally { internalEditRequest = false; }

        const text = await response.text();

        if (response.status === 403) { const e = new Error('HTTP 403'); e.status = 403; e.is403 = true; throw e; }
        if (response.status === 429) { const e = new Error('HTTP 429'); e.status = 429; e.is429 = true; throw e; }
        if (!response.ok) { const e = new Error(`HTTP ${response.status}`); e.status = response.status; throw e; }

        let json = null;
        try { json = JSON.parse(text); } catch {}

        if (json) {
            const code = json.status_code ?? json.statusCode ?? json.code ?? json.data?.status_code ?? json.data?.statusCode;
            if (code !== undefined && code !== null && Number(code) !== 0) {
                const e = new Error(`TikTok edit ${code}: ${json.status_msg || json.statusMsg || json.message || 'Erreur inconnue'}`);
                e.apiCode = Number(code); throw e;
            }
        }
        log('success', 'Edit', `Modification envoyée : ${awemeId} → ${getVisibilityLabel(target)}`);
        return { ok: true, status: response.status, json, targetVisibility: target };
    }

    // ============================================================
    // TEST 1 VIDÉO
    // ============================================================

    async function testOnePrivate() {
        if (!isStudioPage()) { await showAlert('Attention', 'Ouvre TikTok Studio > Contenu.'); return; }
        if (db.videos.length === 0) { await showAlert('Attention', 'Aucune playlist enregistrée.'); return; }

        const target = normalizeVisibility(db.selectedVisibility);
        if (!hasValidStudioScan()) await scanStudioAPI(true);
        if (!hasValidStudioScan()) { await showAlert('❌ Test bloqué', 'Le scan Studio n’est pas complet.'); return; }

        const candidate = db.studioMatches.find(item => isHealthyEditableCandidate(item, target));

        if (!candidate) {
            const stats = getStudioStats(target);
            await showAlert('ℹ️ Aucune candidate', `Cible : ${getVisibilityLabel(target)}\n\nSaines : ${stats.healthy}\n\nDéjà dans la cible : ${stats.alreadyTarget}\n\nÀ modifier : ${stats.eligible}\n\nRestreintes : ${stats.restricted}\n\nCopyright/DMCA : ${stats.copyright}`);
            return;
        }

        const confirmed = await showConfirm('🔬 TEST 1 VIDÉO', `ID : ${candidate.id}\nCatégorie : ${candidate.category}\nCible : ${getVisibilityLabel(target)}\n\nCette vidéo est classée SAINE et modifiable.\nContinuer ?`);
        if (!confirmed) return;

        try {
            setStatus(`🔬 Test ${candidate.id}...`);
            await setPrivate(candidate.id);
            await sleep(1000);
            await scanStudioAPI(false);

            const verified = db.studioMatches.find(item => String(item.id) === String(candidate.id));
            if (!verified) throw new Error('Vidéo absente du nouveau scan Studio.');
            if (verified.category !== 'SAINE') throw new Error(`Après modification, TikTok classe la vidéo : ${verified.category}.`);
            if (Number(verified.visibility) !== target) throw new Error(`La visibilité cible n’est pas confirmée. Valeur relue : ${verified.visibility}.`);

            markProcessed(candidate.id, target);
            db.lastStudioRun = Date.now();
            saveDB(); updatePanel();

            await showAlert('✅ TEST RÉUSSI', `ID : ${candidate.id}\nNouvelle visibilité : ${getVisibilityLabel(target)}\n\nVérification Studio : OK\nLa vidéo a été ajoutée aux vidéos traitées.`);
        } catch (error) {
            log('error', 'Test', 'Échec test.', error);
            db.failed.push({ id: String(candidate.id), targetVisibility: target, reason: error.message, time: Date.now(), mode: 'test' });
            saveDB();
            await showAlert('❌ TEST ÉCHOUÉ', error.message);
        }
    }

    // ============================================================
    // TRAITEMENT DE MASSE
    // ============================================================

    async function processStudio() {
        if (busy) return;
        if (db.videos.length === 0) { await showAlert('Attention', 'Aucune vidéo playlist enregistrée.'); return; }

        const target = normalizeVisibility(db.selectedVisibility);
        if (!hasValidStudioScan()) await scanStudioAPI(true);
        if (!hasValidStudioScan()) return;

        const candidates = db.studioMatches.filter(item => isHealthyEditableCandidate(item, target));
        const stats = getStudioStats(target);

        if (candidates.length === 0) {
            await showAlert('ℹ️ Rien à modifier', `Cible : ${getVisibilityLabel(target)}\n\nVidéos saines : ${stats.healthy}\n\nDéjà dans la cible : ${stats.alreadyTarget}\n\nÀ modifier : ${stats.eligible}\n\nRestreintes : ${stats.restricted}\n\nCopyright/DMCA : ${stats.copyright}\n\nAucune modification effectuée.`);
            return;
        }

        const confirmed = await showConfirm('🚀 MODIFICATION EN MASSE', `Cible : ${getVisibilityLabel(target)}\n\nVidéos à modifier : ${candidates.length}\n\nCes vidéos sont toutes classées SAINES.\nLes vidéos restreintes / modération / copyright sont exclues.\n\nContinuer ?`);
        if (!confirmed) return;

        busy = true; stopRequested = false;
        let sent = 0; let errors = 0; const sentIds = [];

        try {
            for (let i = 0; i < candidates.length; i++) {
                if (stopRequested) break;
                const item = candidates[i];
                const id = String(item.id);
                setStatus(`🚀 ${i + 1}/${candidates.length} — ${id}`);

                try {
                    await setPrivate(id);
                    sent++; sentIds.push(id);
                } catch (error) {
                    errors++;
                    db.failed.push({ id, targetVisibility: target, reason: error.message, time: Date.now(), mode: 'mass' });
                    saveDB();
                    if (error.is403 || error.is429) { stopRequested = true; break; }
                }

                if (i < candidates.length - 1 && !stopRequested) await sleep(EDIT_DELAY);
            }

            let verifiedIds = [];
            let verificationComplete = false;

            if (sentIds.length > 0 && !stopRequested) {
                setStatus(`🔎 Vérification ${sentIds.length} vidéos...`);
                try {
                    await scanStudioAPI(false);
                    if (hasValidStudioScan()) {
                        verificationComplete = true;
                        const verifiedSet = new Set(db.studioMatches.filter(item => item.category === 'SAINE' && Number(item.visibility) === target).map(item => String(item.id)));
                        verifiedIds = sentIds.filter(id => verifiedSet.has(id));
                        for (const id of verifiedIds) markProcessed(id, target);

                        const notVerified = sentIds.filter(id => !verifiedSet.has(id));
                        for (const id of notVerified) {
                            errors++;
                            db.failed.push({ id, targetVisibility: target, reason: 'Modification envoyée mais non confirmée par Studio.', time: Date.now(), mode: 'verification' });
                        }
                    }
                } catch (error) { log('error', 'Mass', 'Erreur vérification finale.', error); }
            }

            db.lastStudioRun = Date.now();
            saveDB(); updatePanel();

            if (verificationComplete) setStatus(`🏁 ${verifiedIds.length}/${sentIds.length} confirmées`);
            else setStatus(`⚠️ ${sent} requêtes envoyées — vérification incomplète`);

            await showAlert(verificationComplete ? '🏁 TRAITEMENT TERMINÉ' : '⚠️ TRAITEMENT TERMINÉ — VÉRIFICATION INCOMPLÈTE', `Cible : ${getVisibilityLabel(target)}\n\nRequêtes envoyées : ${sent}\nConfirmées par Studio : ${verifiedIds.length}\nErreurs : ${errors}`);
        } finally {
            busy = false; updatePanel();
        }
    }

    // ============================================================
    // BIBLIOTHÈQUE PLAYLISTS ET INTERCEPTEUR
    // ============================================================

    function saveCurrentPlaylistToLibrary() {
        if (!db.playlistId || !Array.isArray(db.videos) || db.videos.length === 0) return false;
        const saved = {
            playlistId: String(db.playlistId), playlistName: db.playlistName || '', username: db.username || '',
            expectedCount: Number(db.expectedCount || db.videos.length),
            videos: db.videos.map(video => ({ id: String(video.id), desc: video.desc || '', createTime: Number(video.createTime || 0), authorUsername: video.authorUsername || '', shareUrl: video.shareUrl || '' })),
            lastScan: db.lastScan || Date.now(),
            scanComplete: db.expectedCount ? db.videos.length === db.expectedCount : true,
            savedAt: Date.now()
        };

        const index = db.savedPlaylists.findIndex(p => String(p.playlistId) === saved.playlistId);
        if (index >= 0) db.savedPlaylists[index] = saved; else db.savedPlaylists.push(saved);

        db.savedPlaylists = normalizeSavedPlaylists(db.savedPlaylists);
        saveDB(); updateSavedPlaylistSelector(); return true;
    }

    async function restoreSavedPlaylist(playlistId) {
        const saved = getSavedPlaylist(playlistId);
        if (!saved) { await showAlert('Erreur', 'Playlist sauvegardée introuvable.'); return; }

        db.playlistId = saved.playlistId; db.playlistName = saved.playlistName || ''; db.username = saved.username || '';
        db.expectedCount = Number(saved.expectedCount || saved.videos.length);
        db.videos = saved.videos.map(video => ({ ...video, id: String(video.id) }));
        db.studioMatches = []; db.lastStudioScan = null; db.lastStudioRun = null; db.missingFromStudio = []; db.studioScanComplete = false;
        db.studioClassificationVersion = STUDIO_CLASSIFICATION_VERSION; db.lastScan = saved.lastScan || null;

        saveDB(); updatePanel(); setStatus(`📂 ${db.playlistName || db.playlistId} restaurée — ${db.videos.length} vidéos`);
        await showAlert('✅ PLAYLIST RESTAURÉE', `Playlist :\n${db.playlistName || db.playlistId}\n\nVidéos :\n${db.videos.length}\n\nTu peux maintenant ouvrir Studio et lancer "Analyser Studio".`);
    }

    async function deleteSavedPlaylist(playlistId) {
        const saved = getSavedPlaylist(playlistId);
        if (!saved) return;
        const confirmed = await showConfirm('🗑 SUPPRIMER LA PLAYLIST', `Supprimer cette playlist de la bibliothèque ?\n\n${saved.playlistName || playlistId}`);
        if (!confirmed) return;
        db.savedPlaylists = db.savedPlaylists.filter(p => String(p.playlistId) !== String(playlistId));
        saveDB(); updateSavedPlaylistSelector(); setStatus('🗑 Playlist supprimée de la bibliothèque.');
    }

    async function clearDB() {
        const confirmed = await showConfirm('🗑 EFFACER TOUTES LES DONNÉES', 'Supprimer toutes les données du gestionnaire ?');
        if (!confirmed) return;
        GM_deleteValue(DB_KEY); db = cloneEmptyDB(); saveDB(); updatePanel(); updateSavedPlaylistSelector();
        setStatus('🗑 Toutes les données ont été supprimées.');
    }

    function installNativeEditCapture() {
        try {
            const pageWindow = (typeof unsafeWindow !== 'undefined' && unsafeWindow) ? unsafeWindow : window;
            if (!pageWindow || typeof pageWindow.fetch !== 'function' || pageWindow.__TTPM_V33_FETCH_HOOK__) return;
            const originalFetch = pageWindow.fetch;
            const wrappedFetch = async function (...args) {
                try {
                    const rawUrl = args[0]; const options = args[1] || {};
                    const url = typeof rawUrl === 'string' ? rawUrl : (rawUrl && typeof rawUrl.url === 'string') ? rawUrl.url : '';
                    if (url.includes('/tiktok/post/edit/v1/') && !internalEditRequest) {
                        let body = options.body;
                        if (typeof body === 'string') {
                            try {
                                const parsed = JSON.parse(body);
                                if (parsed && typeof parsed === 'object') {
                                    nativeEditTemplate = parsed;
                                    nativeEditParamsTemplate = new URLSearchParams(new URL(url, location.origin).search);
                                    log('success', 'Interceptor', 'Modèle natif d’édition capturé.');
                                }
                            } catch {}
                        }
                    }
                } catch (error) { log('warn', 'Interceptor', 'Erreur interception.', error); }
                return originalFetch.apply(this, args);
            };
            Object.defineProperty(pageWindow, '__TTPM_V33_FETCH_HOOK__', { value: true, configurable: false });
            pageWindow.fetch = wrappedFetch; log('success', 'Interceptor', 'Intercepteur fetch installé.');
        } catch (error) { log('warn', 'Interceptor', 'Impossible d’installer l’intercepteur.', error); }
    }

    // ============================================================
    // UI ET DRAG (Déplacement du panneau)
    // ============================================================

    function setStatus(msg) {
        const el = document.getElementById('ttpm-status');
        if (el) el.textContent = msg;
    }

    function updatePanel() {
        const info = document.getElementById('ttpm-info');
        if (!info) return;

        const target = normalizeVisibility(db.selectedVisibility);
        const stats = getStudioStats(target);

        let html = `<b>Playlist :</b> ${db.playlistName || db.playlistId || '—'}<br>`;
        html += `<b>Vidéos dans la playlist :</b> ${db.videos.length} / ${db.expectedCount || '?'}<br>`;
        html += `<b>Matches Studio :</b> ${db.studioMatches.length}<br>`;
        html += `<b>Vidéos saines :</b> ${stats.healthy}<br>`;
        html += `<b>Déjà dans la cible (Saines) :</b> <span style="color:#2ecc71;">${stats.alreadyTarget}</span><br>`;
        html += `<b>À modifier (Saines) :</b> <span style="color:#E67E22;">${stats.eligible}</span><br>`;
        html += `<b>Restreintes / Bloquées :</b> <span style="color:#e74c3c;">${stats.restricted}</span><br>`;
        html += `<b>Copyright / DMCA :</b> <span style="color:#f1c40f;">${stats.copyright}</span><br>`;

        info.innerHTML = html;
        updateVisibilityControls();
    }

    function makeDraggable(element) {
        const header = element.querySelector('#ttpm-header');
        if (!header) return;

        let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
        header.onmousedown = dragMouseDown;

        function dragMouseDown(e) {
            e = e || window.event;
            e.preventDefault();
            pos3 = e.clientX; pos4 = e.clientY;
            document.onmouseup = closeDragElement;
            document.onmousemove = elementDrag;
        }

        function elementDrag(e) {
            e = e || window.event;
            e.preventDefault();
            pos1 = pos3 - e.clientX; pos2 = pos4 - e.clientY;
            pos3 = e.clientX; pos4 = e.clientY;
            element.style.top = (element.offsetTop - pos2) + "px";
            element.style.left = (element.offsetLeft - pos1) + "px";
            element.style.right = 'auto'; // Disable initial right absolute positioning
        }

        function closeDragElement() {
            document.onmouseup = null; document.onmousemove = null;
        }
    }

    function createPanel() {
        if (document.getElementById(PANEL_ID)) return;

        const panel = document.createElement('div');
        panel.id = PANEL_ID;
        panel.style.cssText = `
            position:fixed; top:20px; right:20px; width:430px; max-height:calc(100vh - 40px);
            overflow-y:auto; z-index:2147483647; background:rgba(20,20,20,.97); border:2px solid #25F4EE;
            border-radius:12px; padding:14px; color:white; font-family:Arial,sans-serif; box-shadow:0 8px 30px rgba(0,0,0,.65); box-sizing:border-box;
        `;

        panel.innerHTML = `
            <div id="ttpm-header" style="color:#25F4EE; font-size:16px; font-weight:bold; text-align:center; cursor:move; padding-bottom:10px; border-bottom:1px solid #333;">
                🔒 TikTok Playlist Manager v3.4
            </div>
            <div style="margin-top:10px; background:#111; padding:10px; border-radius:7px;">
                <div style="font-size:12px; font-weight:bold; margin-bottom:7px;">📚 Playlists sauvegardées</div>
                <select id="ttpm-playlist-library" style="width:100%; padding:8px; background:#222; color:white; border:1px solid #555; border-radius:6px; box-sizing:border-box; margin-bottom:6px;"></select>
                <div id="ttpm-library-count" style="text-align:center; color:#999; font-size:11px; margin-bottom:7px;"></div>
                <button id="ttpm-restore" style="width:100%; padding:8px; margin-bottom:6px; background:#3498DB; color:white; border:0; border-radius:6px; font-weight:bold; cursor:pointer;">📂 Restaurer playlist sélectionnée</button>
                <button id="ttpm-save-current" style="width:100%; padding:8px; margin-bottom:6px; background:#27AE60; color:white; border:0; border-radius:6px; font-weight:bold; cursor:pointer;">💾 Sauvegarder playlist actuelle</button>
                <button id="ttpm-delete-playlist" style="width:100%; padding:8px; background:#555; color:#ddd; border:0; border-radius:6px; font-weight:bold; cursor:pointer;">🗑 Supprimer playlist sélectionnée</button>
            </div>
            <div style="margin-top:10px; background:#111; padding:10px; border-radius:7px;">
                <div style="font-size:12px; font-weight:bold; margin-bottom:7px;">🎯 Choisir la visibilité cible</div>
                <select id="ttpm-visibility" style="width:100%; padding:8px; background:#222; color:white; border:1px solid #555; border-radius:6px; box-sizing:border-box; font-weight:bold;">
                    <option value="1">🔒 1 — Privé / Moi uniquement</option>
                    <option value="0">🌍 0 — Public / Followers</option>
                    <option value="2">👥 2 — Amis</option>
                </select>
                <div id="ttpm-target-label" style="text-align:center; color:#25F4EE; font-weight:bold; font-size:12px; margin-top:7px;"></div>
            </div>
            <div id="ttpm-status" style="text-align:center; color:#bbb; min-height:32px; margin:10px 0; font-size:12px;">🟢 Prêt</div>
            <div id="ttpm-info" style="background:#111; padding:10px; border-radius:7px; font-size:12px; line-height:1.7; margin-bottom:10px;"></div>
            <button id="ttpm-test-api" style="width:100%; padding:9px; margin-bottom:6px; background:#666; color:white; border:0; border-radius:6px; font-weight:bold; cursor:pointer;">🧪 Tester l'API Playlist</button>
            <button id="ttpm-scan-playlist" style="width:100%; padding:10px; margin-bottom:6px; background:#25F4EE; color:#000; border:0; border-radius:6px; font-weight:bold; cursor:pointer;">📥 Récupérer les vidéos</button>
            <button id="ttpm-scan-studio" style="width:100%; padding:10px; margin-bottom:6px; background:#9B59B6; color:white; border:0; border-radius:6px; font-weight:bold; cursor:pointer;">🔎 Analyser Studio</button>
            <button id="ttpm-test-one" style="width:100%; padding:10px; margin-bottom:6px; background:#E67E22; color:white; border:0; border-radius:6px; font-weight:bold; cursor:pointer;">🔬 Tester 1 vidéo</button>
            <button id="ttpm-process" style="width:100%; padding:11px; margin-bottom:6px; background:#FE2C55; color:white; border:0; border-radius:6px; font-weight:bold; cursor:pointer;">🚀 Appliquer aux correspondances</button>
            <button id="ttpm-debug" style="width:100%; padding:8px; margin-top:6px; background:#444; color:#25F4EE; border:0; border-radius:6px; font-weight:bold; cursor:pointer;">🐞 Mode Debug Console : ON</button>
            <button id="ttpm-clear" style="width:100%; padding:7px; margin-top:8px; background:#333; color:#aaa; border:0; border-radius:6px; font-weight:bold; cursor:pointer;">🗑 Effacer toutes les données</button>
        `;

        document.body.appendChild(panel);

        document.getElementById('ttpm-test-api').onclick = testAPI;
        document.getElementById('ttpm-scan-playlist').onclick = scanPlaylistAPI;
        document.getElementById('ttpm-scan-studio').onclick = async () => { try { await scanStudioAPI(true); } catch (e) { await showAlert('❌ Erreur Studio', e.message); } };
        document.getElementById('ttpm-test-one').onclick = testOnePrivate;
        document.getElementById('ttpm-process').onclick = processStudio;
        document.getElementById('ttpm-clear').onclick = clearDB;
        document.getElementById('ttpm-debug').onclick = () => { debugMode = !debugMode; const btn = document.getElementById('ttpm-debug'); btn.textContent = `🐞 Mode Debug Console : ${debugMode ? 'ON' : 'OFF'}`; btn.style.color = debugMode ? '#25F4EE' : '#888'; };
        document.getElementById('ttpm-visibility').onchange = e => { db.selectedVisibility = normalizeVisibility(e.target.value); saveDB(); updatePanel(); setStatus(`🎯 Cible : ${getVisibilityLabel(db.selectedVisibility)}`); };
        document.getElementById('ttpm-save-current').onclick = async () => { if (saveCurrentPlaylistToLibrary()) await showAlert('✅ PLAYLIST SAUVEGARDÉE', `Playlist :\n${db.playlistName || db.playlistId}`); else await showAlert('Attention', 'Aucune playlist actuelle à sauvegarder.'); };
        document.getElementById('ttpm-restore').onclick = async () => { const select = document.getElementById('ttpm-playlist-library'); if (!select?.value) await showAlert('Attention', 'Sélectionne une playlist sauvegardée.'); else await restoreSavedPlaylist(select.value); };
        document.getElementById('ttpm-delete-playlist').onclick = async () => { const select = document.getElementById('ttpm-playlist-library'); if (!select?.value) await showAlert('Attention', 'Sélectionne une playlist sauvegardée.'); else await deleteSavedPlaylist(select.value); };

        makeDraggable(panel); updatePanel(); updateSavedPlaylistSelector();
    }

    function updateVisibilityControls() {
        const select = document.getElementById('ttpm-visibility');
        const targetLabel = document.getElementById('ttpm-target-label');
        const target = normalizeVisibility(db.selectedVisibility);

        if (select) select.value = String(target);
        if (targetLabel) targetLabel.textContent = `🎯 Cible : ${getVisibilityLabel(target)}`;

        const testOne = document.getElementById('ttpm-test-one');
        if (testOne) testOne.textContent = `🔬 Tester 1 vidéo → ${getVisibilityLabel(target)}`;
        const process = document.getElementById('ttpm-process');
        if (process) process.textContent = `🚀 Appliquer aux correspondances → ${getVisibilityLabel(target)}`;
    }

    function updateSavedPlaylistSelector() {
        const select = document.getElementById('ttpm-playlist-library');
        const count = document.getElementById('ttpm-library-count');
        if (!select) return;

        db.savedPlaylists = normalizeSavedPlaylists(db.savedPlaylists);
        const current = select.value;
        select.innerHTML = '';

        const empty = document.createElement('option');
        empty.value = '';
        empty.textContent = db.savedPlaylists.length ? '📚 Choisir une playlist sauvegardée' : '📚 Aucune playlist sauvegardée';
        select.appendChild(empty);

        for (const playlist of db.savedPlaylists) {
            const option = document.createElement('option');
            option.value = String(playlist.playlistId);
            option.textContent = `${playlist.scanComplete ? '✅' : '⚠️'} ${playlist.playlistName || playlist.playlistId} — ${playlist.videos.length} vidéos`;
            select.appendChild(option);
        }

        if (current && db.savedPlaylists.some(p => String(p.playlistId) === String(current))) {
            select.value = current;
        } else if (db.playlistId && db.savedPlaylists.some(p => String(p.playlistId) === String(db.playlistId))) {
            select.value = String(db.playlistId);
        }

        if (count) count.textContent = `${db.savedPlaylists.length} playlist${db.savedPlaylists.length > 1 ? 's' : ''} sauvegardée${db.savedPlaylists.length > 1 ? 's' : ''}`;
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => { createPanel(); installNativeEditCapture(); });
    } else {
        createPanel(); installNativeEditCapture();
    }
})();