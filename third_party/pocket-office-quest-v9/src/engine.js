(function (global) {
  const Engine = {};

  function getAvatarById(data, avatarId) {
    return data.avatars.find((avatar) => avatar.id === avatarId) || data.avatars[0];
  }

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }

  function lerp(a, b, t) {
    return a + (b - a) * t;
  }

  function rectsIntersect(a, b) {
    return (
      a.x < b.x + b.w &&
      a.x + a.w > b.x &&
      a.y < b.y + b.h &&
      a.y + a.h > b.y
    );
  }

  function objectInsetByType(type) {
    switch (type) {
      case 'chair':
        return { x: 6, y: 10 };
      case 'plant':
        return { x: 7, y: 10 };
      case 'printer':
      case 'water-cooler':
      case 'round-table':
        return { x: 5, y: 8 };
      case 'desk-double':
      case 'desk-single':
      case 'meeting-table':
      case 'reception-desk':
      case 'sofa':
      case 'coffee-bar':
      case 'bookshelf':
      case 'server-rack':
      case 'cabinet':
      case 'archive-shelf':
        return { x: 4, y: 6 };
      default:
        return { x: 4, y: 6 };
    }
  }

  function getObjectRect(object, tileSize) {
    const inset = objectInsetByType(object.type);
    const rawX = object.x * tileSize;
    const rawY = object.y * tileSize;
    const rawW = object.w * tileSize;
    const rawH = object.h * tileSize;
    return {
      id: object.id,
      type: object.type,
      x: rawX + inset.x,
      y: rawY + inset.y,
      w: Math.max(8, rawW - inset.x * 2),
      h: Math.max(8, rawH - inset.y),
    };
  }

  function getSolidRects(data) {
    return data.objects
      .filter((object) => object.solid)
      .map((object) => getObjectRect(object, data.world.tileSize));
  }

  function getCharacterRect(entity) {
    return {
      x: entity.x - 10,
      y: entity.y - 14,
      w: 20,
      h: 14,
    };
  }

  function getBounds(data) {
    const width = data.world.width * data.world.tileSize;
    const height = data.world.height * data.world.tileSize;
    return {
      minX: 30,
      maxX: width - 30,
      minY: 44,
      maxY: height - 34,
    };
  }

  function makePlayer(data, avatarId) {
    const spawn = data.world.spawn;
    return {
      avatarId,
      x: spawn.x * data.world.tileSize,
      y: spawn.y * data.world.tileSize,
      facing: spawn.facing || 'up',
      speed: 98,
      sprintSpeed: 152,
      moving: false,
      animTimer: 0,
      frame: 0,
    };
  }

  function makeNPCs(data, playerAvatarId) {
    return data.avatars
      .filter((avatar) => avatar.id !== playerAvatarId)
      .map((avatar) => {
        const spot = data.npcSpots[avatar.id];
        return {
          avatarId: avatar.id,
          x: spot.x * data.world.tileSize,
          y: spot.y * data.world.tileSize,
          facing: spot.facing || 'down',
          moving: false,
          animTimer: 0,
          frame: 0,
          role: avatar.role,
        };
      });
  }

  function normalizeInputAxes(input) {
    let x = 0;
    let y = 0;
    if (input.left) x -= 1;
    if (input.right) x += 1;
    if (input.up) y -= 1;
    if (input.down) y += 1;
    if (x !== 0 && y !== 0) {
      const inv = 1 / Math.sqrt(2);
      x *= inv;
      y *= inv;
    }
    return { x, y };
  }

  function setFacingFromAxes(entity, axes) {
    if (Math.abs(axes.x) > Math.abs(axes.y)) {
      entity.facing = axes.x >= 0 ? 'right' : 'left';
    } else if (Math.abs(axes.y) > 0) {
      entity.facing = axes.y >= 0 ? 'down' : 'up';
    }
  }

  function moveWithCollisions(entity, dx, dy, solidRects, bounds) {
    const next = { x: entity.x, y: entity.y };
    if (dx !== 0) {
      next.x += dx;
      next.x = clamp(next.x, bounds.minX, bounds.maxX);
      const rectX = getCharacterRect(next);
      let collidedX = false;
      for (const solid of solidRects) {
        if (rectsIntersect(rectX, solid)) {
          collidedX = true;
          break;
        }
      }
      if (!collidedX) {
        entity.x = next.x;
      }
      next.x = entity.x;
    }
    if (dy !== 0) {
      next.y += dy;
      next.y = clamp(next.y, bounds.minY, bounds.maxY);
      const rectY = getCharacterRect(next);
      let collidedY = false;
      for (const solid of solidRects) {
        if (rectsIntersect(rectY, solid)) {
          collidedY = true;
          break;
        }
      }
      if (!collidedY) {
        entity.y = next.y;
      }
    }
  }

  function interactionPointForObject(object, tileSize) {
    const centerX = (object.x + object.w / 2) * tileSize;
    const baseY = (object.y + object.h) * tileSize;
    if (object.type === 'window' || object.type === 'whiteboard' || object.type === 'screen' || object.type === 'pinboard') {
      return { x: centerX, y: baseY + 18 };
    }
    if (object.type === 'door') {
      return { x: centerX, y: object.y * tileSize - 6 };
    }
    return { x: centerX, y: baseY - 6 };
  }

  function facingVector(facing) {
    switch (facing) {
      case 'left':
        return { x: -1, y: 0 };
      case 'right':
        return { x: 1, y: 0 };
      case 'up':
        return { x: 0, y: -1 };
      case 'down':
      default:
        return { x: 0, y: 1 };
    }
  }

  function getInteractionTarget(state, data) {
    if (!state.player) {
      return null;
    }
    const probeVector = facingVector(state.player.facing);
    const probeX = state.player.x + probeVector.x * 28;
    const probeY = state.player.y + probeVector.y * 28;

    let bestTarget = null;
    let bestScore = Infinity;

    for (const object of data.objects) {
      if (!object.interaction) continue;
      const point = interactionPointForObject(object, data.world.tileSize);
      const dx = point.x - probeX;
      const dy = point.y - probeY;
      const dist = Math.hypot(dx, dy);
      const threshold = object.type === 'window' ? 60 : 54;
      if (dist < threshold && dist < bestScore) {
        bestScore = dist;
        bestTarget = {
          kind: 'object',
          id: object.id,
          label: object.label,
          text: object.interaction,
          point,
          distance: dist,
        };
      }
    }

    for (const npc of state.npcs) {
      const avatar = getAvatarById(data, npc.avatarId);
      const point = { x: npc.x, y: npc.y - 20 };
      const dist = Math.hypot(point.x - probeX, point.y - probeY);
      const effectiveDist = dist - 10;
      if (dist < 48 && effectiveDist < bestScore) {
        bestScore = effectiveDist;
        bestTarget = {
          kind: 'npc',
          id: avatar.id,
          label: avatar.name,
          subtitle: avatar.role,
          text: avatar.dialogue,
          point,
          distance: dist,
        };
      }
    }

    return bestTarget;
  }

  function animationFrameForMovement(entity, dt, speedFactor) {
    if (entity.moving) {
      entity.animTimer += dt * (speedFactor || 1);
      if (entity.animTimer >= 0.12) {
        entity.animTimer = 0;
        entity.frame = (entity.frame + 1) % 4;
      }
    } else {
      entity.animTimer = 0;
      entity.frame = 0;
    }
  }

  function createDemoAxes(state, data) {
    const waypoints = data.world.demoPath || [];
    if (!waypoints.length) {
      return { x: 0, y: 0 };
    }
    const currentIndex = state.demoWaypointIndex || 0;
    const current = waypoints[currentIndex];
    const targetX = current.x * data.world.tileSize;
    const targetY = current.y * data.world.tileSize;
    const dx = targetX - state.player.x;
    const dy = targetY - state.player.y;
    const distance = Math.hypot(dx, dy);
    if (distance < 8) {
      state.demoWaypointIndex = (currentIndex + 1) % waypoints.length;
      return { x: 0, y: 0 };
    }
    const inv = distance === 0 ? 0 : 1 / distance;
    return { x: dx * inv, y: dy * inv };
  }

  function startGame(state, data) {
    const avatar = data.avatars[state.selectedIndex] || data.avatars[0];
    state.selectedAvatarId = avatar.id;
    state.player = makePlayer(data, avatar.id);
    state.npcs = makeNPCs(data, avatar.id);
    state.scene = 'play';
    state.dialog = null;
    state.interactionTarget = null;
    state.prompt = 'Walk with arrows or WASD. Space interacts. Shift sprints.';
    state.demoWaypointIndex = 0;
    return state;
  }

  function createState(data, options) {
    const opts = options || {};
    const selectedIndex = typeof opts.selectedIndex === 'number' ? opts.selectedIndex : 0;
    const state = {
      scene: opts.demoMode ? 'play' : 'title',
      selectedIndex,
      selectedAvatarId: data.avatars[selectedIndex].id,
      player: null,
      npcs: [],
      dialog: null,
      interactionTarget: null,
      prompt: '',
      demoMode: !!opts.demoMode,
      demoWaypointIndex: 0,
      time: 0,
      introPulse: 0,
    };
    if (opts.demoMode) {
      startGame(state, data);
    }
    return state;
  }

  function updateTitleScene(state, data, input) {
    if (input.justConfirm || input.justInteract) {
      state.scene = 'select';
    }
  }

  function updateSelectScene(state, data, input) {
    if (input.justLeft) {
      state.selectedIndex = (state.selectedIndex + data.avatars.length - 1) % data.avatars.length;
      state.selectedAvatarId = data.avatars[state.selectedIndex].id;
    }
    if (input.justRight) {
      state.selectedIndex = (state.selectedIndex + 1) % data.avatars.length;
      state.selectedAvatarId = data.avatars[state.selectedIndex].id;
    }
    if (input.justCancel) {
      state.scene = 'title';
    }
    if (input.justConfirm || input.justInteract) {
      startGame(state, data);
    }
  }

  function updatePlayScene(state, data, input, dt) {
    if (!state.player) {
      startGame(state, data);
    }

    if (state.demoMode && input.manualOverride) {
      state.demoMode = false;
      state.prompt = 'Manual control engaged.';
    }

    if (input.justCancel && !state.demoMode) {
      state.scene = 'select';
      state.dialog = null;
      state.prompt = '';
      return;
    }

    if (state.dialog) {
      if (input.justConfirm || input.justInteract || input.justCancel) {
        state.dialog = null;
      }
      state.interactionTarget = getInteractionTarget(state, data);
      return;
    }

    const solidRects = getSolidRects(data);
    const bounds = getBounds(data);
    const axes = state.demoMode ? createDemoAxes(state, data) : normalizeInputAxes(input);
    const hasMovement = Math.abs(axes.x) > 0 || Math.abs(axes.y) > 0;
    const speed = state.demoMode ? 92 : (input.sprint ? state.player.sprintSpeed : state.player.speed);

    if (hasMovement) {
      setFacingFromAxes(state.player, axes);
      const dx = axes.x * speed * dt;
      const dy = axes.y * speed * dt;
      const oldX = state.player.x;
      const oldY = state.player.y;
      moveWithCollisions(state.player, dx, dy, solidRects, bounds);
      state.player.moving = Math.abs(state.player.x - oldX) > 0.01 || Math.abs(state.player.y - oldY) > 0.01;
    } else {
      state.player.moving = false;
    }

    animationFrameForMovement(state.player, dt, speed / state.player.speed);
    for (const npc of state.npcs) {
      npc.moving = false;
      npc.frame = 0;
    }

    state.interactionTarget = getInteractionTarget(state, data);
    state.prompt = state.interactionTarget
      ? 'Interact: ' + state.interactionTarget.label
      : 'Explore the redesigned office.';

    if ((input.justConfirm || input.justInteract) && state.interactionTarget) {
      state.dialog = {
        title: state.interactionTarget.label,
        subtitle: state.interactionTarget.subtitle || '',
        text: state.interactionTarget.text,
      };
    }
  }

  function tick(state, data, input, dt) {
    state.time += dt;
    state.introPulse = lerp(state.introPulse, 1, 0.06);

    if (state.scene === 'title') {
      updateTitleScene(state, data, input);
    } else if (state.scene === 'select') {
      updateSelectScene(state, data, input);
    } else if (state.scene === 'play') {
      updatePlayScene(state, data, input, dt);
    }
    return state;
  }

  Engine.getAvatarById = getAvatarById;
  Engine.getSolidRects = getSolidRects;
  Engine.getCharacterRect = getCharacterRect;
  Engine.getBounds = getBounds;
  Engine.rectsIntersect = rectsIntersect;
  Engine.getInteractionTarget = getInteractionTarget;
  Engine.createState = createState;
  Engine.startGame = startGame;
  Engine.tick = tick;
  Engine.normalizeInputAxes = normalizeInputAxes;
  Engine.facingVector = facingVector;

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = Engine;
  }
  if (typeof global !== 'undefined') {
    global.PocketOfficeEngine = Engine;
  }
})(typeof window !== 'undefined' ? window : globalThis);
