/* eslint-disable */
var WebSocketService = function (model, webSocket) {
  var webSocketService = this;

  var webSocket = webSocket;
  var model = model;

  this.hasConnection = false;
  this.isShowTimer = false;

  this.welcomeHandler = function (data) {
    webSocketService.hasConnection = true;
    model.userTadpole.id = data.id;
    var roomNum = data.room_num;

    $('#room_num')
      .text('ROOM' + roomNum)
      .show();

    //获取当前用户的姓名
    $.ajax({
      url: '/rumpetroll/api/get_username/',
      data: { token: token },
      success: function (data) {
        // console.log(data);
        model.userTadpole.name = data.name;
        model.userTadpole.isGOT = data.is_got;
        model.userTadpole.gender = data.gender;
        model.userTadpole.openid = data.openid;
      },
      error: function () {
        model.userTadpole.name = 'Guest ' + data.id;
      },
      dataType: 'json',
      async: false
    });
    model.tadpoles[data.id] = model.tadpoles[-1];
    // console.log(model.tadpoles)
    delete model.tadpoles[-1];

    $('#chat_box').initChat();
  };

  function sankData() {
    var sank = document.getElementById('sank_data');
    var html = '';
    sank.innerHTML = '';
    $.ajax({
      url: '/rumpetroll/api/rank/',
      data: { token: token },
      success: function (data) {
        for (let i = 0; i < 10; i++) {
          index = i + 1;
          if (index > 3)
            html +=
              '<tr style="height: 60px;"><td>' +
              index +
              '</td><td>' +
              data[i]['name'] +
              '</td><td>' +
              data[i]['golds'] +
              '</td></tr>';
          else
            html +=
              '<tr style="height: 60px;"><td style="background: url(../static/images/num' +
              index +
              '.png) no-repeat center center; background-size:0.9rem auto"></td><td>' +
              data[i]['name'] +
              '</td><td>' +
              data[i]['golds'] +
              '</td></tr>';
        }
      },
      error: function () {},
      dataType: 'json',
      async: false
    });
    sank.innerHTML = html;
    $('#game_over').show();
  }

  function getSpeicalTime(timestamp) {
    var now = new Date(timestamp);
    now.setSeconds(now.getSeconds() + over_time);
    var dateStr =
      now.getFullYear() +
      '/' +
      (now.getMonth() + 1) +
      '/' +
      now.getDate() +
      ' ' +
      now.getHours() +
      ':' +
      now.getMinutes() +
      ':' +
      now.getSeconds();
    return dateStr;
  }

  var timer = 0;

  function countDown(time, day_elem, hour_elem, minute_elem, second_elem) {
    clearInterval(timer);
    var end_time = new Date(time).getTime(); //月份是实际月份-1
    var sys_second = end_time - new Date().getTime();
    var hourElem = $(hour_elem);
    var minuteElem = $(minute_elem);
    var secondElem = $(second_elem);
    var haomiaoElem = $('#haomiao');

    timer = setInterval(function () {
      sys_second = end_time - new Date().getTime();
      if (sys_second > 0) {
        var day = Math.floor(sys_second / 1000 / 3600 / 24);
        var hour = Math.floor((sys_second / 1000 / 3600) % 24);
        var minute = Math.floor((sys_second / 1000 / 60) % 60);
        var second = Math.floor((sys_second / 1000) % 60);
        var haomiao = Math.floor(sys_second % 1000);
        day_elem && $(day_elem).text(day + '天'); //计算天
        hourElem.text(hour < 10 ? '0' + hour : hour + '时'); //计算小时
        minuteElem.text(minute < 10 ? '0' + minute : minute + ''); //计算分
        secondElem.text(second < 10 ? '0' + second : second + ''); // 计算秒
        haomiaoElem.text(haomiao); // 计算秒
      } else {
        minuteElem.text('00'); //计算分
        secondElem.text('00'); // 计算秒
        haomiaoElem.text('00'); // 计算秒
        clearInterval(timer);
        $('#timer_wrapper').hide();
        var sank_timer = setInterval(function () {
          sankData();
          clearInterval(sank_timer)
        },6000);
      }
    }, 42);
  }

  window.countDown = countDown;

  this.updateHandler = function (data) {
    var newtp = false;
    if (!model.tadpoles[data.id]) {
      newtp = true;
      newTadpole = new Tadpole();
      newTadpole.id = data.id;
      model.tadpoles[data.id] = newTadpole;
      model.arrows[data.id] = new Arrow(model.tadpoles[data.id], model.camera);
    }

    var tadpole = model.tadpoles[data.id];

    if (tadpole.id == model.userTadpole.id) {
      tadpole.name = data.name;
      tadpole.gender = data.gender;
      tadpole.isGOT = data.isGOT;
      tadpole.size = data.size;
      tadpole.openid = data.openid;
      return;
    } else {
      tadpole.name = data.name;
      tadpole.gender = data.gender;
      tadpole.isGOT = data.isGOT;
      tadpole.size = data.size;
      tadpole.openid = data.openid;
    }

    if (newtp) {
      tadpole.x = parseFloat(data.x);
      tadpole.y = parseFloat(data.y);
    } else {
      tadpole.targetX = parseFloat(data.x);
      tadpole.targetY = parseFloat(data.y);
    }

    tadpole.angle = parseFloat(data.angle);
    tadpole.momentum = parseFloat(data.momentum);

    tadpole.timeSinceLastServerUpdate = 0;
  };

  this.messageHandler = function (data) {
    var tadpole = model.tadpoles[data.id];
    if (!tadpole) {
      return;
    }
    tadpole.timeSinceLastServerUpdate = 0;
    tadpole.messages.push(new Message(data.message));
  };

  this.goldHandler = function (data) {
    model.golds = [];
    for (var i in data.golds) {
      model.golds.push(new Gold(data.golds[i]));
    }

    if (model.golds.length == 0) {
      return false;
    }
    if (data.is_created) {
      $('#tip_box').show();
      $('#tip_box').bind('touchstart', function () {
        return false;
      });
      setTimeout(function () {
        $('#tip_box').hide();
      }, 2000);
    }
    if ('none' === $('#game_over').css('display')) {
      $('#timer_wrapper').show();
    }
    if (data.timestamp) {
      countDown(
        getSpeicalTime(data.timestamp),
        '#timer_wrapper .day',
        '#timer_wrapper .hour',
        '#timer_wrapper .minute',
        '#timer_wrapper .second'
      );
    }
  };

  this.eatGoldHandler = function (data) {
    var gold = model.golds[data.goldId];
    if (gold) {
      gold.hide = true;
    }
    var tadpole = model.tadpole[data.id];
    if (tadpole) {
      tadpole.size++;
    }
  };

  this.closedHandler = function (data) {
    if (model.tadpoles[data.id]) {
      delete model.tadpoles[data.id];
      delete model.arrows[data.id];
    }
  };

  this.redirectHandler = function (data) {
    if (data.url) {
      if (authWindow) {
        authWindow.document.location = data.url;
      } else {
        document.location = data.url;
      }
    }
  };

  this.processMessage = function (data) {
    var fn = webSocketService[data.type + 'Handler'];
    if (fn) {
      fn(data);
    }
  };

  this.connectionClosed = function () {
    webSocketService.hasConnection = false;
    $('#cant-connect').fadeIn(300);
  };

  this.sendUpdate = function (tadpole) {
    var sendObj = {
      type: 'update',
      x: tadpole.x.toFixed(1),
      y: tadpole.y.toFixed(1),
      angle: tadpole.angle.toFixed(3),
      momentum: tadpole.momentum.toFixed(3),
      size: tadpole.size,
      openid: tadpole.openid
    };

    if (tadpole.name) {
      sendObj['name'] = tadpole.name;
      sendObj['id'] = tadpole.id;
      sendObj['gender'] = tadpole.gender;
      sendObj['isGOT'] = tadpole.isGOT;
    }

    webSocket.send(JSON.stringify(sendObj));
  };

  this.sendGold = function (gold) {
    var sendObj = {
      golds: {
        345418978: { y: -61, x: 1278, goldId: 345418978 },
        807802035: { y: 1905, x: -498, goldId: 807802035 },
        651628678: { y: 1072, x: -415, goldId: 651628678 },
        733221962: { y: 167, x: -586, goldId: 733221962 },
        273225771: { y: 46, x: 1323, goldId: 273225771 },
        763344482: { y: 1040, x: -450, goldId: 763344482 },
        772095891: { y: -1232, x: -1305, goldId: 772095891 },
        975904981: { y: -279, x: -1570, goldId: 975904981 },
        206601049: { y: -1624, x: -459, goldId: 206601049 },
        455766205: { y: -1871, x: -1072, goldId: 455766205 }
      },
      type: 'gold'
    };
    webSocket.send(JSON.stringify(sendObj));
  };

  this.sendGoldMessage = function (gold, tadpole) {
    var sendObj = {
      id: tadpole.id,
      goldId: gold.id,
      type: 'eatGold',
      openid: tadpole.openid,
      name: tadpole.name,
      isGOT: tadpole.isGOT,
      message: '+1'
    };
    webSocket.send(JSON.stringify(sendObj));
  };

  this.sendMessage = function (msg) {
    var regexp = /name: ?(.+)/i;
    if (regexp.test(msg)) {
      model.userTadpole.name = msg.match(regexp)[1];
      return;
    }

    var sendObj = {
      id: model.userTadpole.id,
      type: 'message',
      message: msg
    };

    webSocket.send(JSON.stringify(sendObj));
  };

  this.authorize = function (token, verifier) {
    var sendObj = {
      type: 'authorize',
      token: token,
      verifier: verifier
    };

    webSocket.send(JSON.stringify(sendObj));
  };
};
