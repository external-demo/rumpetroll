/* eslint-disable */
var settings = new Settings();
var debug = false;
var isStatsOn = false;

var authWindow;

var app;
var runLoop = function () {
  app.update();
  app.draw();
};
var initApp = function () {
  if (app != null) {
    return;
  }
  var canvas = document.getElementById('canvas');
  app = new App(settings, document.getElementById('canvas'));

  window.addEventListener('resize', app.resize, false);

  document.addEventListener('mousemove', app.mousemove, false);
  document.addEventListener('mousedown', app.mousedown, false);
  document.addEventListener('mouseup', app.mouseup, false);

  canvas.addEventListener('touchstart', app.touchstart, false);
  document.addEventListener('touchend', app.touchend, false);
  document.addEventListener('touchcancel', app.touchend, false);
  document.addEventListener('touchmove', app.touchmove, false);

  document.addEventListener('keydown', app.keydown, false);
  document.addEventListener('keyup', app.keyup, false);

  document.getElementById('authorize-user-button').addEventListener('click', function (e) {
    app.authorize(null, null);
    authWindow = window.open(
      'auth.html',
      '',
      "width=950,height=460,menubar=no,toolbar=no,location=no,directories=no,status=no,scrollbars=yes,resizable=yes')"
    );
    return false;
  });

  setInterval(runLoop, 40);
};

var forceInit = function () {
  // initApp()
  document.getElementById('unsupported-browser').style.display = 'none';
  return false;
};

if (Modernizr.canvas && Modernizr.websockets) {
  initApp();
} else {
  document.getElementById('unsupported-browser').style.display = 'block';
  document.getElementById('force-init-button').addEventListener('click', forceInit);
}

var addStats = function () {
  if (isStatsOn) {
    return;
  }
  // Draw fps
  var stats = new Stats();
  document.getElementById('fps').appendChild(stats.domElement);

  setInterval(function () {
    stats.update();
  }, 1000 / 60);

  // Array Remove - By John Resig (MIT Licensed)
  Array.remove = function (array, from, to) {
    var rest = array.slice((to || from) + 1 || array.length);
    array.length = from < 0 ? array.length + from : from;
    return array.push.apply(array, rest);
  };
  isStatsOn = true;
};

//document.addEventListener('keydown',function(e) {
//	if(e.which == 27) {
//		addStats();
//	}
//})

if (debug) {
  addStats();
}

$(function () {
  $('a[rel=external]').click(function (e) {
    e.preventDefault();
    window.open($(this).attr('href'));
  });
});

document.body.onselectstart = function () {
  return false;
};
