var Tadpole = function () {
  var tadpole = this;

  this.x = Math.random() * 300 - 150;
  this.y = Math.random() * 300 - 150;
  this.size = 3;

  this.name = '';
  this.age = 0;
  // isGOT true为GOT大会签到人员， False不是
  this.isGOT = false;
  // gender 1为男性 2为女性 0为未知
  this.gender = 0;

  this.hover = false;

  this.momentum = 0;
  this.maxMomentum = 3;
  this.angle = Math.PI * 2;

  this.targetX = 0;
  this.targetY = 0;
  this.targetMomentum = 0;

  this.messages = [];
  this.changed = 0;
  this.timeSinceLastServerUpdate = 0;

  this.update = function (mouse) {
    tadpole.timeSinceLastServerUpdate++;

    tadpole.x += Math.cos(tadpole.angle) * tadpole.momentum;
    tadpole.y += Math.sin(tadpole.angle) * tadpole.momentum;

    if (tadpole.targetX != 0 || tadpole.targetY != 0) {
      tadpole.x += (tadpole.targetX - tadpole.x) / 20;
      tadpole.y += (tadpole.targetY - tadpole.y) / 20;
    }

    if (tadpole.size > 18) {
      tadpole.size = 18;
    }

    // Update messages
    for (var i = tadpole.messages.length - 1; i >= 0; i--) {
      var msg = tadpole.messages[i];
      msg.update();

      if (msg.age == msg.maxAge) {
        tadpole.messages.splice(i, 1);
      }
    }

    // Update tadpole hover/mouse state
    if (Math.sqrt(Math.pow(tadpole.x - mouse.worldx, 2) + Math.pow(tadpole.y - mouse.worldy, 2)) < tadpole.size + 2) {
      tadpole.hover = true;
      mouse.tadpole = tadpole;
    } else {
      if (mouse.tadpole && mouse.tadpole.id == tadpole.id) {
        //mouse.tadpole = null;
      }
      tadpole.hover = false;
    }

    tadpole.tail.update();
  };

  this.userUpdate = function (tadpoles, angleTargetX, angleTargetY) {
    this.age++;

    var prevState = {
      angle: tadpole.angle,
      momentum: tadpole.momentum
    };

    // Angle to targetx and targety (mouse position)
    var anglediff = Math.atan2(angleTargetY - tadpole.y, angleTargetX - tadpole.x) - tadpole.angle;
    while (anglediff < -Math.PI) {
      anglediff += Math.PI * 2;
    }
    while (anglediff > Math.PI) {
      anglediff -= Math.PI * 2;
    }

    tadpole.angle += anglediff / 5;

    // Momentum to targetmomentum
    if (tadpole.targetMomentum != tadpole.momentum) {
      tadpole.momentum += (tadpole.targetMomentum - tadpole.momentum) / 20;
    }

    if (tadpole.momentum < 0) {
      tadpole.momentum = 0;
    }

    tadpole.changed += Math.abs((prevState.angle - tadpole.angle) * 3) + tadpole.momentum;

    if (tadpole.changed > 1) {
      this.timeSinceLastServerUpdate = 0;
    }
  };

  this.draw = function (context) {
    var opacity = Math.max(Math.min(20 / Math.max(tadpole.timeSinceLastServerUpdate - 300, 1), 1), 0.2).toFixed(3);
    context.fillStyle = 'rgba(255,255,255,' + opacity + ')';
    context.shadowColor = 'rgba(255, 255, 255, ' + opacity * 0.7 + ')';
    if (this.gender && this.gender == 2) {
      context.fillStyle = 'rgba(245, 126, 245,' + opacity + ')';
      context.shadowColor = 'rgba(245, 126, 245, ' + opacity * 0.7 + ')';
    }

    context.shadowOffsetX = 0;
    context.shadowOffsetY = 0;
    context.shadowBlur = 6;

    // Draw circle
    context.beginPath();
    context.arc(tadpole.x, tadpole.y, tadpole.size, tadpole.angle + Math.PI * 2.7, tadpole.angle + Math.PI * 1.3, true);

    tadpole.tail.draw(context);

    context.closePath();
    context.fill();

    context.shadowBlur = 0;
    context.shadowColor = '';

    drawName(context);
    drawMessages(context);
    if (this.isGOT) {
      drawImg(context);
    }
  };

  var drawImg = function (context) {
    var img = new Image();
    img.src = gotPNg;
    context.drawImage(img, tadpole.x - 25, tadpole.y + 3, 12, 4);
  };

  var drawName = function (context) {
    var opacity = Math.max(Math.min(20 / Math.max(tadpole.timeSinceLastServerUpdate - 300, 1), 1), 0.2).toFixed(3);
    context.fillStyle = 'rgba(160,160,160,' + opacity + ')';
    context.font = 10 + "px 'Microsoft YaHei'";
    context.textBaseline = 'hanging';
    var width = context.measureText(tadpole.name).width;
    context.fillText(tadpole.name, tadpole.x - width / 2, tadpole.y + 8);
  };

  var drawMessages = function (context) {
    tadpole.messages.reverse();
    var len = tadpole.messages.length;
    //只显示一条记录
    if (len) {
      tadpole.messages[0].draw(context, tadpole.x + 10, tadpole.y + 10, 0);
    }

    tadpole.messages.reverse();
  };

  // Constructor
  (function () {
    tadpole.tail = new TadpoleTail(tadpole);
  })();
};
