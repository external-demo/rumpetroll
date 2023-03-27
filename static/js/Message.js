var Message = function (msg) {
  var message = this;

  this.age = 1;
  this.maxAge = 300;
  var chatText = $('#chatText');

  this.message = msg;

  this.update = function () {
    this.age++;
  };

  this.draw = function (context, x, y, i) {
    var fontsize = 12;
    context.font = 12 + "px 'Microsoft YaHei'";
    // context.textBaseline = 'hanging';

    var paddingH = 3;
    var paddingW = 5;
    console.log(message.message);
    var messageBox = {
      width: context.measureText(message.message).width + paddingW * 2,
      height: fontsize + paddingH * 2 + 2,
      x: x,
      y: y - i * (fontsize + paddingH * 2 + 1) - 20
    };

    var fadeDuration = 20;

    var opacity = (message.maxAge - message.age) / fadeDuration;
    opacity = opacity < 1 ? opacity : 1;

    context.fillStyle = 'rgba(255,255,255,' + opacity / 1.3 + ')';
    drawRoundedRectangle(context, messageBox.x, messageBox.y, messageBox.width, messageBox.height, 10);
    context.fillStyle = 'rgba(0,0,0,1)';
    context.fillText(message.message, messageBox.x + paddingW, messageBox.y + paddingH, 100);
  };

  var drawRoundedRectangle = function (ctx, x, y, w, h, r) {
    var r = r / 2;
    // ctx.beginPath();
    // ctx.moveTo(x,y+r);
    //      ctx.quadraticCurveTo(25,25,25,62.5);
    //      ctx.quadraticCurveTo(25,100,50,100);
    //      ctx.quadraticCurveTo(50,120,30,125);
    //      ctx.quadraticCurveTo(60,120,65,100);
    //      ctx.quadraticCurveTo(125,100,125,62.5);
    //      ctx.quadraticCurveTo(125,25,75,25);
    //      ctx.stroke();
    //      ctx.closePath();
    // ctx.fill();

    ctx.beginPath();
    ctx.moveTo(x - 6, y + r);
    ctx.lineTo(x, y + h - r);
    ctx.quadraticCurveTo(x, y + h, x + r, y + h);
    ctx.lineTo(x + w - r, y + h);
    ctx.quadraticCurveTo(x + w, y + h, x + w, y + h - r);
    ctx.lineTo(x + w, y + r);
    ctx.quadraticCurveTo(x + w, y, x + w - r, y);
    ctx.lineTo(x + r, y);
    ctx.quadraticCurveTo(x, y, x, y + r);
    ctx.closePath();
    ctx.fill();
  };
};
