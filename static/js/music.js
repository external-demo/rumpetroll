$(function () {
  $('.music').bind('touchstart', function (event) {
    var _this = $(this);
    console.log(2);
    if (_this.hasClass('music-play')) {
      _this
        .removeClass('music-play')
        .find('img')
        .attr('src', static_url + 'static/images/music-pause.png');
      $('#music')[0].pause();
    } else {
      _this
        .addClass('music-play')
        .find('img')
        .attr('src', static_url + 'static/images/music-play.png');
      $('#music')[0].play();
    }

    return false;
  });

  var audioAutoPlay = function (id) {
    var audio = document.getElementById(id),
      play = function () {
        audio.play();
        document.removeEventListener('touchstart', play, false);
      };
    audio.play();
    document.addEventListener(
      'WeixinJSBridgeReady',
      function () {
        //微信
        play();
      },
      false
    );
    document.addEventListener(
      'YixinJSBridgeReady',
      function () {
        //易信
        play();
      },
      false
    );
    document.addEventListener('touchstart', play, false);
  };

  audioAutoPlay('music');
});
