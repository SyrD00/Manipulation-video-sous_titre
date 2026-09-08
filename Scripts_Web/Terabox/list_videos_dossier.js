// ==UserScript==
// @name         TeraBox Extracteur
// @namespace    http://tampermonkey.net/
// @version      8.6
// @description  Fenêtre redimensionnable depuis tous les bords comme un vrai logiciel
// @match        https://www.terabox.com/*
// @match        https://www.terabox.app/*
// @match        https://www.1024tera.com/*
// @run-at       document-idle
// @grant        none
// ==/UserScript==

(function () {
    'use strict';

    console.log('[TeraBox V8.6] Script "True Resize" chargé');

    const PANEL_ID = 'tb-extractor-v8';
    const VIDEO_EXT = /\.(mp4|mkv|mov|avi|3gp|webm|flv|ts|m4v|wmv|mpeg|mpg)$/i;

    let videos = new Set();
    let running = false;
    let scrollInterval = null;
    let scrollContainer = null;

    // =========================================================
    // PANNEAU UI
    // =========================================================

    function createPanel() {
        if (!document.body || document.getElementById(PANEL_ID)) return;

        const panel = document.createElement('div');
        panel.id = PANEL_ID;

        panel.innerHTML = `
            <div id="tb-inner-content" style="width: 100%; height: 100%; overflow: auto; padding-bottom: 5px; padding-right: 5px;">
                <div id="tb-drag-header" style="color:#00e676; font-weight:bold; text-align:center; margin-bottom:10px; cursor:move; user-select:none; padding-bottom:5px; border-bottom:1px solid #333;">
                    TeraBox V8.6
                </div>

                <div class="tb-status" style="font-size:12px; text-align:center; margin-bottom:7px; color:white;">🟢 Prêt</div>
                <div class="tb-count" style="font-size:12px; text-align:center; margin-bottom:10px; color:white; font-weight:bold;">Vidéos : 0</div>

                <div style="font-size:10px; color:#ffcc80; text-align:center; line-height:1.4; margin-bottom:12px;">
                    Le scan repart du début même si tu as scrollé.
                </div>

                <button id="tb-start" style="width:100%; padding:8px; margin-top:6px; background:#00a152; color:white; border:none; border-radius:5px; font-weight:bold; cursor:pointer;">🚀 Scan Complet</button>
                <button id="tb-stop" style="width:100%; padding:8px; margin-top:6px; background:#f44336; color:white; border:none; border-radius:5px; font-weight:bold; cursor:pointer;">⏹ Arrêter</button>
                <button id="tb-download" style="width:100%; padding:8px; margin-top:6px; background:#00897b; color:white; border:none; border-radius:5px; font-weight:bold; cursor:pointer;">📥 TXT</button>
                <button id="tb-reset" style="width:100%; padding:8px; margin-top:6px; background:#8e0000; color:white; border:none; border-radius:5px; font-weight:bold; cursor:pointer;">🗑️ Reset</button>
            </div>
        `;

        // Suppression de la contrainte "overflow: hidden" sur le panel principal
        // pour permettre aux poignées de déborder légèrement et être faciles à attraper.
        panel.style.cssText = `
            position: fixed;
            right: 20px;
            bottom: 20px;
            width: 240px;
            height: 340px;
            min-width: 110px;
            min-height: 80px;
            background: rgba(15,15,15,.97);
            border: 2px solid #00c853;
            border-radius: 10px;
            padding: 10px;
            z-index: 2147483647;
            box-shadow: 0 5px 30px rgba(0,0,0,.7);
            font-family: Arial, sans-serif;
            box-sizing: border-box;
        `;

        document.body.appendChild(panel);

        bindEvents(panel);
        makePanelDraggable(panel);
        makePanelResizableFull(panel);
    }

    // =========================================================
    // FIXER LES COORDONNÉES
    // =========================================================
    // Indispensable pour éviter que la fenêtre ne saute quand on l'attrape
    function pinPosition(panel) {
        const rect = panel.getBoundingClientRect();
        panel.style.right = 'auto';
        panel.style.bottom = 'auto';
        panel.style.left = rect.left + 'px';
        panel.style.top = rect.top + 'px';
    }

    // =========================================================
    // REDIMENSIONNEMENT SUR LES 8 BORDS (NOUVEAU SYSTÈME)
    // =========================================================
    function makePanelResizableFull(panel) {
        const handles = [
            { dir: 'n', cursor: 'ns-resize', style: 'top: -5px; left: 0; width: 100%; height: 10px;' },
            { dir: 's', cursor: 'ns-resize', style: 'bottom: -5px; left: 0; width: 100%; height: 10px;' },
            { dir: 'e', cursor: 'ew-resize', style: 'top: 0; right: -5px; width: 10px; height: 100%;' },
            { dir: 'w', cursor: 'ew-resize', style: 'top: 0; left: -5px; width: 10px; height: 100%;' },
            { dir: 'nw', cursor: 'nwse-resize', style: 'top: -5px; left: -5px; width: 15px; height: 15px;' },
            { dir: 'ne', cursor: 'nesw-resize', style: 'top: -5px; right: -5px; width: 15px; height: 15px;' },
            { dir: 'sw', cursor: 'nesw-resize', style: 'bottom: -5px; left: -5px; width: 15px; height: 15px;' },
            { dir: 'se', cursor: 'nwse-resize', style: 'bottom: -5px; right: -5px; width: 15px; height: 15px;' }
        ];

        handles.forEach(h => {
            const handleDiv = document.createElement('div');
            handleDiv.style.cssText = `position: absolute; z-index: 99999; cursor: ${h.cursor}; ${h.style}`;
            panel.appendChild(handleDiv);

            handleDiv.addEventListener('mousedown', function(e) {
                e.preventDefault();
                e.stopPropagation();

                pinPosition(panel); // Fixe la fenêtre pour pouvoir la redimensionner par la gauche/haut

                let startX = e.clientX;
                let startY = e.clientY;
                let startW = panel.offsetWidth;
                let startH = panel.offsetHeight;
                let startL = panel.offsetLeft;
                let startT = panel.offsetTop;

                function doDrag(ev) {
                    let dx = ev.clientX - startX;
                    let dy = ev.clientY - startY;

                    let newW = startW, newH = startH, newL = startL, newT = startT;

                    if (h.dir.includes('e')) newW = startW + dx;
                    if (h.dir.includes('s')) newH = startH + dy;
                    if (h.dir.includes('w')) { newW = startW - dx; newL = startL + dx; }
                    if (h.dir.includes('n')) { newH = startH - dy; newT = startT + dy; }

                    // Limites de taille pour ne pas écraser complètement la fenêtre
                    if (newW < 110) {
                        if (h.dir.includes('w')) newL = startL + (startW - 110);
                        newW = 110;
                    }
                    if (newH < 80) {
                        if (h.dir.includes('n')) newT = startT + (startH - 80);
                        newH = 80;
                    }

                    panel.style.width = newW + 'px';
                    panel.style.height = newH + 'px';
                    if (h.dir.includes('w')) panel.style.left = newL + 'px';
                    if (h.dir.includes('n')) panel.style.top = newT + 'px';
                }

                function stopDrag() {
                    document.removeEventListener('mousemove', doDrag);
                    document.removeEventListener('mouseup', stopDrag);
                }

                document.addEventListener('mousemove', doDrag);
                document.addEventListener('mouseup', stopDrag);
            });
        });
    }

    // =========================================================
    // ÉVÉNEMENTS
    // =========================================================
    function bindEvents(panel) {
        panel.querySelector('#tb-start').onclick = startAutoScroll;
        panel.querySelector('#tb-stop').onclick = stopExtraction;
        panel.querySelector('#tb-download').onclick = downloadTXT;

        panel.querySelector('#tb-reset').onclick = () => {
            if (running) return alert('Arrête d’abord le scan.');
            videos.clear();
            updateUI();
            updateStatus('🗑️ Liste vidée');
        };
    }

    // =========================================================
    // PANNEAU DÉPLAÇABLE
    // =========================================================
    function makePanelDraggable(panel) {
        const header = panel.querySelector('#tb-drag-header');
        let dragging = false;
        let offsetX = 0; let offsetY = 0;

        header.addEventListener('mousedown', function (e) {
            dragging = true;
            pinPosition(panel);
            const rect = panel.getBoundingClientRect();
            offsetX = e.clientX - rect.left;
            offsetY = e.clientY - rect.top;
            e.preventDefault();
        });

        document.addEventListener('mousemove', function (e) {
            if (!dragging) return;
            let left = e.clientX - offsetX;
            let top = e.clientY - offsetY;

            const maxLeft = window.innerWidth - panel.offsetWidth;
            const maxTop = window.innerHeight - panel.offsetHeight;

            panel.style.left = Math.max(0, Math.min(left, maxLeft)) + 'px';
            panel.style.top = Math.max(0, Math.min(top, maxTop)) + 'px';
        });

        document.addEventListener('mouseup', () => dragging = false);
    }

    // =========================================================
    // LOGIQUE DE SCROLL & EXTRACTION
    // =========================================================
    function findScrollContainer() {
        return document.querySelector('.wp-s-pan-table__body') || document.querySelector('.list-content') || document.querySelector('.wp-s-pan-table__body-content') || window;
    }

    function startAutoScroll() {
        if (running) return;
        running = true;
        scrollContainer = findScrollContainer();

        videos.clear();
        updateUI();
        updateStatus('⬆️ Retour au début...');
        if (scrollContainer === window) window.scrollTo({ top: 0, behavior: 'auto' });
        else scrollContainer.scrollTop = 0;

        setTimeout(() => {
            if (!running) return;
            updateStatus('🚀 Scan complet...');

            scrollInterval = setInterval(() => {
                if (!running) return;
                extractVisibleVideos();
                if (scrollContainer === window) window.scrollBy({ top: 800, left: 0, behavior: 'auto' });
                else scrollContainer.scrollBy({ top: 800, left: 0, behavior: 'auto' });
            }, 800);
        }, 1500);
    }

    function stopExtraction() {
        if (!running) return;
        running = false;
        if (scrollInterval) { clearInterval(scrollInterval); scrollInterval = null; }
        updateStatus(`⏹ Arrêté — ${videos.size} vidéos`);
    }

    function extractVisibleVideos() {
        const elements = document.querySelectorAll('.text-name, .filename, [title]');
        let added = 0;
        elements.forEach(el => {
            const name = el.getAttribute('title') || el.innerText || el.textContent;
            if (!name) return;
            const cleanName = name.trim();
            if (VIDEO_EXT.test(cleanName) && !videos.has(cleanName)) {
                videos.add(cleanName);
                added++;
            }
        });
        if (added > 0) updateUI();
    }

    function updateStatus(t) { const el = document.querySelector(`#${PANEL_ID} .tb-status`); if (el) el.textContent = t; }
    function updateUI() { const el = document.querySelector(`#${PANEL_ID} .tb-count`); if (el) el.textContent = `Vidéos : ${videos.size}`; }

    function downloadTXT() {
        if (videos.size === 0) return alert('Aucune vidéo capturée.');
        const blob = new Blob([Array.from(videos).join('\n')], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a'); link.href = url; link.download = 'terabox_videos.txt';
        document.body.appendChild(link); link.click(); document.body.removeChild(link); URL.revokeObjectURL(url);
    }

    setTimeout(createPanel, 1500);

})();