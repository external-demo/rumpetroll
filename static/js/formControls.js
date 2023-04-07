/* eslint-disable */
// Settings controls

(function ($) {
  $.fn.initChat = function () {
    var input = $(this).find('#chat');
    var submitBtn = $(this).find('#submit');
    var clean_rank = $(this).find('#clean_rank');
    var send_golds = $(this).find('#send_golds');
    var chatText = $('#chatText');
    var chatBox = $('#chat_box');
    var hidden = true;
    var messageHistory = [];
    var messagePointer = -1;
    var winWidth = chatBox.width();
    var admin_control = $(this).find('#is_admin_control');

    function init() {
      $.ajax({
        url: '/rumpetroll/api/get_username/',
        data: { token: token },
        success: function (data) {
          if ('admin' == data.name) {
            admin_control.html(`<button id="clean_rank">清除成绩</button><button id="send_golds">发送金币</button>`);
          }
        },
        dataType: 'json',
        async: false
      });
    }
    init();

    // input.width(winWidth - 65*3 - 10 - 40*2);
    input.width(winWidth / 2);
    if (!is_token) {
      chatBox.css('opacity', '0.3');
    } else {
      chatBox.addClass('pc-chatBox');
      chatBox.css('opacity', '0.3');
    }

    var closechat = function () {
      hidden = true;
      // input.css("opacity","0.5");
      messagePointer = messageHistory.length;
      input.val('');
      chatText.text('');
    };

    var updateDimensions = function () {
      chatText.text(input.val());
      // var width = chatText.width() + 30;
      // input.css({
      // 	width: width,
      // 	marginLeft: (width/2)*-1
      // });
    };

    // input.blur(function(e) {
    // 	setTimeout(function(){
    // 		input.focus();
    // 		console.log('auto focus');
    // 	}, 0.1);
    // });
    input.focus(function () {
      console.log('focus');
    });
    input.bind('touchstart', function () {
      // input.focus();
      chatBox.addClass('focus');
      // messageHistory.push('hello world');
      //  		messagePointer = messageHistory.length;
      // app.sendMessage('hello world');
      // return false;
    });
    input.bind('click', function () {
      // input.focus();
      chatBox.addClass('focus');
      // messageHistory.push('hello world');
      //  		messagePointer = messageHistory.length;
      // app.sendMessage('hello world');
      // return false;
    });
    // input.bind('keydown',function(){
    // 	alert(input.val());
    // })
    input.keydown(function (e) {
      // alert(input.val())
      if (input.val().length > 0) {
        //set timeout because event occurs before text is entered
        setTimeout(updateDimensions, 0.1);
        // input.css({"opacity":"1"});
      } else {
        closechat();
      }

      if (!hidden) {
        e.stopPropagation();
        if (messageHistory.length > 0) {
          if (e.keyCode == keys.up) {
            if (messagePointer > 0) {
              messagePointer--;
              input.val(messageHistory[messagePointer]);
            }
          } else if (e.keyCode == keys.down) {
            if (messagePointer < messageHistory.length - 1) {
              messagePointer++;
              input.val(messageHistory[messagePointer]);
            } else {
              closechat();
              return;
            }
          }
        }
      }
    });
    submitBtn.bind('touchstart', function () {
      if (input.val().length > 0) {
        messageHistory.push(input.val());
        messagePointer = messageHistory.length;
        app.sendMessage(input.val());
        // app.sendGold();
      }
      closechat();
      input.blur();
      chatBox.removeClass('focus');
      return false;
    });
    submitBtn.bind('click', function () {
      if (input.val().length > 0) {
        messageHistory.push(input.val());
        messagePointer = messageHistory.length;
        app.sendMessage(input.val());
        // app.sendGold();
      }
      closechat();
      input.blur();
      chatBox.removeClass('focus');
      return false;
    });

    clean_rank.bind('click', function () {
      $.ajax({
        url: '/rumpetroll/api/clean/?token=' + token,
        async: 'true',
        dataType: 'json',
        success: function (data) {
          console.log('[request]:clean', data);
        },
        error: function () {
          console.log('清除成绩出错');
        }
      });
    });

    send_golds.bind('click', function () {
      $.ajax({
        url: '/rumpetroll/api/gold/?num=500&token=' + token,
        async: 'true',
        dataType: 'json',
        success: function (data) {
          console.log('[request]:send golods', data);
        },
        error: function () {
          console.log('发送金币错误');
        }
      });
    });

    input.keyup(function (e) {
      var k = e.keyCode;
      if (input.val().length >= 45) {
        input.val(input.val().substr(0, 45));
      }

      if (input.val().length > 0) {
        updateDimensions();
        input.css('opacity', '1');
        hidden = false;
      } else {
        closechat();
      }
      if (!hidden) {
        if (k == keys.esc || k == keys.enter || (k == keys.space && input.val().length > 35)) {
          if (k != keys.esc && input.val().length > 0) {
            messageHistory.push(input.val());
            messagePointer = messageHistory.length;
            app.sendMessage(input.val());
            // app.sendGold();
          }
          closechat();
        }

        e.stopPropagation();
      }
    });

    // input.focus();
  };

  $(function () {
    //$('#chat').initChat();
  });
})(jQuery);
