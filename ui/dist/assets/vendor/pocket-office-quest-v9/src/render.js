(function (global) {
  const Render = {};

  function roundRectPath(ctx, x, y, w, h, r) {
    const radius = Math.min(r, w / 2, h / 2);
    ctx.beginPath();
    ctx.moveTo(x + radius, y);
    ctx.arcTo(x + w, y, x + w, y + h, radius);
    ctx.arcTo(x + w, y + h, x, y + h, radius);
    ctx.arcTo(x, y + h, x, y, radius);
    ctx.arcTo(x, y, x + w, y, radius);
    ctx.closePath();
  }

  function fillPanel(ctx, x, y, w, h, radius, fill, stroke) {
    ctx.save();
    roundRectPath(ctx, x, y, w, h, radius);
    ctx.fillStyle = fill;
    ctx.fill();
    if (stroke) {
      ctx.lineWidth = 2;
      ctx.strokeStyle = stroke;
      ctx.stroke();
    }
    ctx.restore();
  }

  function drawWrappedText(ctx, text, x, y, maxWidth, lineHeight, color) {
    ctx.save();
    ctx.fillStyle = color;
    const words = String(text || '').split(/\s+/);
    let line = '';
    let lineCount = 0;
    for (let i = 0; i < words.length; i += 1) {
      const testLine = line ? line + ' ' + words[i] : words[i];
      const width = ctx.measureText(testLine).width;
      if (width > maxWidth && line) {
        ctx.fillText(line, x, y + lineCount * lineHeight);
        line = words[i];
        lineCount += 1;
      } else {
        line = testLine;
      }
    }
    if (line) {
      ctx.fillText(line, x, y + lineCount * lineHeight);
      lineCount += 1;
    }
    ctx.restore();
    return lineCount;
  }

  function drawGradientBackdrop(ctx, width, height) {
    const gradient = ctx.createLinearGradient(0, 0, 0, height);
    gradient.addColorStop(0, '#1d2940');
    gradient.addColorStop(1, '#0b121d');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, width, height);
  }

  function drawFloatingShapes(ctx, time, width, height) {
    ctx.save();
    ctx.globalAlpha = 0.26;
    for (let i = 0; i < 8; i += 1) {
      const x = (i * 84 + Math.sin(time * 0.4 + i) * 18 + 50) % width;
      const y = (i * 42 + Math.cos(time * 0.5 + i * 0.9) * 12 + 36) % height;
      const size = 16 + (i % 3) * 6;
      ctx.fillStyle = i % 2 === 0 ? '#72b0d8' : '#efb56d';
      ctx.beginPath();
      ctx.moveTo(x, y - size);
      ctx.lineTo(x + size, y);
      ctx.lineTo(x, y + size);
      ctx.lineTo(x - size, y);
      ctx.closePath();
      ctx.fill();
    }
    ctx.restore();
  }

  function drawVignette(ctx, width, height) {
    const radial = ctx.createRadialGradient(width / 2, height / 2, 80, width / 2, height / 2, width / 1.1);
    radial.addColorStop(0, 'rgba(0,0,0,0)');
    radial.addColorStop(1, 'rgba(0,0,0,0.22)');
    ctx.fillStyle = radial;
    ctx.fillRect(0, 0, width, height);
  }

  function drawScanlines(ctx, width, height) {
    ctx.save();
    ctx.globalAlpha = 0.06;
    ctx.fillStyle = '#0f1622';
    for (let y = 0; y < height; y += 4) {
      ctx.fillRect(0, y, width, 1);
    }
    ctx.restore();
  }

  function spriteSourceRect(direction, frame) {
    const rowMap = { down: 0, left: 1, right: 2, up: 3 };
    return { sx: frame * 40, sy: rowMap[direction] * 56, sw: 40, sh: 56 };
  }

  function drawSprite(ctx, sheet, direction, frame, x, y, scale) {
    if (!sheet) return;
    const src = spriteSourceRect(direction, frame);
    const w = 40 * (scale || 1);
    const h = 56 * (scale || 1);
    ctx.drawImage(sheet, src.sx, src.sy, src.sw, src.sh, Math.round(x - w / 2), Math.round(y - h + 2), w, h);
  }

  function drawShadow(ctx, x, y, player) {
    ctx.save();
    ctx.fillStyle = player ? 'rgba(18,16,24,0.34)' : 'rgba(18,16,24,0.24)';
    ctx.beginPath();
    ctx.ellipse(x, y - 2, player ? 12 : 10, player ? 5 : 4, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  function drawOfficeBase(ctx, assets, width, height, dimAlpha) {
    if (assets.officeBackground) {
      ctx.drawImage(assets.officeBackground, 0, 0, width, height);
    } else {
      ctx.fillStyle = '#d7d4cd';
      ctx.fillRect(0, 0, width, height);
    }
    if (dimAlpha) {
      ctx.fillStyle = 'rgba(11,18,29,' + dimAlpha + ')';
      ctx.fillRect(0, 0, width, height);
    }
  }

  function drawTitle(ctx, state, data, assets, width, height) {
    drawGradientBackdrop(ctx, width, height);
    drawOfficeBase(ctx, assets, width, height, 0.56);
    drawFloatingShapes(ctx, state.time, width, height);
    drawVignette(ctx, width, height);

    ctx.fillStyle = '#f1f4f8';
    ctx.font = 'bold 34px monospace';
    ctx.fillText('Pocket Office Quest', 48, 78);
    ctx.fillStyle = '#7bd1f2';
    ctx.font = 'bold 22px monospace';
    ctx.fillText('N64 Brick Edition', 48, 110);
    ctx.fillStyle = '#d0dae6';
    ctx.font = '16px monospace';
    drawWrappedText(
      ctx,
      'Explore an original office room with toy-brick avatars, clearer portrait reads, and Nintendo 64 inspired atmosphere.',
      48,
      146,
      360,
      20,
      '#d0dae6'
    );

    fillPanel(ctx, 42, 220, 360, 88, 16, 'rgba(16,23,35,0.82)', '#7aa7c8');
    ctx.fillStyle = '#f4f7fb';
    ctx.font = 'bold 18px monospace';
    ctx.fillText('Press Enter to open character select', 60, 252);
    ctx.font = '14px monospace';
    ctx.fillStyle = '#c1d0de';
    ctx.fillText('Arrows or A/D choose a personage. Space interacts in the office.', 60, 280);

    const pulse = 1 + Math.sin(state.time * 3.2) * 0.05;
    const heroId = data.avatars[state.selectedIndex].id;
    const portrait = assets.portraits[heroId];
    if (portrait) {
      const size = Math.round(132 * pulse);
      const px = width - 190;
      const py = 74;
      fillPanel(ctx, px - 12, py - 12, size + 24, size + 24, 22, 'rgba(13,19,31,0.62)', '#ffca7a');
      ctx.drawImage(portrait, px, py, size, size);
    }

    const lineupY = 320;
    for (let i = 0; i < data.avatars.length; i += 1) {
      const avatar = data.avatars[i];
      const x = 56 + i * 108;
      const selected = i === state.selectedIndex;
      fillPanel(ctx, x, lineupY - 14, 84, 52, 12, selected ? 'rgba(255,255,255,0.18)' : 'rgba(255,255,255,0.08)', selected ? '#ffca7a' : 'rgba(255,255,255,0.16)');
      const portrait = assets.portraits[avatar.id];
      if (portrait) {
        ctx.drawImage(portrait, x + 10, lineupY - 6, 36, 36);
      }
      ctx.fillStyle = selected ? '#fff6d4' : '#d2d9e4';
      ctx.font = 'bold 12px monospace';
      ctx.fillText(avatar.name.split(' ')[0].toUpperCase(), x + 50, lineupY + 12);
    }

    drawScanlines(ctx, width, height);
  }

  function drawSelect(ctx, state, data, assets, width, height) {
    drawOfficeBase(ctx, assets, width, height, 0.52);
    drawFloatingShapes(ctx, state.time, width, height);
    drawVignette(ctx, width, height);

    ctx.fillStyle = '#f1f4f8';
    ctx.font = 'bold 28px monospace';
    ctx.fillText('Choose your personage', 36, 46);
    ctx.fillStyle = '#c3d1df';
    ctx.font = '14px monospace';
    ctx.fillText('Left and Right switch avatars. Enter starts the office tour.', 36, 70);

    const cardW = 112;
    const gap = 10;
    const total = data.avatars.length * cardW + (data.avatars.length - 1) * gap;
    let startX = Math.round((width - total) / 2);
    const topY = 94;
    const selectedAvatar = data.avatars[state.selectedIndex];

    data.avatars.forEach((avatar, index) => {
      const x = startX + index * (cardW + gap);
      const selected = index === state.selectedIndex;
      const y = selected ? topY - 6 : topY + 4;
      fillPanel(ctx, x, y, cardW, 176, 18, selected ? 'rgba(20,28,42,0.88)' : 'rgba(18,24,34,0.72)', selected ? '#ffca7a' : '#7aa7c8');
      const portrait = assets.portraits[avatar.id];
      if (portrait) {
        ctx.drawImage(portrait, x + 20, y + 14, 72, 72);
      }
      const sheet = assets.sheets[avatar.id];
      if (sheet) {
        const frame = Math.floor(state.time * 6) % 4;
        drawSprite(ctx, sheet, 'down', frame, x + cardW / 2, y + 142, selected ? 1.2 : 1);
      }
      ctx.fillStyle = '#f1f4f8';
      ctx.font = 'bold 14px monospace';
      ctx.fillText(avatar.name.split(' ')[0].toUpperCase(), x + 18, y + 102);
      ctx.fillStyle = '#bad0df';
      ctx.font = '12px monospace';
      drawWrappedText(ctx, avatar.role, x + 18, y + 122, cardW - 28, 14, '#bad0df');
    });

    fillPanel(ctx, 42, 286, width - 84, 84, 18, 'rgba(12,18,28,0.84)', '#7aa7c8');
    const detailPortrait = assets.portraits[selectedAvatar.id];
    if (detailPortrait) {
      ctx.drawImage(detailPortrait, 58, 298, 56, 56);
    }
    ctx.fillStyle = '#f8fbff';
    ctx.font = 'bold 18px monospace';
    ctx.fillText(selectedAvatar.name, 128, 314);
    ctx.fillStyle = '#7bd1f2';
    ctx.font = 'bold 12px monospace';
    ctx.fillText(selectedAvatar.role.toUpperCase(), 128, 332);
    ctx.fillStyle = '#d0dae6';
    ctx.font = '13px monospace';
    drawWrappedText(ctx, selectedAvatar.bio, 128, 350, width - 170, 16, '#d0dae6');
    drawScanlines(ctx, width, height);
  }

  function entityListForScene(state) {
    const entities = [];
    if (state.npcs) {
      state.npcs.forEach((npc) => entities.push({ type: 'npc', data: npc }));
    }
    if (state.player) {
      entities.push({ type: 'player', data: state.player });
    }
    return entities.sort((a, b) => a.data.y - b.data.y);
  }

  function drawInteractionHint(ctx, target) {
    if (!target || !target.point) return;
    ctx.save();
    ctx.strokeStyle = 'rgba(255, 222, 130, 0.9)';
    ctx.lineWidth = 2;
    const pulse = 4 + Math.sin(Date.now() / 120) * 1.5;
    ctx.beginPath();
    ctx.arc(target.point.x, target.point.y - 16, 10 + pulse, 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();
  }

  function drawHud(ctx, state, data, assets, width, height) {
    const avatar = data.avatars[state.selectedIndex];
    fillPanel(ctx, 12, 12, 226, 76, 14, 'rgba(12,18,28,0.88)', '#7aa7c8');
    const portrait = assets.portraits[avatar.id];
    if (portrait) {
      ctx.drawImage(portrait, 18, 18, 58, 58);
    }
    ctx.fillStyle = '#f7fbff';
    ctx.font = 'bold 17px monospace';
    ctx.fillText(avatar.name.toUpperCase(), 88, 35);
    ctx.fillStyle = '#7bd1f2';
    ctx.font = '12px monospace';
    ctx.fillText(avatar.role, 88, 54);
    ctx.fillStyle = '#d0dae6';
    ctx.font = '12px monospace';
    drawWrappedText(ctx, 'Shift sprints. Esc returns to select.', 88, 70, 132, 14, '#d0dae6');

    fillPanel(ctx, width - 172, 12, 160, 60, 14, 'rgba(12,18,28,0.82)', '#7aa7c8');
    ctx.fillStyle = '#f7fbff';
    ctx.font = 'bold 14px monospace';
    ctx.fillText('Zones', width - 154, 34);
    ctx.font = '11px monospace';
    ctx.fillStyle = '#d0dae6';
    ctx.fillText('Reception  Workspace', width - 154, 51);
    ctx.fillText('Meeting   Lounge', width - 154, 64);
  }

  function drawPromptOrDialog(ctx, state, width, height) {
    const boxY = height - 84;
    fillPanel(ctx, 12, boxY, width - 24, 72, 16, 'rgba(12,18,28,0.92)', '#7aa7c8');
    if (state.dialog) {
      ctx.fillStyle = '#fff6d4';
      ctx.font = 'bold 16px monospace';
      ctx.fillText(state.dialog.title, 28, boxY + 24);
      if (state.dialog.subtitle) {
        ctx.fillStyle = '#7bd1f2';
        ctx.font = '12px monospace';
        ctx.fillText(state.dialog.subtitle, 28, boxY + 40);
      }
      ctx.fillStyle = '#e1ebf5';
      ctx.font = '13px monospace';
      drawWrappedText(ctx, state.dialog.text, 210, boxY + 26, width - 232, 16, '#e1ebf5');
      ctx.fillStyle = '#c6d3e2';
      ctx.fillText('Press Space, Enter, or Esc to close.', width - 260, boxY + 58);
    } else {
      ctx.fillStyle = '#fff6d4';
      ctx.font = 'bold 14px monospace';
      ctx.fillText('Status', 28, boxY + 24);
      ctx.fillStyle = '#e1ebf5';
      ctx.font = '13px monospace';
      drawWrappedText(ctx, state.prompt || 'Explore the redesigned office.', 110, boxY + 24, width - 130, 16, '#e1ebf5');
    }
  }

  function drawPlay(ctx, state, data, assets, width, height) {
    drawOfficeBase(ctx, assets, width, height, 0);
    const entities = entityListForScene(state);
    entities.forEach((entry) => {
      const entity = entry.data;
      drawShadow(ctx, entity.x, entity.y, entry.type === 'player');
      drawSprite(ctx, assets.sheets[entity.avatarId], entity.facing, entity.frame || 0, entity.x, entity.y, 1);
    });
    drawInteractionHint(ctx, state.interactionTarget);
    drawHud(ctx, state, data, assets, width, height);
    drawPromptOrDialog(ctx, state, width, height);
    drawVignette(ctx, width, height);
  }

  function renderFrame(ctx, state, data, assets) {
    const width = data.meta.internalResolution.width;
    const height = data.meta.internalResolution.height;
    ctx.clearRect(0, 0, width, height);
    ctx.imageSmoothingEnabled = false;
    if (state.scene === 'title') {
      drawTitle(ctx, state, data, assets, width, height);
    } else if (state.scene === 'select') {
      drawSelect(ctx, state, data, assets, width, height);
    } else {
      drawPlay(ctx, state, data, assets, width, height);
    }
  }

  Render.renderFrame = renderFrame;
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = Render;
  }
  if (typeof global !== 'undefined') {
    global.PocketOfficeRender = Render;
  }
})(typeof window !== 'undefined' ? window : globalThis);
