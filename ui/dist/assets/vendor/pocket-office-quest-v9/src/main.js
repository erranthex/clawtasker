(function () {
  const data = window.PocketOfficeData;
  const Engine = window.PocketOfficeEngine;
  const Render = window.PocketOfficeRender;

  const canvas = document.getElementById('game');
  const ctx = canvas.getContext('2d');
  const statusText = document.getElementById('statusText');
  const avatarText = document.getElementById('avatarText');
  const objectiveText = document.getElementById('objectiveText');
  const compatText = document.getElementById('compatText');

  canvas.width = data.meta.internalResolution.width;
  canvas.height = data.meta.internalResolution.height;
  ctx.imageSmoothingEnabled = false;

  const keysDown = new Set();
  const keysPressed = new Set();

  function setStatus(message) {
    if (statusText) statusText.textContent = message;
  }

  function setAvatar(message) {
    if (avatarText) avatarText.textContent = message;
  }

  function setObjective(message) {
    if (objectiveText) objectiveText.textContent = message;
  }

  function setCompat(message) {
    if (compatText) compatText.textContent = message;
  }

  function keyFromEvent(event) {
    return event.key;
  }

  window.addEventListener('keydown', function (event) {
    const key = keyFromEvent(event);
    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', ' ', 'Enter'].includes(key)) {
      event.preventDefault();
    }
    if (!keysDown.has(key)) {
      keysPressed.add(key);
    }
    keysDown.add(key);
  });

  window.addEventListener('keyup', function (event) {
    keysDown.delete(keyFromEvent(event));
  });

  window.addEventListener('blur', function () {
    keysDown.clear();
    keysPressed.clear();
  });

  function isDown(...keys) {
    return keys.some((key) => keysDown.has(key));
  }

  function wasPressed(...keys) {
    return keys.some((key) => keysPressed.has(key));
  }

  function buildInput() {
    const left = isDown('ArrowLeft', 'a', 'A');
    const right = isDown('ArrowRight', 'd', 'D');
    const up = isDown('ArrowUp', 'w', 'W');
    const down = isDown('ArrowDown', 's', 'S');
    const manualOverride = left || right || up || down || wasPressed(' ', 'Enter', 'z', 'Z', 'Escape');
    return {
      left,
      right,
      up,
      down,
      sprint: isDown('Shift'),
      justLeft: wasPressed('ArrowLeft', 'a', 'A'),
      justRight: wasPressed('ArrowRight', 'd', 'D'),
      justUp: wasPressed('ArrowUp', 'w', 'W'),
      justDown: wasPressed('ArrowDown', 's', 'S'),
      justConfirm: wasPressed('Enter'),
      justInteract: wasPressed(' ', 'z', 'Z'),
      justCancel: wasPressed('Escape'),
      manualOverride,
    };
  }

  function clearPressed() {
    keysPressed.clear();
  }

  function loadImage(src) {
    return new Promise(function (resolve, reject) {
      const image = new Image();
      image.onload = function () { resolve(image); };
      image.onerror = function () { reject(new Error('Failed to load ' + src)); };
      image.src = src;
    });
  }

  async function loadAssets() {
    const assets = { portraits: {}, sheets: {}, officeBackground: null };
    assets.officeBackground = await loadImage('assets/office-background.png');
    for (const avatar of data.avatars) {
      assets.portraits[avatar.id] = await loadImage('assets/avatars/' + avatar.id + '-portrait.png');
      assets.sheets[avatar.id] = await loadImage('assets/avatars/' + avatar.id + '-sheet.png');
    }
    return assets;
  }

  function updatePanels(state) {
    const avatar = data.avatars[state.selectedIndex] || data.avatars[0];
    if (state.scene === 'title') {
      setStatus('Title screen ready. Press Enter to open the Nintendo 64 inspired brick-avatar select.');
      setAvatar('Featured avatar: ' + avatar.name + ' - ' + avatar.role + '.');
      setObjective('Open the office adventure and choose who will explore the redesigned workspace.');
    } else if (state.scene === 'select') {
      setStatus('Character select active. Five brick-avatar personages are available.');
      setAvatar(avatar.name + ' - ' + avatar.role + '. ' + avatar.bio);
      setObjective('Use Left and Right, then press Enter to start the office tour.');
    } else {
      const liveAvatar = Engine.getAvatarById(data, state.selectedAvatarId);
      setStatus(state.dialog ? 'Dialogue open with ' + state.dialog.title + '.' : 'Live office build running at browser resolution ' + data.meta.internalResolution.width + 'x' + data.meta.internalResolution.height + '.');
      setAvatar(liveAvatar.name + ' - ' + liveAvatar.role + '.');
      setObjective(state.dialog ? state.dialog.text : state.prompt);
    }
    setCompat('Static browser build. Works from the included files on Windows, macOS, and Linux browsers.');
  }

  function drawLoadingScreen(message) {
    ctx.fillStyle = '#101826';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#f1f4f8';
    ctx.font = 'bold 24px monospace';
    ctx.fillText('Pocket Office Quest', 42, 88);
    ctx.fillStyle = '#7bd1f2';
    ctx.font = 'bold 18px monospace';
    ctx.fillText('Loading brick-avatar assets...', 42, 120);
    ctx.fillStyle = '#d0dae6';
    ctx.font = '14px monospace';
    ctx.fillText(message, 42, 156);
  }

  async function boot() {
    const demoMode = new URLSearchParams(window.location.search).get('demo') === '1';
    let assets;
    let state = Engine.createState(data, { demoMode: demoMode, selectedIndex: 0 });
    let lastTime = performance.now();
    let ready = false;

    setStatus('Loading Nintendo 64 inspired office assets...');
    setAvatar('Preparing brick portraits and clearer walk cycles.');
    setObjective('The browser build is setting up the office scene.');
    setCompat('Static browser application. No build step is required to play.');
    drawLoadingScreen('Preparing portraits, sprites, and the office layout.');

    try {
      assets = await loadAssets();
      ready = true;
      updatePanels(state);
    } catch (error) {
      console.error(error);
      setStatus('Asset loading failed. See the browser console for details.');
      drawLoadingScreen('Asset loading failed. Open the console for details.');
      return;
    }

    function frame(now) {
      const dt = Math.min(0.05, (now - lastTime) / 1000);
      lastTime = now;
      if (ready) {
        const input = buildInput();
        Engine.tick(state, data, input, dt);
        Render.renderFrame(ctx, state, data, assets);
        updatePanels(state);
        clearPressed();
      }
      requestAnimationFrame(frame);
    }

    requestAnimationFrame(frame);
  }

  boot();
})();
