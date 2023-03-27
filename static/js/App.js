var App = function (aSettings, aCanvas) {
  let app = this;

  let model,
    canvas,
    context,
    webSocket,
    webSocketService,
    mouse = { x: 0, y: 0, worldx: 0, worldy: 0, tadpole: null },
    keyNav = { x: 0, y: 0 },
    messageQuota = 5;
  app.update = function () {
    if (messageQuota < 5 && model.userTadpole.age % 50 == 0) {
      messageQuota++;
    }
    let userTadpole = model.userTadpole;
    // Update usertadpole
    if (keyNav.x != 0 || keyNav.y != 0) {
      userTadpole.userUpdate(model.tadpoles, userTadpole.x + keyNav.x, userTadpole.y + keyNav.y);
    } else {
      let mvp = getMouseWorldPosition();
      mouse.worldx = mvp.x;
      mouse.worldy = mvp.y;
      userTadpole.userUpdate(model.tadpoles, mouse.worldx, mouse.worldy);
    }

    if (userTadpole.age % 6 == 0 && userTadpole.changed > 1 && webSocketService.hasConnection) {
      userTadpole.changed = 0;
      webSocketService.sendUpdate(userTadpole);
    }

    model.camera.update(model);

    // Update tadpoles
    let tadpoles = model.tadpoles;
    for (id in tadpoles) {
      tadpoles[id].update(mouse);
    }

    // Update waterParticles
    let waterParticles = model.waterParticles;
    let camera = model.camera;
    for (i in waterParticles) {
      waterParticles[i].update(camera.getOuterBounds(), camera.zoom);
    }

    // Update golds
    let golds = model.golds;
    for (i in golds) {
      golds[i].update(camera.getOuterBounds(), tadpoles);
    }

    // Update arrows
    let arrows = model.arrows;
    for (i in arrows) {
      let cameraBounds = camera.getBounds();
      let arrow = arrows[i];
      arrow.update();
    }
  };

  app.draw = function () {
    model.camera.setupContext();

    // Draw waterParticles
    let waterParticles = model.waterParticles;
    for (i in waterParticles) {
      waterParticles[i].draw(context);
    }

    // Draw gold
    let golds = model.golds;
    for (i in model.golds) {
      golds[i].draw(context);
    }

    // Draw tadpoles
    let tadpoles = model.tadpoles;
    for (id in tadpoles) {
      tadpoles[id].draw(context);
    }

    // Start UI layer (reset transform matrix)
    model.camera.startUILayer();

    // Draw arrows
    let arrows = model.arrows;
    for (i in arrows) {
      arrows[i].draw(context, canvas);
    }
  };

  app.onSocketOpen = function (e) {
    uri = parseUri(document.location);
    if (uri.queryKey.oauth_token) {
      app.authorize(uri.queryKey.oauth_token, uri.queryKey.oauth_verifier);
    }
  };

  app.onSocketClose = function (e) {
    webSocketService.connectionClosed();
    // app.reconnect();
    setTimeout(function () {
      hotcss.initView();
      $('#chat_box').hide();
      $('#timer_wrapper').hide();
      $('#game_over').hide();
      $('#dav_error').show();
    }, 2500);
  };

  app.reconnect = function () {
    // 获取当前endpoint
    $.ajax({
      url: '/rumpetroll/api/get_endpoint/',
      data: { token: token, room: room },
      success: function (data) {
        console.log(data);
        if (data.result) {
          webSocket = new WebSocket(data.data.endpoint);
          webSocket.onopen = app.onSocketOpen;
          webSocket.onclose = app.onSocketClose;
          webSocket.onmessage = app.onSocketMessage;
          window.webSocket = webSocket;
          webSocketService = new WebSocketService(model, webSocket);
          window.webSocketService = webSocketService;
        } else {
          // 获取endpoint失败
          console.log('error');
        }
      },
      error: function () {
        // 获取endpoint失败
        console.log('error');
      },
      dataType: 'json',
      async: false
    });
  };

  app.onSocketMessage = function (e) {
    // Detect if message was in multi form
    if (/^__mul__/.test(e.data)) {
      $.each(e.data.substr(9).split('\n'), function (i, json_str) {
        try {
          let data = JSON.parse(json_str);
          webSocketService.processMessage(data);
        } catch (e) {}
      });
    } else {
      try {
        let data = JSON.parse(e.data);
        webSocketService.processMessage(data);
      } catch (e) {}
    }
  };

  app.sendMessage = function (msg) {
    if (messageQuota > 0) {
      messageQuota--;
      webSocketService.sendMessage(msg);
    }
  };

  app.sendGold = function () {
    let gold = [];

    for (var i = 0; i < 10; i++) {
      let obj = {
        x: Math.random() * 300 - 150,
        y: Math.random() * 300 - 150
      };
      gold[i] = obj;
    }
    webSocketService.sendGold(gold);
  };

  app.sendGoldMessage = function (gold, tadpole) {
    webSocketService.sendGoldMessage(gold, tadpole);
  };

  app.authorize = function (token, verifier) {
    webSocketService.authorize(token, verifier);
  };

  app.mousedown = function (e) {
    mouse.clicking = true;

    if (mouse.tadpole && mouse.tadpole.hover && mouse.tadpole.onclick(e)) {
      return;
    }
    if (model.userTadpole && e.which == 1) {
      model.userTadpole.momentum = model.userTadpole.targetMomentum = model.userTadpole.maxMomentum;
    }
  };

  app.mouseup = function (e) {
    if (model.userTadpole && e.which == 1) {
      model.userTadpole.targetMomentum = 0;
    }
  };

  app.mousemove = function (e) {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
  };

  app.keydown = function (e) {
    if (e.keyCode == keys.up) {
      keyNav.y = -1;
      model.userTadpole.momentum = model.userTadpole.targetMomentum = model.userTadpole.maxMomentum;
      e.preventDefault();
    } else if (e.keyCode == keys.down) {
      keyNav.y = 1;
      model.userTadpole.momentum = model.userTadpole.targetMomentum = model.userTadpole.maxMomentum;
      e.preventDefault();
    } else if (e.keyCode == keys.left) {
      keyNav.x = -1;
      model.userTadpole.momentum = model.userTadpole.targetMomentum = model.userTadpole.maxMomentum;
      e.preventDefault();
    } else if (e.keyCode == keys.right) {
      keyNav.x = 1;
      model.userTadpole.momentum = model.userTadpole.targetMomentum = model.userTadpole.maxMomentum;
      e.preventDefault();
    }
  };
  app.keyup = function (e) {
    if (e.keyCode == keys.up || e.keyCode == keys.down) {
      keyNav.y = 0;
      if (keyNav.x == 0 && keyNav.y == 0) {
        model.userTadpole.targetMomentum = 0;
      }
      e.preventDefault();
    } else if (e.keyCode == keys.left || e.keyCode == keys.right) {
      keyNav.x = 0;
      if (keyNav.x == 0 && keyNav.y == 0) {
        model.userTadpole.targetMomentum = 0;
      }
      e.preventDefault();
    }
  };

  app.touchstart = function (e) {
    e.preventDefault();
    mouse.clicking = true;

    if (model.userTadpole) {
      model.userTadpole.momentum = model.userTadpole.targetMomentum = model.userTadpole.maxMomentum;
    }

    let touch = e.changedTouches.item(0);
    if (touch) {
      mouse.x = touch.clientX;
      mouse.y = touch.clientY;
    }
  };
  app.touchend = function (e) {
    if (model.userTadpole) {
      model.userTadpole.targetMomentum = 0;
    }
  };
  app.touchmove = function (e) {
    e.preventDefault();

    let touch = e.changedTouches.item(0);
    if (touch) {
      mouse.x = touch.clientX;
      mouse.y = touch.clientY;
    }
  };

  app.resize = function (e) {
    resizeCanvas();
  };

  let getMouseWorldPosition = function () {
    return {
      x: (mouse.x + (model.camera.x * model.camera.zoom - canvas.width / 2)) / model.camera.zoom,
      y: (mouse.y + (model.camera.y * model.camera.zoom - canvas.height / 2)) / model.camera.zoom
    };
  };

  let resizeCanvas = function () {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  };

  // Constructor
  (function () {
    canvas = aCanvas;
    context = canvas.getContext('2d');
    resizeCanvas();

    model = new Model();
    model.settings = aSettings;

    model.userTadpole = new Tadpole();
    model.userTadpole.id = -1;
    model.tadpoles[model.userTadpole.id] = model.userTadpole;

    model.waterParticles = [];
    for (var i = 0; i < 150; i++) {
      model.waterParticles.push(new WaterParticle());
    }

    model.camera = new Camera(canvas, context, model.userTadpole.x, model.userTadpole.y);

    model.arrows = {};

    webSocket = new WebSocket(model.settings.socketServer);
    webSocket.onopen = app.onSocketOpen;
    webSocket.onclose = app.onSocketClose;
    webSocket.onmessage = app.onSocketMessage;
    window.webSocket = webSocket;

    webSocketService = new WebSocketService(model, webSocket);
    window.webSocketService = webSocketService;
  })();
};
