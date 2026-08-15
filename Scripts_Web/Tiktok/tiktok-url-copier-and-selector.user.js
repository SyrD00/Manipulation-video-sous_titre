// ==UserScript==
// @name         TikTok - Panneau Déplaçable & Sélection ON/OFF
// @namespace    http://tampermonkey.net/
// @version      8.1
// @description  Rend le panneau de contrôle glissant/déplaçable (Draggable) et gère la sélection/le mode OFF propre.
// @match        https://www.tiktok.com/*
// @match        https://tiktok.com/*
// @run-at       document-idle
// @grant        GM_setClipboard
// ==/UserScript==

(function () {
    'use strict';

    const selectedUrls = new Set();
    let isSelectionModeActive = false;

    // 1. Panneau de contrôle fixe et déplaçable (Draggable)
    function createControlPanel() {
        if (document.getElementById('tm-tiktok-panel')) return;

        const panel = document.createElement('div');
        panel.id = 'tm-tiktok-panel';
        panel.style.cssText = `
            position: fixed !important;
            bottom: 20px !important;
            right: 20px !important;
            z-index: 2147483647 !important;
            background: rgba(18, 18, 18, 0.95) !important;
            border: 1px solid #FE2C55 !important;
            border-radius: 8px !important;
            padding: 12px 16px !important;
            box-shadow: 0 4px 20px rgba(254, 44, 85, 0.4) !important;
            display: flex !important;
            flex-direction: column !important;
            gap: 8px !important;
            font-family: sans-serif !important;
            color: #fff !important;
            cursor: move !important;
            user-select: none !important;
        `;

        // Logique de Drag & Drop (Déplacement du panneau)
        let isDragging = false;
        let offsetX = 0;
        let offsetY = 0;

        panel.addEventListener('mousedown', (e) => {
            // Ne pas déclencher le drag si on clique sur un bouton intérieur
            if (e.target.tagName === 'BUTTON') return;
            isDragging = true;
            offsetX = e.clientX - panel.getBoundingClientRect().left;
            offsetY = e.clientY - panel.getBoundingClientRect().top;

            // Passer en positionnement absolu top/left lors du premier drag
            panel.style.bottom = 'auto';
            panel.style.right = 'auto';
        });

        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            panel.style.left = `${e.clientX - offsetX}px`;
            panel.style.top = `${e.clientY - offsetY}px`;
        });

        document.addEventListener('mouseup', () => {
            isDragging = false;
        });

        // Interrupteur Mode Sélection
        const toggleBtn = document.createElement('button');
        toggleBtn.id = 'tm-tiktok-toggle-mode';
        toggleBtn.textContent = 'Mode Sélection : OFF';
        toggleBtn.style.cssText = `
            background: #333 !important;
            color: #aaa !important;
            border: 1px solid #555 !important;
            border-radius: 4px !important;
            padding: 6px 10px !important;
            font-size: 11px !important;
            font-weight: bold !important;
            cursor: pointer !important;
            transition: 0.2s !important;
        `;

        toggleBtn.onclick = () => {
            isSelectionModeActive = !isSelectionModeActive;
            if (isSelectionModeActive) {
                toggleBtn.textContent = 'Mode Sélection : ON';
                toggleBtn.style.background = '#FE2C55';
                toggleBtn.style.color = '#fff';
                toggleBtn.style.borderColor = '#FE2C55';
                document.body.classList.add('tm-mode-on');
            } else {
                toggleBtn.textContent = 'Mode Sélection : OFF';
                toggleBtn.style.background = '#333';
                toggleBtn.style.color = '#aaa';
                toggleBtn.style.borderColor = '#555';
                document.body.classList.remove('tm-mode-on');
            }
        };

        const counter = document.createElement('div');
        counter.id = 'tm-tiktok-counter';
        counter.textContent = 'Vidéos sélectionnées : 0';
        counter.style.cssText = `
            font-size: 12px !important;
            font-weight: bold !important;
            color: #FE2C55 !important;
            text-align: center !important;
            pointer-events: none !important;
        `;

        const btnContainer = document.createElement('div');
        btnContainer.style.cssText = `
            display: flex !important;
            gap: 8px !important;
        `;

        const copyListBtn = document.createElement('button');
        copyListBtn.id = 'tm-tiktok-copy-list';
        copyListBtn.textContent = 'Copier la liste';
        copyListBtn.style.cssText = `
            background: #FE2C55 !important;
            color: #fff !important;
            border: none !important;
            border-radius: 4px !important;
            padding: 6px 12px !important;
            font-size: 11px !important;
            font-weight: bold !important;
            cursor: pointer !important;
            transition: 0.2s !important;
        `;

        copyListBtn.onclick = () => {
            if (selectedUrls.size === 0) {
                alert('Aucune vidéo sélectionnée !');
                return;
            }
            const textToCopy = Array.from(selectedUrls).join('\n');
            if (typeof GM_setClipboard !== 'undefined') {
                GM_setClipboard(textToCopy);
            } else {
                navigator.clipboard.writeText(textToCopy);
            }

            copyListBtn.textContent = 'Liste copiée !';
            copyListBtn.style.background = '#25F4EE';
            copyListBtn.style.color = '#000';

            setTimeout(() => {
                copyListBtn.textContent = 'Copier la liste';
                copyListBtn.style.background = '#FE2C55';
                copyListBtn.style.color = '#fff';
            }, 1200);
        };

        const resetBtn = document.createElement('button');
        resetBtn.textContent = 'Vider';
        resetBtn.style.cssText = `
            background: #333 !important;
            color: #ccc !important;
            border: none !important;
            border-radius: 4px !important;
            padding: 6px 10px !important;
            font-size: 11px !important;
            cursor: pointer !important;
        `;

        resetBtn.onclick = () => {
            selectedUrls.clear();
            document.querySelectorAll('.tm-selection-overlay').forEach(overlay => {
                overlay.style.display = 'none';
            });
            updateCounter();
        };

        btnContainer.appendChild(copyListBtn);
        btnContainer.appendChild(resetBtn);

        panel.appendChild(toggleBtn);
        panel.appendChild(counter);
        panel.appendChild(btnContainer);
        document.body.appendChild(panel);

        // Masquer/Afficher dynamiquement les badges selon le mode
        const style = document.createElement('style');
        style.innerHTML = `
            .tm-tiktok-badge {
                display: none !important;
            }
            body.tm-mode-on .tm-tiktok-badge {
                display: flex !important;
            }
        `;
        document.head.appendChild(style);
    }

    function updateCounter() {
        const counter = document.getElementById('tm-tiktok-counter');
        if (counter) {
            counter.textContent = `Vidéos sélectionnées : ${selectedUrls.size}`;
        }
    }

    function toggleSelection(a, fullUrl, visualOverlay) {
        if (selectedUrls.has(fullUrl)) {
            selectedUrls.delete(fullUrl);
            visualOverlay.style.display = 'none';
        } else {
            selectedUrls.add(fullUrl);
            visualOverlay.style.display = 'block';
        }
        updateCounter();
    }

    function inject() {
        createControlPanel();

        const links = document.querySelectorAll('a[href*="/video/"]');

        links.forEach(a => {
            // Ignorer les éléments dans le lecteur vidéo ouvert
            if (a.closest('div[class*="DivVideoDetailContainer"]') || a.closest('div[class*="DivBrowseModeContainer"]')) {
                return;
            }

            if (a.dataset.clickSelectionInit) return;

            const rawHref = a.getAttribute('href') || a.href;
            const fullUrl = a.href;

            const match = rawHref.match(/\/video\/(\d+)/);
            if (!match) return;

            const videoId = match[1];
            a.dataset.clickSelectionInit = 'true';

            if (window.getComputedStyle(a).position === 'static') {
                a.style.position = 'relative';
            }

            // Overlay visuel rouge
            const visualOverlay = document.createElement('div');
            visualOverlay.className = 'tm-selection-overlay';
            visualOverlay.style.cssText = `
                position: absolute !important;
                top: 0 !important;
                left: 0 !important;
                width: 100% !important;
                height: 100% !important;
                background: rgba(254, 44, 85, 0.25) !important;
                border: 4px solid #FE2C55 !important;
                box-sizing: border-box !important;
                box-shadow: inset 0 0 20px rgba(254, 44, 85, 0.8) !important;
                z-index: 2147483640 !important;
                pointer-events: none !important;
                display: none;
            `;
            a.appendChild(visualOverlay);

            // Gestion du clic
            a.addEventListener('click', (e) => {
                if (e.target.closest('.tm-copy-single-btn')) return;

                if (isSelectionModeActive) {
                    e.preventDefault();
                    e.stopPropagation();
                    toggleSelection(a, fullUrl, visualOverlay);
                }
            }, true);

            // Badge ID + Bouton Copier
            const box = document.createElement('div');
            box.className = 'tm-tiktok-badge';
            box.style.cssText = `
                position: absolute !important;
                top: 5px !important;
                left: 5px !important;
                right: 5px !important;
                z-index: 2147483647 !important;
                justify-content: space-between !important;
                align-items: center !important;
                pointer-events: auto !important;
            `;

            const badge = document.createElement('span');
            badge.textContent = videoId;
            badge.style.cssText = `
                background: rgba(0,0,0,0.85) !important;
                color: #00ff88 !important;
                font-size: 10px !important;
                font-weight: bold !important;
                padding: 2px 5px !important;
                border-radius: 3px !important;
                font-family: monospace !important;
            `;

            const btn = document.createElement('button');
            btn.className = 'tm-copy-single-btn';
            btn.textContent = 'Copier';
            btn.style.cssText = `
                background: #FE2C55 !important;
                color: #fff !important;
                border: none !important;
                border-radius: 3px !important;
                padding: 2px 6px !important;
                font-size: 10px !important;
                font-weight: bold !important;
                cursor: pointer !important;
            `;

            btn.onclick = (e) => {
                e.preventDefault();
                e.stopPropagation();

                if (typeof GM_setClipboard !== 'undefined') {
                    GM_setClipboard(fullUrl);
                } else {
                    navigator.clipboard.writeText(fullUrl);
                }

                btn.textContent = 'Copié !';
                btn.style.background = '#25F4EE';
                btn.style.color = '#000';

                setTimeout(() => {
                    btn.textContent = 'Copier';
                    btn.style.background = '#FE2C55';
                    btn.style.color = '#fff';
                }, 1000);
            };

            box.appendChild(badge);
            box.appendChild(btn);
            a.appendChild(box);
        });
    }

    setInterval(inject, 500);
})();